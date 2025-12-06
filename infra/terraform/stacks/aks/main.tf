# =============================================================================
# AKS Stack - Main Configuration
# =============================================================================
# Purpose: Orchestrate all infrastructure modules for Homunculy on AKS
# Following: Clean Architecture - composition root pattern
# =============================================================================

# -----------------------------------------------------------------------------
# Local Variables
# -----------------------------------------------------------------------------

locals {
  common_tags = merge(var.tags, {
    project     = var.project_name
    environment = var.environment
    managed_by  = "terraform"
    stack       = "aks"
  })

  resource_group_name = "rg-${var.project_name}-aks-${var.environment}"
  is_production       = var.environment == "prod"
}

# -----------------------------------------------------------------------------
# Data Sources
# -----------------------------------------------------------------------------

data "azurerm_client_config" "current" {}

# -----------------------------------------------------------------------------
# Resource Group
# -----------------------------------------------------------------------------

resource "azurerm_resource_group" "main" {
  name     = local.resource_group_name
  location = var.location

  tags = local.common_tags
}

# -----------------------------------------------------------------------------
# Random Password for Database
# -----------------------------------------------------------------------------

resource "random_password" "db_password" {
  length           = 32
  special          = true
  override_special = "!#$%&*()-_=+[]{}<>:?"
}

# -----------------------------------------------------------------------------
# VNet Module (Production: dedicated network)
# -----------------------------------------------------------------------------

module "vnet" {
  count  = var.enable_vnet_integration ? 1 : 0
  source = "../../modules/vnet"

  resource_group_name = azurerm_resource_group.main.name
  location            = var.location
  project_name        = var.project_name
  environment         = var.environment
  tags                = local.common_tags

  address_space                           = var.vnet_address_space
  aks_subnet_address_prefix               = var.aks_subnet_address_prefix
  database_subnet_address_prefix          = var.database_subnet_address_prefix
  private_endpoints_subnet_address_prefix = var.private_endpoints_subnet_address_prefix
  bastion_subnet_address_prefix           = var.bastion_subnet_address_prefix

  create_bastion_subnet    = var.private_cluster_enabled
  create_private_dns_zones = var.private_cluster_enabled
}

# -----------------------------------------------------------------------------
# Monitoring Module
# -----------------------------------------------------------------------------

module "monitoring" {
  source = "../../modules/monitoring"

  resource_group_name = azurerm_resource_group.main.name
  location            = var.location
  project_name        = var.project_name
  environment         = var.environment
  tags                = local.common_tags
  retention_in_days   = local.is_production ? 90 : 30
}

# -----------------------------------------------------------------------------
# Container Registry Module
# -----------------------------------------------------------------------------

module "container_registry" {
  source = "../../modules/container-registry"

  resource_group_name = azurerm_resource_group.main.name
  location            = var.location
  project_name        = var.project_name
  environment         = var.environment
  tags                = local.common_tags
  sku                 = local.is_production ? "Standard" : "Basic"
  admin_enabled       = true
}

# -----------------------------------------------------------------------------
# Database Module
# -----------------------------------------------------------------------------

module "database" {
  source = "../../modules/database"

  resource_group_name   = azurerm_resource_group.main.name
  location              = var.location
  project_name          = var.project_name
  environment           = var.environment
  tags                  = local.common_tags
  sku_name              = var.db_sku_name
  storage_mb            = var.db_storage_mb
  backup_retention_days = var.db_backup_retention_days
  database_name         = "homunculy"
  admin_password        = random_password.db_password.result
}

# -----------------------------------------------------------------------------
# Key Vault Module
# -----------------------------------------------------------------------------

module "keyvault" {
  source = "../../modules/keyvault"

  resource_group_name = azurerm_resource_group.main.name
  location            = var.location
  project_name        = var.project_name
  environment         = var.environment
  tags                = local.common_tags
  tenant_id           = data.azurerm_client_config.current.tenant_id

  secret_names = ["openai-api-key", "elevenlabs-api-key", "db-password"]
  secret_values = {
    "openai-api-key"     = var.openai_api_key
    "elevenlabs-api-key" = var.elevenlabs_api_key
    "db-password"        = random_password.db_password.result
  }

  depends_on = [module.database]
}

# -----------------------------------------------------------------------------
# AKS Module
# -----------------------------------------------------------------------------

module "aks" {
  source = "../../modules/aks"

