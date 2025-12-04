# =============================================================================
# Velero Backup Module Outputs
# =============================================================================
# Purpose: Export Velero resources information
# Following: Clean Architecture - clear interface contracts
# =============================================================================

output "velero_identity_client_id" {
  description = "Client ID of Velero managed identity"
  value       = azurerm_user_assigned_identity.velero.client_id
}

output "velero_identity_principal_id" {
  description = "Principal ID of Velero managed identity"
  value       = azurerm_user_assigned_identity.velero.principal_id
}

output "storage_account_name" {
  description = "Name of the backup storage account"
  value       = var.create_storage_account ? azurerm_storage_account.velero[0].name : var.storage_account_name
}

output "storage_container_name" {
  description = "Name of the backup storage container"
  value       = var.create_storage_account ? azurerm_storage_container.velero[0].name : var.storage_container_name
}

output "velero_installed" {
  description = "Whether Velero was installed"
  value       = var.install_velero
}

output "velero_namespace" {
  description = "Namespace where Velero is installed"
  value       = var.install_velero ? "velero" : null
}
