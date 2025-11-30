# =============================================================================
# Key Vault Module - Main
# =============================================================================
# Purpose: Provision Azure Key Vault for secrets management
# Following: Clean Architecture - Infrastructure layer, Security best practices
# =============================================================================

data "azurerm_client_config" "current" {}

resource "azurerm_key_vault" "main" {
  name                            = "kv-${var.project_name}-${var.environment}"
  location                        = var.location
  resource_group_name             = var.resource_group_name
  tenant_id                       = var.tenant_id
  sku_name                        = "standard"
  enabled_for_deployment          = true
  enabled_for_disk_encryption     = false
  enabled_for_template_deployment = true
  purge_protection_enabled        = var.environment == "prod" ? true : false
  soft_delete_retention_days      = 7

  # Enable RBAC authorization for Key Vault
  # This allows using Azure RBAC roles instead of access policies
  # Required for Container Apps managed identity to access secrets
  rbac_authorization_enabled = true

  tags = merge(var.tags, {
    component = "security"
  })
}

# Grant Key Vault Secrets Officer role to Terraform service principal
# This allows Terraform to manage secrets in the Key Vault
resource "azurerm_role_assignment" "terraform_secrets_officer" {
  scope                = azurerm_key_vault.main.id
  role_definition_name = "Key Vault Secrets Officer"
  principal_id         = data.azurerm_client_config.current.object_id
}

# Secrets
resource "azurerm_key_vault_secret" "secrets" {
  for_each = toset(var.secret_names)

  name         = each.value
  value        = var.secret_values[each.value]
  key_vault_id = azurerm_key_vault.main.id

  # Ensure Terraform has permission before creating secrets
  depends_on = [azurerm_role_assignment.terraform_secrets_officer]

  tags = merge(var.tags, {
    component = "secret"
  })
}
