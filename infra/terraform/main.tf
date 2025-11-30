# =============================================================================
# Root Module - Main Configuration
# =============================================================================
# Purpose: Orchestrate all infrastructure modules for Homunculy
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
  })

  resource_group_name = "rg-${var.project_name}-${var.environment}"
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
  source = "./modules/monitoring"

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
  source = "./modules/container-registry"

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
  source = "./modules/database"

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
  source = "./modules/keyvault"

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
# Container Apps Module
# -----------------------------------------------------------------------------

module "container_apps" {
  source = "./modules/container-apps"

  resource_group_name        = azurerm_resource_group.main.name
  location                   = var.location
  project_name               = var.project_name
  environment                = var.environment
  tags                       = local.common_tags
  log_analytics_workspace_id = module.monitoring.log_analytics_workspace_id

  # Container Registry
  container_registry_login_server   = module.container_registry.login_server
  container_registry_admin_username = module.container_registry.admin_username
  container_registry_admin_password = module.container_registry.admin_password

  # Homunculy App
  homunculy_image_tag    = var.homunculy_image_tag
  homunculy_min_replicas = var.homunculy_min_replicas
  homunculy_max_replicas = var.homunculy_max_replicas

  # Chat Client
  chat_client_image_tag    = var.chat_client_image_tag
  chat_client_min_replicas = var.chat_client_min_replicas
  chat_client_max_replicas = var.chat_client_max_replicas

  # Database
  database_host     = module.database.server_fqdn
  database_name     = module.database.database_name
  database_username = module.database.admin_username
  database_password = random_password.db_password.result

  # Secrets
  openai_api_key     = var.openai_api_key
  elevenlabs_api_key = var.elevenlabs_api_key

  # Monitoring
  application_insights_connection_string = module.monitoring.application_insights_connection_string

  depends_on = [
    module.monitoring,
    module.container_registry,
    module.database,
    module.keyvault
  ]
}
