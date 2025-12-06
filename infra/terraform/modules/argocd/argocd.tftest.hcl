# =============================================================================
# ArgoCD Module - Unit Tests
# =============================================================================
# Purpose: Validate ArgoCD GitOps configuration and settings
# Supports: public clusters (helm_release) and private clusters (command invoke)
# Run: terraform test
# =============================================================================

# Mock providers to avoid real Kubernetes/Helm calls
mock_provider "helm" {}
mock_provider "kubectl" {}
mock_provider "null" {}

# -----------------------------------------------------------------------------
# Test: Public Cluster - Helm Release Created
# -----------------------------------------------------------------------------
run "test_public_cluster_helm_release" {
  command = plan

  variables {
    environment        = "dev"
    admin_password     = "test-password"
    use_command_invoke = false
    argocd_version     = "5.51.6"
  }

  assert {
    condition     = length(helm_release.argocd) == 1
    error_message = "Should create helm_release for public cluster"
  }

  assert {
    condition     = helm_release.argocd[0].namespace == "argocd"
    error_message = "Should install in argocd namespace"
  }

  assert {
    condition     = helm_release.argocd[0].version == "5.51.6"
    error_message = "Should use specified chart version"
  }

  assert {
    condition     = helm_release.argocd[0].chart == "argo-cd"
    error_message = "Should use argo-cd chart"
  }

  assert {
    condition     = helm_release.argocd[0].repository == "https://argoproj.github.io/argo-helm"
    error_message = "Should use official Argo Helm repository"
  }
}

# -----------------------------------------------------------------------------
# Test: Private Cluster - Command Invoke Created
# -----------------------------------------------------------------------------
run "test_private_cluster_command_invoke" {
  command = plan

  variables {
    environment         = "prod"
    admin_password      = "test-password"
    use_command_invoke  = true
    resource_group_name = "rg-test"
    aks_cluster_name    = "aks-test"
    aks_cluster_id      = "/subscriptions/xxx/aks"
  }

  assert {
    condition     = length(null_resource.argocd_install) == 1
    error_message = "Should create null_resource for private cluster"
  }

  assert {
    condition     = length(helm_release.argocd) == 0
    error_message = "Should NOT create helm_release for private cluster"
  }
}

# -----------------------------------------------------------------------------
# Test: Root App - Public Cluster
# -----------------------------------------------------------------------------
run "test_root_app_public_cluster" {
  command = plan

  variables {
    environment        = "dev"
    admin_password     = "test-password"
    use_command_invoke = false
    create_root_app    = true
    git_repo_url       = "https://github.com/test/repo.git"
  }

  assert {
    condition     = length(kubectl_manifest.argocd_app) == 1
    error_message = "Should create kubectl_manifest for root app on public cluster"
  }

  assert {
    condition     = length(null_resource.argocd_root_app) == 0
    error_message = "Should NOT create null_resource root app for public cluster"
  }
}

# -----------------------------------------------------------------------------
# Test: Root App - Private Cluster
# -----------------------------------------------------------------------------
run "test_root_app_private_cluster" {
  command = plan

  variables {
    environment         = "prod"
    admin_password      = "test-password"
    use_command_invoke  = true
    resource_group_name = "rg-test"
    aks_cluster_name    = "aks-test"
    aks_cluster_id      = "/subscriptions/xxx/aks"
    create_root_app     = true
    git_repo_url        = "https://github.com/test/repo.git"
  }

  assert {
    condition     = length(null_resource.argocd_root_app) == 1
    error_message = "Should create null_resource root app for private cluster"
  }

  assert {
    condition     = length(kubectl_manifest.argocd_app) == 0
    error_message = "Should NOT create kubectl_manifest for private cluster"
  }
}

# -----------------------------------------------------------------------------
# Test: Root App Disabled
# -----------------------------------------------------------------------------
run "test_root_app_disabled" {
  command = plan

  variables {
    environment        = "dev"
    admin_password     = "test-password"
    use_command_invoke = false
    create_root_app    = false
  }

  assert {
    condition     = length(kubectl_manifest.argocd_app) == 0
    error_message = "Should NOT create root app when disabled"
  }
}

# -----------------------------------------------------------------------------
# Test: Outputs - Public Cluster
# -----------------------------------------------------------------------------
run "test_outputs_public" {
  command = plan

  variables {
    environment        = "dev"
    admin_password     = "test-password"
    use_command_invoke = false
    enable_ingress     = true
    argocd_hostname    = "argocd.test.io"
  }

  assert {
    condition     = output.argocd_namespace == "argocd"
    error_message = "Output namespace should be argocd"
  }

  assert {
    condition     = output.argocd_server_service == "argocd-server"
    error_message = "Output service should be argocd-server"
  }

  assert {
    condition     = output.installation_method == "helm-release"
    error_message = "Installation method should be helm-release for public cluster"
  }
}

# -----------------------------------------------------------------------------
# Test: Outputs - Private Cluster
# -----------------------------------------------------------------------------
run "test_outputs_private" {
  command = plan

  variables {
    environment         = "prod"
    admin_password      = "test-password"
    use_command_invoke  = true
    resource_group_name = "rg-test"
    aks_cluster_name    = "aks-test"
    aks_cluster_id      = "/subscriptions/xxx/aks"
  }

  assert {
    condition     = output.installation_method == "az-aks-command-invoke"
    error_message = "Installation method should be az-aks-command-invoke for private cluster"
  }
}

# -----------------------------------------------------------------------------
# Test: Custom ArgoCD Version
# -----------------------------------------------------------------------------
run "test_custom_version" {
  command = plan

  variables {
    environment        = "dev"
    admin_password     = "test-password"
    use_command_invoke = false
    argocd_version     = "6.0.0"
  }

  assert {
    condition     = helm_release.argocd[0].version == "6.0.0"
    error_message = "Should use custom ArgoCD version"
  }
}

# -----------------------------------------------------------------------------
# Test: Custom Git Configuration
# -----------------------------------------------------------------------------
run "test_custom_git_config" {
  command = plan

  variables {
    environment         = "dev"
    admin_password      = "test-password"
    use_command_invoke  = false
    create_root_app     = true
    git_repo_url        = "https://github.com/custom/repo.git"
    git_target_revision = "feature/branch"
    git_apps_path       = "k8s/overlays/staging"
  }

  assert {
    condition     = length(kubectl_manifest.argocd_app) == 1
    error_message = "Should create app with custom git config"
  }
}
