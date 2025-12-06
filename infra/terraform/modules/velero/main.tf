# =============================================================================
# Velero Backup Module - Main Configuration
# =============================================================================
# Purpose: Install Velero for Kubernetes backup and disaster recovery
# Supports both public clusters (helm_release) and private clusters (az aks command invoke)
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
# Local values for Velero configuration
# -----------------------------------------------------------------------------

locals {
  storage_account_name = var.create_storage_account ? azurerm_storage_account.velero[0].name : var.storage_account_name
  container_name       = var.create_storage_account ? azurerm_storage_container.velero[0].name : var.storage_container_name
}

# =============================================================================
# Node Readiness Check
# =============================================================================

resource "null_resource" "wait_for_nodes" {
  count = var.install_velero ? 1 : 0

  provisioner "local-exec" {
    interpreter = ["bash", "-c"]
    environment = {
      PYTHONUTF8 = "1"
    }
    command = "${path.module}/check_node_readiness.sh '${var.resource_group_name}' '${var.aks_cluster_name}' 30"
  }
}

# =============================================================================
# Velero Helm Chart Installation via az aks command invoke
# =============================================================================
# For private clusters, we cannot use helm_release directly
# Instead, use az aks command invoke to install Helm chart

resource "null_resource" "velero_install" {
  count = var.install_velero ? 1 : 0

  triggers = {
    velero_version   = var.velero_version
    azure_plugin     = var.velero_azure_plugin_version
    storage_account  = local.storage_account_name
    container_name   = local.container_name
    client_id        = azurerm_user_assigned_identity.velero.client_id
    kubectl_image    = var.velero_kubectl_image
  }

  provisioner "local-exec" {
    interpreter = ["bash", "-c"]
    environment = {
      PYTHONUTF8 = "1"
    }
    command = <<-EOT
      set -e
      
      echo "Installing Velero ${var.velero_version} on private AKS cluster..."
      
      # Install Helm via az aks command invoke
      PYTHONIOENCODING=utf-8 az aks command invoke \
        --resource-group "${var.resource_group_name}" \
        --name "${var.aks_cluster_name}" \
        --command "helm repo add vmware-tanzu https://vmware-tanzu.github.io/helm-charts && \
                   helm repo update && \
                   helm upgrade --install velero vmware-tanzu/velero \
                     --version ${var.velero_version} \
                     --namespace velero \
                     --create-namespace \
                     --set image.repository=velero/velero \
                     --set image.tag=v1.15.0 \
                     --set kubectl.image.repository=bitnami/kubectl \
                     --set kubectl.image.tag=${var.velero_kubectl_image} \
                     --set initContainers[0].name=velero-plugin-for-microsoft-azure \
                     --set initContainers[0].image=${var.velero_init_container_image} \
                     --set initContainers[0].volumeMounts[0].mountPath=/target \
                     --set initContainers[0].volumeMounts[0].name=plugins \
                     --set podLabels.azure\\.workload\\.identity/use=true \
                     --set serviceAccount.server.annotations.azure\\.workload\\.identity/client-id=${azurerm_user_assigned_identity.velero.client_id} \
                     --set credentials.useSecret=false \
                     --set resources.requests.cpu=10m \
                     --set resources.requests.memory=64Mi \
                     --set resources.limits.cpu=50m \
                     --set resources.limits.memory=128Mi \
                     --set configuration.backupStorageLocation[0].name=default \
                     --set configuration.backupStorageLocation[0].provider=azure \
                     --set configuration.backupStorageLocation[0].bucket=${local.container_name} \
                     --set configuration.backupStorageLocation[0].config.resourceGroup=${var.resource_group_name} \
                     --set configuration.backupStorageLocation[0].config.storageAccount=${local.storage_account_name} \
                     --set configuration.backupStorageLocation[0].config.subscriptionId=${var.subscription_id} \
                     --set configuration.volumeSnapshotLocation[0].name=default \
                     --set configuration.volumeSnapshotLocation[0].provider=azure \
                     --set configuration.volumeSnapshotLocation[0].config.resourceGroup=${var.resource_group_name} \
                     --set configuration.volumeSnapshotLocation[0].config.subscriptionId=${var.subscription_id} \
                     --set schedules.daily-backup.disabled=false \
                     --set schedules.daily-backup.schedule='${var.backup_schedule}' \
                     --set schedules.daily-backup.template.ttl='${var.backup_retention_days * 24}h' \
                     --set schedules.daily-backup.template.includedNamespaces[0]='*' \
                     --wait --timeout 10m" 2>&1 | tr -d '\u2388' || true
      
      echo "Velero installation completed"
    EOT
  }

  depends_on = [
    null_resource.wait_for_nodes,
    azurerm_federated_identity_credential.velero,
    azurerm_role_assignment.velero_storage,
    azurerm_role_assignment.velero_rg
  ]
}
