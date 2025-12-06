# =============================================================================
# NGINX Ingress Controller - Unit Tests
# =============================================================================

# -----------------------------------------------------------------------------
# Mock Providers
# -----------------------------------------------------------------------------

mock_provider "helm" {}
mock_provider "null" {}

# -----------------------------------------------------------------------------
# Test: Default Configuration (Disabled)
# -----------------------------------------------------------------------------

run "test_disabled_by_default_explicit" {
  command = plan

  variables {
    enabled = false
  }

  assert {
    condition     = length(helm_release.nginx_ingress) == 0
    error_message = "NGINX Ingress should not be created when disabled"
  }
}

# -----------------------------------------------------------------------------
# Test: Enable with Public Cluster
# -----------------------------------------------------------------------------

run "test_public_cluster_helm_release" {
  command = plan

  variables {
    enabled            = true
    use_command_invoke = false
    chart_version      = "4.9.0"
    replica_count      = 2
  }

  assert {
    condition     = length(helm_release.nginx_ingress) == 1
    error_message = "Should create helm_release for public cluster"
  }

  assert {
    condition     = helm_release.nginx_ingress[0].namespace == "ingress-nginx"
    error_message = "Should install in ingress-nginx namespace"
  }

  assert {
    condition     = helm_release.nginx_ingress[0].version == "4.9.0"
    error_message = "Should use specified chart version"
  }
}

# -----------------------------------------------------------------------------
# Test: Enable with Private Cluster
# -----------------------------------------------------------------------------

run "test_private_cluster_command_invoke" {
  command = plan

  variables {
    enabled             = true
    use_command_invoke  = true
    resource_group_name = "rg-test"
    aks_cluster_name    = "aks-test"
    aks_cluster_id      = "/subscriptions/xxx/resourceGroups/rg-test/providers/Microsoft.ContainerService/managedClusters/aks-test"
  }

  assert {
    condition     = length(null_resource.nginx_ingress) == 1
    error_message = "Should create null_resource for private cluster"
  }

  assert {
    condition     = length(helm_release.nginx_ingress) == 0
    error_message = "Should NOT create helm_release for private cluster"
  }
}

# -----------------------------------------------------------------------------
# Test: Internal Only Configuration
# -----------------------------------------------------------------------------

run "test_internal_only_mode" {
  command = plan

  variables {
    enabled       = true
    internal_only = true
  }

  assert {
    condition     = length(helm_release.nginx_ingress) == 1
    error_message = "Should create nginx ingress with internal-only mode"
  }
}

# -----------------------------------------------------------------------------
# Test: Custom Replica Count
# -----------------------------------------------------------------------------

run "test_custom_replica_count" {
  command = plan

  variables {
    enabled       = true
    replica_count = 5
  }

  assert {
    condition     = length(helm_release.nginx_ingress) == 1
    error_message = "Should create nginx ingress with custom replica count"
  }
}

# -----------------------------------------------------------------------------
# Test: Outputs
# -----------------------------------------------------------------------------

run "test_outputs" {
  command = plan

  variables {
    enabled            = true
    use_command_invoke = false
  }

  assert {
    condition     = output.namespace == "ingress-nginx"
    error_message = "Output namespace should be ingress-nginx"
  }

  assert {
    condition     = output.service_name == "ingress-nginx-controller"
    error_message = "Output service_name should be ingress-nginx-controller"
  }

  assert {
    condition     = output.installation_method == "helm-release"
    error_message = "Installation method should be helm-release for public cluster"
  }
}

run "test_outputs_private_cluster" {
  command = plan

  variables {
    enabled             = true
    use_command_invoke  = true
    resource_group_name = "rg-test"
    aks_cluster_name    = "aks-test"
    aks_cluster_id      = "/subscriptions/xxx/xxx"
  }

  assert {
    condition     = output.installation_method == "az-aks-command-invoke"
    error_message = "Installation method should be az-aks-command-invoke for private cluster"
  }
}
