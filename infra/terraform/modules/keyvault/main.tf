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

  # Default access policy for Terraform
  access_policy {
    tenant_id = var.tenant_id
    object_id = data.azurerm_client_config.current.object_id

    secret_permissions = [
      "Get",
      "List",
      "Set",
      "Delete",
      "Purge",
      "Recover",
    ]

    key_permissions = [
      "Get",
      "List",
      "Create",
      "Delete",
    ]
  }

  tags = merge(var.tags, {
    component = "security"
  })
}

# Dynamic access policies
resource "azurerm_key_vault_access_policy" "policies" {
  for_each = { for idx, policy in var.access_policies : idx => policy }

  key_vault_id = azurerm_key_vault.main.id
  tenant_id    = var.tenant_id
  object_id    = each.value.object_id

  secret_permissions      = each.value.secret_permissions
  key_permissions         = each.value.key_permissions
  certificate_permissions = each.value.certificate_permissions
}

# Secrets
resource "azurerm_key_vault_secret" "secrets" {
  for_each = toset(var.secret_names)

  name         = each.value
  value        = var.secret_values[each.value]
  key_vault_id = azurerm_key_vault.main.id

  tags = merge(var.tags, {
    component = "secret"
  })
}
