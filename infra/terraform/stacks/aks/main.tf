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

  github_oidc_subject = "repo:${var.github_repo_owner}/${var.github_repo_name}:ref:refs/heads/${var.github_branch}"
}

# -----------------------------------------------------------------------------
# Data Sources
# -----------------------------------------------------------------------------

data "azurerm_client_config" "current" {}

# -----------------------------------------------------------------------------
# GitHub Actions OIDC App Registration (conditional create or reuse)
# -----------------------------------------------------------------------------

resource "azuread_application" "gha" {
  count                   = var.github_actions_app_id == "" ? 1 : 0
  display_name            = var.github_actions_app_display_name
  sign_in_audience        = "AzureADMyOrg"
  prevent_duplicate_names = true
}

data "azuread_application" "gha" {
  count    = var.github_actions_app_id != "" ? 1 : 0
  client_id = var.github_actions_app_id
}

resource "azuread_service_principal" "gha" {
  count     = var.github_actions_app_id == "" ? 1 : 0
  client_id = azuread_application.gha[0].client_id
}

data "azuread_service_principal" "gha" {
  count     = var.github_actions_app_id != "" ? 1 : 0
  client_id = var.github_actions_app_id
}

locals {
  gha_app_object_id  = var.github_actions_app_id != "" ? data.azuread_application.gha[0].object_id : azuread_application.gha[0].object_id
  gha_sp_object_id   = var.github_actions_app_id != "" ? data.azuread_service_principal.gha[0].object_id : azuread_service_principal.gha[0].object_id
  gha_client_id      = var.github_actions_app_id != "" ? var.github_actions_app_id : azuread_application.gha[0].client_id
}

resource "azuread_application_federated_identity_credential" "gha" {
  count = var.manage_github_federated_identity ? 1 : 0

  application_id = "/applications/${local.gha_app_object_id}"
  display_name   = "github-${var.github_branch}"
  description    = "GitHub Actions OIDC for ${var.github_repo_owner}/${var.github_repo_name}:${var.github_branch}"
  issuer         = "https://token.actions.githubusercontent.com"
  subject        = local.github_oidc_subject
  audiences      = [var.github_oidc_audience]
}

# -----------------------------------------------------------------------------
# Resource Group
# -----------------------------------------------------------------------------
# WHAT: Container for all AKS-related resources
# WHY: Logical grouping for billing, RBAC, and lifecycle management
# SECURITY: All resources inherit common tags for governance

resource "azurerm_resource_group" "main" {
  name     = local.resource_group_name
  location = var.location

  tags = local.common_tags
}

# -----------------------------------------------------------------------------
# App Routing Public IP Data Source (for nip.io DNS)
# -----------------------------------------------------------------------------
# WHAT: Discovers the auto-created public IP for Azure App Routing ingress
# WHY: App Routing creates a random-named IP (kubernetes-<hash>), we need to find it
# USED BY: nip.io DNS (argocd.<IP>.nip.io), NSG rules, outputs
# REF: README.md#ref-public-ip

# Fetch all public IPs in the AKS node resource group
data "azurerm_resources" "app_routing_ips" {
  count               = var.enable_app_routing ? 1 : 0
  resource_group_name = module.aks.node_resource_group
  type                = "Microsoft.Network/publicIPAddresses"

  depends_on = [module.aks]
}

# Get the App Routing public IP (kubernetes-* pattern)
data "azurerm_public_ip" "app_routing" {
  count               = var.enable_app_routing ? 1 : 0
  name                = [for ip in data.azurerm_resources.app_routing_ips[0].resources : ip.name if can(regex("^kubernetes-[a-f0-9]+$", ip.name))][0]
  resource_group_name = module.aks.node_resource_group

  depends_on = [data.azurerm_resources.app_routing_ips]
}

# Get the NSG attached to the AKS node pool
# WHAT: Finds the auto-created Network Security Group for AKS nodes
# WHY: Need to add inbound rules for HTTP/HTTPS traffic to reach ingress
# DEFAULT: AKS only allows Azure LB health probes (port 10256), blocks all other inbound
data "azurerm_resources" "aks_nsg" {
  count               = var.enable_app_routing ? 1 : 0
  resource_group_name = module.aks.node_resource_group
  type                = "Microsoft.Network/networkSecurityGroups"

  depends_on = [module.aks]
}

# Allow HTTP traffic for ingress
# WHAT: NSG rule permitting internet → public IP:80
# WHY: Users need to access apps via HTTP (will redirect to HTTPS)
# SECURITY: Ingress controller handles rate limiting, not wide open
# REF: README.md#ref-nsg-http
resource "azurerm_network_security_rule" "allow_http" {
  count                       = var.enable_app_routing ? 1 : 0
  name                        = "AllowHTTPInbound"
  priority                    = 1000
  direction                   = "Inbound"
  access                      = "Allow"
  protocol                    = "Tcp"
  source_port_range           = "*"
  destination_port_range      = "80"
  source_address_prefix       = "*"
  destination_address_prefix  = "*"
  resource_group_name         = module.aks.node_resource_group
  network_security_group_name = [for nsg in data.azurerm_resources.aks_nsg[0].resources : nsg.name][0]

  depends_on = [data.azurerm_resources.aks_nsg]
}

