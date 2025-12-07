# =============================================================================
# Argo CD Installation for Private AKS (manifest-based via az aks command invoke)
# =============================================================================
# Rationale: k8s-extension is preview; manifest install is upstream-supported and
# works in private clusters by running kubectl inside the cluster via command invoke.
# =============================================================================

locals {
  argocd_manifest_url = coalesce(var.argocd_manifest_url, "https://raw.githubusercontent.com/argoproj/argo-cd/stable/manifests/install.yaml")
}

resource "null_resource" "wait_for_nodes" {

  triggers = {
    cluster_id = var.aks_cluster_id
  }

  provisioner "local-exec" {
    interpreter = ["bash", "-c"]
    environment = {
      PYTHONUTF8 = "1"
    }
    command = "${path.module}/wait_for_nodes.sh '${var.resource_group_name}' '${var.aks_cluster_name}' 30"
  }
}

resource "null_resource" "argocd_install" {

  triggers = {
    argocd_manifest_url = local.argocd_manifest_url
    cluster_id          = var.aks_cluster_id
    ilb_manifest_hash   = filemd5("${path.module}/argocd-ilb.yaml")
    force_redeploy      = timestamp()
  }

  provisioner "local-exec" {
    interpreter = ["bash", "-c"]
    environment = {
      PYTHONUTF8 = "1"
    }
    command = "${path.module}/install_argocd.sh '${var.resource_group_name}' '${var.aks_cluster_name}' '${local.argocd_manifest_url}'"
  }

  depends_on = [
    null_resource.wait_for_nodes
  ]
}