  resource_group_name = azurerm_resource_group.main.name
  resource_group_id   = azurerm_resource_group.main.id
  location            = var.location
  project_name        = var.project_name
  environment         = var.environment
  tags                = local.common_tags

  # Cluster Configuration
  kubernetes_version      = var.kubernetes_version
  sku_tier                = var.aks_sku_tier
  automatic_upgrade       = var.aks_automatic_upgrade
  node_os_upgrade_channel = var.node_os_upgrade_channel

  # Production Security Features
  private_cluster_enabled    = var.private_cluster_enabled
  azure_policy_enabled       = var.azure_policy_enabled
  microsoft_defender_enabled = var.microsoft_defender_enabled

  # VNet Integration
  aks_subnet_id = var.enable_vnet_integration ? module.vnet[0].aks_subnet_id : null

  # Node Pool Configuration
  system_node_pool_vm_size    = var.system_node_pool_vm_size
  system_node_pool_node_count = var.system_node_pool_node_count
  system_node_pool_min_count  = var.system_node_pool_min_count
  system_node_pool_max_count  = var.system_node_pool_max_count

  # User Node Pool (for production workloads)
  create_user_node_pool     = var.create_user_node_pool
  user_node_pool_vm_size    = var.user_node_pool_vm_size
  user_node_pool_node_count = var.user_node_pool_node_count
  user_node_pool_min_count  = var.user_node_pool_min_count
  user_node_pool_max_count  = var.user_node_pool_max_count

  # Networking
  network_plugin    = var.network_plugin
  network_policy    = var.network_policy
  dns_service_ip    = var.dns_service_ip
  service_cidr      = var.service_cidr
  load_balancer_sku = var.load_balancer_sku

  # Integrations
  log_analytics_workspace_id = module.monitoring.log_analytics_workspace_id
  container_registry_id      = module.container_registry.registry_id
  enable_acr_pull            = var.enable_acr_pull
  keyvault_id                = module.keyvault.vault_id
  enable_keyvault_access     = var.enable_keyvault_access

  # ==========================================================================
  # Azure Application Routing (Managed NGINX Ingress)
  # ==========================================================================
  # Enables Azure-managed NGINX Ingress - NO bastion/helm needed!
  # Single terraform apply provisions everything including ingress
  # ==========================================================================
  enable_app_routing       = var.enable_app_routing
  app_routing_dns_zone_ids = var.app_routing_dns_zone_ids

  depends_on = [
    module.monitoring,
    module.container_registry,
    module.keyvault,
    module.vnet
  ]
}

# -----------------------------------------------------------------------------
# Velero Backup (disaster recovery with node readiness check)
# -----------------------------------------------------------------------------

module "velero" {
  count  = var.install_velero ? 1 : 0
  source = "../../modules/velero"

  resource_group_name = azurerm_resource_group.main.name
  resource_group_id   = azurerm_resource_group.main.id
  location            = var.location
  project_name        = var.project_name
  environment         = var.environment
  tags                = local.common_tags
  subscription_id     = var.subscription_id

  oidc_issuer_url = module.aks.oidc_issuer_url

  create_storage_account   = true
  storage_replication_type = local.is_production ? "GRS" : "LRS"
  backup_schedule          = var.velero_backup_schedule
  backup_retention_days    = var.velero_backup_retention_days

  # AKS cluster configuration
  aks_cluster_name = module.aks.cluster_name
  aks_cluster_id   = module.aks.cluster_id

  depends_on = [module.aks]
}

# -----------------------------------------------------------------------------
# ArgoCD Module (GitOps continuous deployment via AKS extension)
# -----------------------------------------------------------------------------

module "argocd" {
  count  = var.install_argocd ? 1 : 0
  source = "../../modules/argocd"

  environment     = var.environment
  argocd_version  = var.argocd_version
  admin_password  = var.argocd_admin_password
  enable_ingress  = var.argocd_enable_ingress
  argocd_hostname = var.argocd_hostname

  # GitOps Configuration
  create_root_app     = var.argocd_create_root_app
  git_repo_url        = var.argocd_git_repo_url
  git_target_revision = var.argocd_git_target_revision
  git_apps_path       = var.argocd_git_apps_path

  # AKS extension configuration
  resource_group_name = azurerm_resource_group.main.name
  aks_cluster_name    = module.aks.cluster_name
  aks_cluster_id      = module.aks.cluster_id

  depends_on = [module.aks]
}