# Allow HTTPS traffic for ingress
# WHAT: NSG rule permitting internet → public IP:443
# WHY: Users access apps securely via HTTPS (TLS terminated at ingress)
# SECURITY: TLS 1.2+, managed by Azure App Routing, auto-renewed certs
# REF: README.md#ref-nsg-https
resource "azurerm_network_security_rule" "allow_https" {
  count                       = var.enable_app_routing ? 1 : 0
  name                        = "AllowHTTPSInbound"
  priority                    = 1001
  direction                   = "Inbound"
  access                      = "Allow"
  protocol                    = "Tcp"
  source_port_range           = "*"
  destination_port_range      = "443"
  source_address_prefix       = "*"
  destination_address_prefix  = "*"
  resource_group_name         = module.aks.node_resource_group
  network_security_group_name = [for nsg in data.azurerm_resources.aks_nsg[0].resources : nsg.name][0]

  depends_on = [data.azurerm_resources.aks_nsg]
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
# WHAT: Creates private virtual network with subnets for AKS, database, private endpoints
# WHY: Network isolation - pods/nodes can't reach internet directly, only via egress firewall
# SECURITY: Private endpoints for PaaS services (no public IPs)
# REF: README.md#ref-vnet

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

# Grant AKS control-plane identity network access to the AKS subnet (needed for ILB provisioning)
# WHAT: Assigns Network Contributor role to AKS managed identity on AKS subnet
# WHY: AKS needs to create internal load balancers (e.g., argocd-server-ilb)
# WITHOUT THIS: LoadBalancer services stuck in <pending> state forever
# SECURITY: Least privilege - only on AKS subnet, not entire VNet
resource "azurerm_role_assignment" "aks_subnet_network_contributor" {
  count                = var.enable_vnet_integration ? 1 : 0
  scope                = module.vnet[0].aks_subnet_id
  role_definition_name = "Network Contributor"
  principal_id         = module.aks.identity_principal_id

  depends_on = [module.vnet, module.aks]
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
# GitHub Actions OIDC - Role Assignments
# -----------------------------------------------------------------------------

resource "azurerm_role_assignment" "gha_subscription_reader" {
  scope                = "/subscriptions/${var.subscription_id}"
  role_definition_name = "Reader"
  principal_id         = local.gha_sp_object_id
}

resource "azurerm_role_assignment" "gha_acr_push" {
  scope                = module.container_registry.registry_id
  role_definition_name = "AcrPush"
  principal_id         = local.gha_sp_object_id

  depends_on = [module.container_registry]
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
# WHAT: Managed Kubernetes cluster with private API server
# WHY: Container orchestration, auto-scaling, self-healing workloads
# SECURITY: Private cluster (API not exposed), Azure Policy, Defender, RBAC
# COST: Control plane free, pay only for worker nodes (~$30/month for 2x B2s_v2)
# REF: README.md section "Architecture Overview"

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
  private_cluster_enabled    = var.private_cluster_enabled    # API server = private IP only
  azure_policy_enabled       = var.azure_policy_enabled       # Enforce pod security standards
  microsoft_defender_enabled = var.microsoft_defender_enabled # Runtime threat detection

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

  # Managed ingress (Web App Routing)
  # WHAT: Microsoft-managed NGINX ingress controller
  # WHY: Zero config, auto-scaling, auto-updates, free public IP
  # REF: README.md#ref-app-routing
  enable_app_routing       = var.enable_app_routing
  app_routing_dns_zone_ids = var.app_routing_dns_zone_ids

  # Integrations
  log_analytics_workspace_id = module.monitoring.log_analytics_workspace_id
  container_registry_id      = module.container_registry.registry_id
  enable_acr_pull            = var.enable_acr_pull
  keyvault_id                = module.keyvault.vault_id
  enable_keyvault_access     = var.enable_keyvault_access

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
# WHAT: Installs Argo CD (GitOps tool) into argocd namespace
# WHY: Declarative deployments, auto-sync from Git, rollback capability
# HOW: Uses `az aks command invoke` to run kubectl (bypasses private API server)
# PUBLIC ACCESS: Creates ingress with nip.io DNS (argocd.<PUBLIC_IP>.nip.io)
# REF: README.md section "Network Flow"

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

  # Public ingress configuration
  # WHAT: Passes discovered public IP to argocd module
  # WHY: Module generates ingress manifest with argocd.<IP>.nip.io
  # SECURITY: Argo CD runs in insecure mode, TLS terminated at ingress
  public_ip = var.enable_app_routing ? try(data.azurerm_public_ip.app_routing[0].ip_address, "") : ""

  depends_on = [module.aks, data.azurerm_public_ip.app_routing]
}

