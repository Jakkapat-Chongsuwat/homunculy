# =============================================================================
# Velero Module - Unit Tests
# =============================================================================
# Purpose: Validate Velero backup configuration
# Run: terraform test (from modules/velero directory)
# =============================================================================

# Mock providers to avoid real Azure/Helm calls
mock_provider "azurerm" {}
mock_provider "helm" {}

variables {
  resource_group_name = "rg-test"
  resource_group_id   = "/subscriptions/00000000-0000-0000-0000-000000000000/resourceGroups/rg-test"
  location            = "eastus"
  project_name        = "homunculy"
  environment         = "dev"
  subscription_id     = "00000000-0000-0000-0000-000000000000"
  oidc_issuer_url     = "https://eastus.oic.prod-aks.azure.com/00000000-0000-0000-0000-000000000000/00000000-0000-0000-0000-000000000000/"

  create_storage_account   = true
  storage_replication_type = "LRS"
  backup_retention_days    = 30
  backup_schedule          = "0 2 * * *"
  install_velero           = true
  velero_version           = "5.2.0"
  velero_azure_plugin_version = "v1.8.2"

  tags = {
    test = "true"
  }
}

# -----------------------------------------------------------------------------
# Test: Storage account name convention
# -----------------------------------------------------------------------------
run "storage_account_name" {
  command = plan

  module {
    source = "./."
  }

  assert {
    condition     = azurerm_storage_account.velero[0].name == "sthomunculyvelerodev"
    error_message = "Storage account name should follow pattern: st{project}velero{environment}"
  }
}

# -----------------------------------------------------------------------------
# Test: Storage account uses Standard tier
# -----------------------------------------------------------------------------
run "storage_account_tier" {
  command = plan

  module {
    source = "./."
  }

  assert {
    condition     = azurerm_storage_account.velero[0].account_tier == "Standard"
    error_message = "Storage account should use Standard tier"
  }
}

# -----------------------------------------------------------------------------
# Test: Storage account uses LRS replication for dev
# -----------------------------------------------------------------------------
run "storage_replication_dev" {
  command = plan

  module {
    source = "./."
  }

  assert {
    condition     = azurerm_storage_account.velero[0].account_replication_type == "LRS"
    error_message = "Dev environment should use LRS replication"
  }
}

# -----------------------------------------------------------------------------
# Test: Storage account uses GRS replication for prod
# -----------------------------------------------------------------------------
run "storage_replication_prod" {
  command = plan

  variables {
    environment              = "prod"
    storage_replication_type = "GRS"
  }

  module {
    source = "./."
  }

  assert {
    condition     = azurerm_storage_account.velero[0].account_replication_type == "GRS"
    error_message = "Prod environment should use GRS replication"
  }
}

# -----------------------------------------------------------------------------
# Test: Storage account enforces TLS 1.2
# -----------------------------------------------------------------------------
run "storage_tls_version" {
  command = plan

  module {
    source = "./."
  }

  assert {
    condition     = azurerm_storage_account.velero[0].min_tls_version == "TLS1_2"
    error_message = "Storage account should enforce TLS 1.2 minimum"
  }
}

# -----------------------------------------------------------------------------
# Test: Blob versioning enabled
# -----------------------------------------------------------------------------
run "blob_versioning_enabled" {
  command = plan

  module {
    source = "./."
  }

  assert {
    condition     = azurerm_storage_account.velero[0].blob_properties[0].versioning_enabled == true
    error_message = "Blob versioning should be enabled for backup protection"
  }
}

# -----------------------------------------------------------------------------
# Test: Storage container name
# -----------------------------------------------------------------------------
run "storage_container_name" {
  command = plan

  module {
    source = "./."
  }

  assert {
    condition     = azurerm_storage_container.velero[0].name == "velero"
    error_message = "Storage container should be named 'velero'"
  }
}

# -----------------------------------------------------------------------------
# Test: Storage container is private
# -----------------------------------------------------------------------------
run "storage_container_private" {
  command = plan

  module {
    source = "./."
  }

  assert {
    condition     = azurerm_storage_container.velero[0].container_access_type == "private"
    error_message = "Storage container should be private"
  }
}

