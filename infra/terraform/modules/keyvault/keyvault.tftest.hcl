# Mock provider with data source override for valid UUIDs
mock_provider "azurerm" {
  override_data {
    target = data.azurerm_client_config.current
    values = {
      client_id       = "00000000-0000-0000-0000-000000000000"
      tenant_id       = "00000000-0000-0000-0000-000000000000"
      subscription_id = "00000000-0000-0000-0000-000000000000"
      object_id       = "00000000-0000-0000-0000-000000000000"
    }
  }
}

mock_provider "time" {}

variables {
  resource_group_name = "rg-test"
  location            = "eastus"
  project_name        = "homunculy"
  environment         = "dev"
  tenant_id           = "00000000-0000-0000-0000-000000000000"
  secret_names        = []
  secret_values       = {}
  access_policies     = []
  tags = {
    test = "true"
  }
}

# -----------------------------------------------------------------------------
# Test: Key Vault name convention
# -----------------------------------------------------------------------------
run "keyvault_name" {
  command = plan

  module {
    source = "./."
  }

  assert {
    condition     = azurerm_key_vault.main.name == "kv-homunculy-dev"
    error_message = "Key Vault name should follow pattern: kv-{project}-{environment}"
  }
}

# -----------------------------------------------------------------------------
# Test: Key Vault uses standard SKU
# -----------------------------------------------------------------------------
run "keyvault_sku" {
  command = plan

  module {
    source = "./."
  }

  assert {
    condition     = azurerm_key_vault.main.sku_name == "standard"
    error_message = "Key Vault should use standard SKU"
  }
}

# -----------------------------------------------------------------------------
# Test: Dev environment has purge protection disabled
# -----------------------------------------------------------------------------
run "dev_purge_protection" {
  command = plan

  module {
    source = "./."
  }

  assert {
    condition     = azurerm_key_vault.main.purge_protection_enabled == false
    error_message = "Dev environment should not have purge protection"
  }
}

# -----------------------------------------------------------------------------
# Test: Prod environment has purge protection enabled
# -----------------------------------------------------------------------------
run "prod_purge_protection" {
  command = plan

  variables {
    environment = "prod"
  }

  module {
    source = "./."
  }

  assert {
    condition     = azurerm_key_vault.main.purge_protection_enabled == true
    error_message = "Prod environment should have purge protection enabled"
  }
}

# -----------------------------------------------------------------------------
# Test: Soft delete retention is 7 days
# -----------------------------------------------------------------------------
run "soft_delete_retention" {
  command = plan

  module {
    source = "./."
  }

  assert {
    condition     = azurerm_key_vault.main.soft_delete_retention_days == 7
    error_message = "Soft delete retention should be 7 days"
  }
}

# -----------------------------------------------------------------------------
# Test: Key Vault is enabled for deployment
# -----------------------------------------------------------------------------
run "deployment_enabled" {
  command = plan

  module {
    source = "./."
  }

  assert {
    condition     = azurerm_key_vault.main.enabled_for_deployment == true
    error_message = "Key Vault should be enabled for deployment"
  }
}

# -----------------------------------------------------------------------------
# Test: Key Vault has security tag
# -----------------------------------------------------------------------------
run "keyvault_tags" {
  command = plan

  module {
    source = "./."
  }

  assert {
    condition     = azurerm_key_vault.main.tags["component"] == "security"
    error_message = "Key Vault should have component=security tag"
  }
}

# -----------------------------------------------------------------------------
# Test: Key Vault uses RBAC authorization
# -----------------------------------------------------------------------------
run "rbac_authorization_enabled" {
  command = plan

  module {
    source = "./."
  }

  assert {
    condition     = azurerm_key_vault.main.rbac_authorization_enabled == true
    error_message = "Key Vault should use RBAC authorization for managed identity access"
  }
}

# -----------------------------------------------------------------------------
# Test: Terraform service principal gets Secrets Officer role
# -----------------------------------------------------------------------------
run "terraform_role_assignment" {
  command = plan

  module {
    source = "./."
  }

  assert {
    condition     = azurerm_role_assignment.terraform_secrets_officer.role_definition_name == "Key Vault Secrets Officer"
    error_message = "Terraform should be assigned Key Vault Secrets Officer role"
  }
}
