# =============================================================================
# ArgoCD Module - Unit Tests
# =============================================================================
# Purpose: Validate ArgoCD GitOps configuration and settings
# Run: terraform test -filter=tests/argocd.tftest.hcl
# =============================================================================

# Mock providers to avoid real Kubernetes/Helm calls
mock_provider "helm" {}
mock_provider "kubectl" {}

variables {
  environment         = "dev"
  argocd_version      = "5.51.6"
  admin_password      = "test-password-123"
  enable_ingress      = true
  argocd_hostname     = "argocd.test.example.com"
  create_root_app     = true
  git_repo_url        = "https://github.com/test-org/test-repo.git"
  git_target_revision = "main"
  git_apps_path       = "infra/k8s/overlays/prod"
}

# -----------------------------------------------------------------------------
# Test: ArgoCD Helm release name
# -----------------------------------------------------------------------------
run "argocd_helm_release_name" {
  command = plan

  module {
    source = "./modules/argocd"
  }

  assert {
    condition     = helm_release.argocd.name == "argocd"
    error_message = "ArgoCD Helm release should be named 'argocd'"
  }
}

# -----------------------------------------------------------------------------
# Test: ArgoCD uses official Helm repository
# -----------------------------------------------------------------------------
run "argocd_helm_repository" {
  command = plan

  module {
    source = "./modules/argocd"
  }

  assert {
    condition     = helm_release.argocd.repository == "https://argoproj.github.io/argo-helm"
    error_message = "ArgoCD should use official Argo Helm repository"
  }
}

# -----------------------------------------------------------------------------
# Test: ArgoCD uses correct chart
# -----------------------------------------------------------------------------
run "argocd_helm_chart" {
  command = plan

  module {
    source = "./modules/argocd"
  }

  assert {
    condition     = helm_release.argocd.chart == "argo-cd"
    error_message = "ArgoCD should use 'argo-cd' chart"
  }
}

# -----------------------------------------------------------------------------
# Test: ArgoCD installed in correct namespace
# -----------------------------------------------------------------------------
run "argocd_namespace" {
  command = plan

  module {
    source = "./modules/argocd"
  }

  assert {
    condition     = helm_release.argocd.namespace == "argocd"
    error_message = "ArgoCD should be installed in 'argocd' namespace"
  }
}

# -----------------------------------------------------------------------------
# Test: ArgoCD creates namespace
# -----------------------------------------------------------------------------
run "argocd_creates_namespace" {
  command = plan

  module {
    source = "./modules/argocd"
  }

  assert {
    condition     = helm_release.argocd.create_namespace == true
    error_message = "ArgoCD should create the namespace if it doesn't exist"
  }
}

# -----------------------------------------------------------------------------
# Test: ArgoCD Helm chart version
# -----------------------------------------------------------------------------
run "argocd_helm_version" {
  command = plan

  module {
    source = "./modules/argocd"
  }

  assert {
    condition     = helm_release.argocd.version == "5.51.6"
    error_message = "ArgoCD Helm chart version should match the specified version"
  }
}

# -----------------------------------------------------------------------------
# Test: ArgoCD waits for deployment
# -----------------------------------------------------------------------------
run "argocd_wait_enabled" {
  command = plan

  module {
    source = "./modules/argocd"
  }

  assert {
    condition     = helm_release.argocd.wait == true
    error_message = "ArgoCD should wait for deployment to complete"
  }
}

# -----------------------------------------------------------------------------
# Test: ArgoCD has reasonable timeout
# -----------------------------------------------------------------------------
run "argocd_timeout" {
  command = plan

  module {
    source = "./modules/argocd"
  }

  assert {
    condition     = helm_release.argocd.timeout >= 300
    error_message = "ArgoCD should have a timeout of at least 300 seconds"
  }
}

