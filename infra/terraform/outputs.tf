# =============================================================================
# Root Module Outputs
# =============================================================================
# Purpose: Export key resource information for downstream consumers
# Following: Clean Code - meaningful outputs, clear descriptions
# =============================================================================

# -----------------------------------------------------------------------------
# Container Apps Environment
# -----------------------------------------------------------------------------

output "container_apps_environment_id" {
  description = "ID of the Container Apps Environment"
  value       = module.container_apps.environment_id
}

output "container_apps_environment_name" {
  description = "Name of the Container Apps Environment"
  value       = module.container_apps.environment_name
}

# -----------------------------------------------------------------------------
# Application URLs
# -----------------------------------------------------------------------------

output "homunculy_app_url" {
  description = "URL of the homunculy-app container app"
  value       = module.container_apps.homunculy_app_url
}

output "chat_client_url" {
  description = "URL of the chat-client container app"
  value       = module.container_apps.chat_client_url
}

# -----------------------------------------------------------------------------
# Container Registry
# -----------------------------------------------------------------------------

output "container_registry_name" {
  description = "Name of the Azure Container Registry"
  value       = module.container_registry.registry_name
}

output "container_registry_login_server" {
  description = "Login server URL for the container registry"
  value       = module.container_registry.login_server
}

# -----------------------------------------------------------------------------
# Database
# -----------------------------------------------------------------------------

output "database_server_fqdn" {
  description = "FQDN of the PostgreSQL server"
  value       = module.database.server_fqdn
  sensitive   = true
}

output "database_name" {
  description = "Name of the PostgreSQL database"
  value       = module.database.database_name
}

# -----------------------------------------------------------------------------
# Monitoring
# -----------------------------------------------------------------------------

output "log_analytics_workspace_id" {
  description = "ID of the Log Analytics workspace"
  value       = module.monitoring.log_analytics_workspace_id
}

output "application_insights_connection_string" {
  description = "Application Insights connection string"
  value       = module.monitoring.application_insights_connection_string
  sensitive   = true
}

# -----------------------------------------------------------------------------
# Key Vault
# -----------------------------------------------------------------------------

output "key_vault_uri" {
  description = "URI of the Key Vault"
  value       = module.keyvault.vault_uri
}

output "key_vault_name" {
  description = "Name of the Key Vault"
  value       = module.keyvault.vault_name
}
