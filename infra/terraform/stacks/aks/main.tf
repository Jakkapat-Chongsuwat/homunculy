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
# Monitoring Module
# -----------------------------------------------------------------------------

module "monitoring" {
  source = "../../modules/monitoring"

  resource_group_name = azurerm_resource_group.main.name
  location            = var.location
  project_name        = var.project_name
  environment         = var.environment
  tags                = local.common_tags
  retention_in_days   = var.environment == "prod" ? 90 : 30
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
  sku                 = var.environment == "prod" ? "Standard" : "Basic"
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

  # Node Pool Configuration
  system_node_pool_vm_size    = var.system_node_pool_vm_size
  system_node_pool_node_count = var.system_node_pool_node_count
  system_node_pool_min_count  = var.system_node_pool_min_count
  system_node_pool_max_count  = var.system_node_pool_max_count

  # Networking
  network_plugin      = var.network_plugin
  network_policy      = var.network_policy
  dns_service_ip      = var.dns_service_ip
  service_cidr        = var.service_cidr
  load_balancer_sku   = var.load_balancer_sku

  # Integrations
  log_analytics_workspace_id = module.monitoring.log_analytics_workspace_id
  container_registry_id      = module.container_registry.registry_id
  keyvault_id                = module.keyvault.vault_id

  depends_on = [
    module.monitoring,
    module.container_registry,
    module.keyvault
  ]
}
