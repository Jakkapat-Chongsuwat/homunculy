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
    ilb_manifest_hash   = filemd5("${path.module}/../../../k8s/bootstrap/argocd/argocd-ilb.yaml")
    ingress_hash        = filemd5("${path.module}/../../../k8s/bootstrap/argocd/argocd-ingress.yaml")
    enable_ingress      = tostring(var.enable_ingress)
    public_ip           = var.public_ip
    force_redeploy      = timestamp()
  }

  provisioner "local-exec" {
    interpreter = ["bash", "-c"]
    environment = {
      PYTHONUTF8 = "1"
    }
    command = "${path.module}/install_argocd.sh '${var.resource_group_name}' '${var.aks_cluster_name}' '${local.argocd_manifest_url}' '${var.enable_ingress}' '${var.public_ip}'"
  }

  depends_on = [
    null_resource.wait_for_nodes
  ]
}

# -----------------------------------------------------------------------------
# Root Application (GitOps Bootstrap)
# -----------------------------------------------------------------------------

resource "null_resource" "root_app" {
  count = var.create_root_app ? 1 : 0

  triggers = {
    cluster_id   = var.aks_cluster_id
    git_repo_url = var.git_repo_url
    git_revision = var.git_target_revision
    git_path     = var.git_apps_path
  }

  provisioner "local-exec" {
    interpreter = ["bash", "-c"]
    environment = {
      PYTHONUTF8 = "1"
    }
    command = "${path.module}/create_root_app.sh '${var.resource_group_name}' '${var.aks_cluster_name}' 'homunculy-${var.environment}' '${var.git_repo_url}' '${var.git_target_revision}' '${var.git_apps_path}'"
  }

  depends_on = [
    null_resource.argocd_install
  ]
}