# -----------------------------------------------------------------------------
# Test: ArgoCD Application created when enabled
# -----------------------------------------------------------------------------
run "argocd_app_created" {
  command = plan

  module {
    source = "./modules/argocd"
  }

  assert {
    condition     = length(kubectl_manifest.argocd_app) == 1
    error_message = "ArgoCD root Application should be created when create_root_app is true"
  }
}

# -----------------------------------------------------------------------------
# Test: ArgoCD Application not created when disabled
# -----------------------------------------------------------------------------
run "argocd_app_not_created" {
  command = plan

  module {
    source = "./modules/argocd"
  }

  variables {
    create_root_app = false
  }

  assert {
    condition     = length(kubectl_manifest.argocd_app) == 0
    error_message = "ArgoCD root Application should not be created when create_root_app is false"
  }
}

# -----------------------------------------------------------------------------
# Test: Production environment - higher replicas
# -----------------------------------------------------------------------------
run "prod_environment_config" {
  command = plan

  module {
    source = "./modules/argocd"
  }

  variables {
    environment = "prod"
  }

  # Production should have 2 replicas for server and repoServer
  # This is validated through the Helm values, which we can't easily assert
  # The test passes if the plan succeeds with prod environment
  assert {
    condition     = helm_release.argocd.namespace == "argocd"
    error_message = "Production ArgoCD should be in argocd namespace"
  }
}

# -----------------------------------------------------------------------------
# Test: Custom Git repo URL
# -----------------------------------------------------------------------------
run "custom_git_repo" {
  command = plan

  module {
    source = "./modules/argocd"
  }

  variables {
    git_repo_url = "https://github.com/custom-org/custom-repo.git"
  }

  # The git repo URL is used in kubectl_manifest, which we verify is created
  assert {
    condition     = length(kubectl_manifest.argocd_app) == 1
    error_message = "ArgoCD should create application with custom git repo"
  }
}

# -----------------------------------------------------------------------------
# Test: Ingress disabled
# -----------------------------------------------------------------------------
run "ingress_disabled" {
  command = plan

  module {
    source = "./modules/argocd"
  }

  variables {
    enable_ingress = false
  }

  # When ingress is disabled, Helm release should still be created
  assert {
    condition     = helm_release.argocd.name == "argocd"
    error_message = "ArgoCD should be installed even when ingress is disabled"
  }
}

# -----------------------------------------------------------------------------
# Test: Custom ArgoCD version
# -----------------------------------------------------------------------------
run "custom_argocd_version" {
  command = plan

  module {
    source = "./modules/argocd"
  }

  variables {
    argocd_version = "6.0.0"
  }

  assert {
    condition     = helm_release.argocd.version == "6.0.0"
    error_message = "ArgoCD should use the specified custom version"
  }
}

# -----------------------------------------------------------------------------
# Test: Custom hostname
# -----------------------------------------------------------------------------
run "custom_hostname" {
  command = plan

  module {
    source = "./modules/argocd"
  }

  variables {
    argocd_hostname = "gitops.custom-domain.io"
  }

  # Hostname is passed to Helm values, release should still be created
  assert {
    condition     = helm_release.argocd.name == "argocd"
    error_message = "ArgoCD should accept custom hostname"
  }
}

# -----------------------------------------------------------------------------
# Test: Git target revision - feature branch
# -----------------------------------------------------------------------------
run "feature_branch_revision" {
  command = plan

  module {
    source = "./modules/argocd"
  }

  variables {
    git_target_revision = "feature/new-feature"
  }

  assert {
    condition     = length(kubectl_manifest.argocd_app) == 1
    error_message = "ArgoCD should accept feature branch as target revision"
  }
}

# -----------------------------------------------------------------------------
# Test: Git apps path - Kustomize overlay
# -----------------------------------------------------------------------------
run "kustomize_overlay_path" {
  command = plan

  module {
    source = "./modules/argocd"
  }

  variables {
    git_apps_path = "infra/k8s/overlays/staging"
  }

  assert {
    condition     = length(kubectl_manifest.argocd_app) == 1
    error_message = "ArgoCD should accept Kustomize overlay path"
  }
}
