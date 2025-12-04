# =============================================================================
# Velero Backup Module - Main Configuration
# =============================================================================
# Purpose: Install Velero for Kubernetes backup and disaster recovery
# Following: Clean Architecture - single responsibility module
# =============================================================================

# -----------------------------------------------------------------------------
# Storage Account for Velero Backups
# -----------------------------------------------------------------------------

resource "azurerm_storage_account" "velero" {
  count = var.create_storage_account ? 1 : 0

  name                     = "st${var.project_name}velero${var.environment}"
  resource_group_name      = var.resource_group_name
  location                 = var.location
  account_tier             = "Standard"
  account_replication_type = var.storage_replication_type
  min_tls_version          = "TLS1_2"

  blob_properties {
    versioning_enabled = true

    delete_retention_policy {
      days = var.backup_retention_days
    }

    container_delete_retention_policy {
      days = var.backup_retention_days
    }
  }

  tags = var.tags
}

resource "azurerm_storage_container" "velero" {
  count = var.create_storage_account ? 1 : 0

  name                  = "velero"
  storage_account_id    = azurerm_storage_account.velero[0].id
  container_access_type = "private"
}

# -----------------------------------------------------------------------------
# Managed Identity for Velero
# -----------------------------------------------------------------------------

resource "azurerm_user_assigned_identity" "velero" {
  name                = "id-velero-${var.project_name}-${var.environment}"
  resource_group_name = var.resource_group_name
  location            = var.location

  tags = var.tags
}

# Storage Blob Data Contributor role for backup storage
resource "azurerm_role_assignment" "velero_storage" {
  count = var.create_storage_account ? 1 : 0

  scope                = azurerm_storage_account.velero[0].id
  role_definition_name = "Storage Blob Data Contributor"
  principal_id         = azurerm_user_assigned_identity.velero.principal_id
}

# Contributor role on resource group for snapshot management
resource "azurerm_role_assignment" "velero_rg" {
  scope                = var.resource_group_id
  role_definition_name = "Contributor"
  principal_id         = azurerm_user_assigned_identity.velero.principal_id
}

# -----------------------------------------------------------------------------
# Federated Identity Credential for Workload Identity
# -----------------------------------------------------------------------------

resource "azurerm_federated_identity_credential" "velero" {
  name                = "velero-federated-credential"
  resource_group_name = var.resource_group_name
  parent_id           = azurerm_user_assigned_identity.velero.id
  audience            = ["api://AzureADTokenExchange"]
  issuer              = var.oidc_issuer_url
  subject             = "system:serviceaccount:velero:velero-server"
}

# -----------------------------------------------------------------------------
# Velero Helm Release
# -----------------------------------------------------------------------------

resource "helm_release" "velero" {
  count = var.install_velero ? 1 : 0

  name             = "velero"
  repository       = "https://vmware-tanzu.github.io/helm-charts"
  chart            = "velero"
  version          = var.velero_version
  namespace        = "velero"
  create_namespace = true

  values = [yamlencode({
    initContainers = [{
      name  = "velero-plugin-for-microsoft-azure"
      image = "velero/velero-plugin-for-microsoft-azure:${var.velero_azure_plugin_version}"
      volumeMounts = [{
        mountPath = "/target"
        name      = "plugins"
      }]
    }]
    configuration = {
      backupStorageLocation = [{
        name     = "azure"
        provider = "azure"
        bucket   = var.create_storage_account ? azurerm_storage_container.velero[0].name : var.storage_container_name
        config = {
          resourceGroup  = var.resource_group_name
          storageAccount = var.create_storage_account ? azurerm_storage_account.velero[0].name : var.storage_account_name
          subscriptionId = var.subscription_id
        }
      }]
      volumeSnapshotLocation = [{
        name     = "azure"
        provider = "azure"
        config = {
          resourceGroup  = var.resource_group_name
          subscriptionId = var.subscription_id
        }
      }]
    }
    serviceAccount = {
      server = {
        annotations = {
          "azure.workload.identity/client-id" = azurerm_user_assigned_identity.velero.client_id
        }
      }
    }
    podLabels = {
      "azure.workload.identity/use" = "true"
    }
    credentials = {
      useSecret = false
    }
    schedules = {
      "daily-backup" = {
        disabled = false
        schedule = var.backup_schedule
        template = {
          ttl                = "${var.backup_retention_days * 24}h"
          includedNamespaces = ["*"]
        }
      }
    }
  })]

  depends_on = [
    azurerm_federated_identity_credential.velero,
    azurerm_role_assignment.velero_storage,
    azurerm_role_assignment.velero_rg
  ]
}
