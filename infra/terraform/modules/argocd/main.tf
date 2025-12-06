# =============================================================================
# ArgoCD Installation via AKS k8s-extension (Microsoft.ArgoCD)
# =============================================================================
# Uses native AKS extension (no Azure Arc required)
# Supports workload identity for private repo access and SSO
# Reference: https://learn.microsoft.com/en-us/azure/aks/deploy-extensions-az-cli
# =============================================================================

resource "null_resource" "argocd_extension" {

  triggers = {
    argocd_version = var.argocd_version
    cluster_id     = var.aks_cluster_id
  }

  provisioner "local-exec" {
    interpreter = ["bash", "-c"]
    environment = {
      PYTHONUTF8 = "1"
    }
    command = <<-EOT
      set -e

      echo "Installing Microsoft.ArgoCD k8s-extension on AKS (no Arc)..."

      EXTRA_CONFIGS=""
      if [ -n "${var.workload_identity_client_id}" ]; then
        EXTRA_CONFIGS="$EXTRA_CONFIGS --config workloadIdentity.enable=true"
        EXTRA_CONFIGS="$EXTRA_CONFIGS --config workloadIdentity.clientId=${var.workload_identity_client_id}"
      fi
      if [ -n "${var.workload_identity_sso_client_id}" ]; then
        EXTRA_CONFIGS="$EXTRA_CONFIGS --config workloadIdentity.entraSSOClientId=${var.workload_identity_sso_client_id}"
      fi

      PYTHONIOENCODING=utf-8 az k8s-extension create \
        --resource-group "${var.resource_group_name}" \
        --cluster-name "${var.aks_cluster_name}" \
        --cluster-type managedClusters \
        --name argocd \
        --extension-type Microsoft.ArgoCD \
        --release-train stable \
        --config deployWithHighAvailability=false \
        --config namespaceInstall=false \
        --config "config-maps.argocd-cmd-params-cm.data.application\.namespaces=default,argocd" \
        $EXTRA_CONFIGS \
        --no-wait 2>&1 | tr -d '\u2388' || true

      echo "Waiting for extension provisioning..."
      PYTHONIOENCODING=utf-8 az k8s-extension show \
        --resource-group "${var.resource_group_name}" \
        --cluster-name "${var.aks_cluster_name}" \
        --cluster-type managedClusters \
        --name argocd --query provisioningState -o tsv 2>/dev/null || true
    EOT
  }

  depends_on = []
}