# -----------------------------------------------------------------------------
# Test: Managed identity name convention
# -----------------------------------------------------------------------------
run "managed_identity_name" {
  command = plan

  module {
    source = "./."
  }

  assert {
    condition     = azurerm_user_assigned_identity.velero.name == "id-velero-homunculy-dev"
    error_message = "Managed identity name should follow pattern: id-velero-{project}-{environment}"
  }
}

# -----------------------------------------------------------------------------
# Test: Storage role assignment
# -----------------------------------------------------------------------------
run "storage_role_assignment" {
  command = plan

  module {
    source = "./."
  }

  assert {
    condition     = azurerm_role_assignment.velero_storage[0].role_definition_name == "Storage Blob Data Contributor"
    error_message = "Velero should have Storage Blob Data Contributor role"
  }
}

# -----------------------------------------------------------------------------
# Test: Resource group role assignment
# -----------------------------------------------------------------------------
run "rg_role_assignment" {
  command = plan

  module {
    source = "./."
  }

  assert {
    condition     = azurerm_role_assignment.velero_rg.role_definition_name == "Contributor"
    error_message = "Velero should have Contributor role on resource group for snapshots"
  }
}

# -----------------------------------------------------------------------------
# Test: Federated identity credential name
# -----------------------------------------------------------------------------
run "federated_credential_name" {
  command = plan

  module {
    source = "./."
  }

  assert {
    condition     = azurerm_federated_identity_credential.velero.name == "velero-federated-credential"
    error_message = "Federated credential should be named 'velero-federated-credential'"
  }
}

# -----------------------------------------------------------------------------
# Test: Federated identity subject
# -----------------------------------------------------------------------------
run "federated_credential_subject" {
  command = plan

  module {
    source = "./."
  }

  assert {
    condition     = azurerm_federated_identity_credential.velero.subject == "system:serviceaccount:velero:velero-server"
    error_message = "Federated credential subject should match Velero service account"
  }
}

# -----------------------------------------------------------------------------
# Test: Helm release name
# -----------------------------------------------------------------------------
run "helm_release_name" {
  command = plan

  module {
    source = "./."
  }

  assert {
    condition     = helm_release.velero[0].name == "velero"
    error_message = "Helm release should be named 'velero'"
  }
}

# -----------------------------------------------------------------------------
# Test: Helm release namespace
# -----------------------------------------------------------------------------
run "helm_release_namespace" {
  command = plan

  module {
    source = "./."
  }

  assert {
    condition     = helm_release.velero[0].namespace == "velero"
    error_message = "Velero should be installed in 'velero' namespace"
  }
}

# -----------------------------------------------------------------------------
# Test: Helm creates namespace
# -----------------------------------------------------------------------------
run "helm_creates_namespace" {
  command = plan

  module {
    source = "./."
  }

  assert {
    condition     = helm_release.velero[0].create_namespace == true
    error_message = "Helm should create the velero namespace"
  }
}

# -----------------------------------------------------------------------------
# Test: Velero not installed when disabled
# -----------------------------------------------------------------------------
run "velero_not_installed_when_disabled" {
  command = plan

  variables {
    install_velero = false
  }

  module {
    source = "./."
  }

  assert {
    condition     = length(helm_release.velero) == 0
    error_message = "Velero helm release should not be created when install_velero is false"
  }
}

# -----------------------------------------------------------------------------
# Test: Storage account not created when disabled
# -----------------------------------------------------------------------------
run "storage_not_created_when_disabled" {
  command = plan

  variables {
    create_storage_account = false
    storage_account_name   = "existingstorage"
    storage_container_name = "existingcontainer"
  }

  module {
    source = "./."
  }

  assert {
    condition     = length(azurerm_storage_account.velero) == 0
    error_message = "Storage account should not be created when create_storage_account is false"
  }
}

# -----------------------------------------------------------------------------
# Test: Tags are applied
# -----------------------------------------------------------------------------
run "tags_applied" {
  command = plan

  module {
    source = "./."
  }

  assert {
    condition     = azurerm_storage_account.velero[0].tags["test"] == "true"
    error_message = "Tags should be applied to storage account"
  }

  assert {
    condition     = azurerm_user_assigned_identity.velero.tags["test"] == "true"
    error_message = "Tags should be applied to managed identity"
  }
}
