# =============================================================================
# External-DNS - Unit Tests
# =============================================================================

# -----------------------------------------------------------------------------
# Mock Providers
# -----------------------------------------------------------------------------

mock_provider "helm" {}
mock_provider "null" {}

# -----------------------------------------------------------------------------
# Test: Disabled
# -----------------------------------------------------------------------------

run "test_disabled" {
  command = plan

  variables {
    enabled               = false
    dns_resource_group    = "rg-dns"
    azure_tenant_id       = "tenant-id"
    azure_subscription_id = "sub-id"
  }

  assert {
    condition     = length(helm_release.external_dns) == 0
    error_message = "external-dns should not be created when disabled"
  }
}

# -----------------------------------------------------------------------------
# Test: Public Cluster with Helm
# -----------------------------------------------------------------------------

run "test_public_cluster_helm" {
  command = plan

  variables {
    enabled               = true
    use_command_invoke    = false
    chart_version         = "1.14.0"
    dns_resource_group    = "rg-dns"
    azure_tenant_id       = "tenant-id"
    azure_subscription_id = "sub-id"
    domain_filters        = ["homunculy.io"]
  }

  assert {
    condition     = length(helm_release.external_dns) == 1
    error_message = "Should create helm_release for public cluster"
  }

  assert {
    condition     = helm_release.external_dns[0].namespace == "external-dns"
    error_message = "Should install in external-dns namespace"
  }

  assert {
    condition     = helm_release.external_dns[0].version == "1.14.0"
    error_message = "Should use specified chart version"
  }
}

# -----------------------------------------------------------------------------
# Test: Private Cluster
# -----------------------------------------------------------------------------

run "test_private_cluster_command_invoke" {
  command = plan

  variables {
    enabled               = true
    use_command_invoke    = true
    dns_resource_group    = "rg-dns"
    azure_tenant_id       = "tenant-id"
    azure_subscription_id = "sub-id"
    resource_group_name   = "rg-test"
    aks_cluster_name      = "aks-test"
    aks_cluster_id        = "/subscriptions/xxx/aks"
  }

  assert {
    condition     = length(null_resource.external_dns) == 1
    error_message = "Should create null_resource for private cluster"
  }

  assert {
    condition     = length(helm_release.external_dns) == 0
    error_message = "Should NOT create helm_release for private cluster"
  }
}

# -----------------------------------------------------------------------------
# Test: Outputs
# -----------------------------------------------------------------------------

run "test_outputs" {
  command = plan

  variables {
    enabled               = true
    dns_resource_group    = "rg-dns"
    azure_tenant_id       = "tenant-id"
    azure_subscription_id = "sub-id"
    domain_filters        = ["homunculy.io", "example.com"]
  }

  assert {
    condition     = output.namespace == "external-dns"
    error_message = "Output namespace should be external-dns"
  }

  assert {
    condition     = length(output.managed_domains) == 2
    error_message = "Output managed_domains should have 2 domains"
  }

  assert {
    condition     = output.installation_method == "helm-release"
    error_message = "Installation method should be helm-release for public cluster"
  }
}

# -----------------------------------------------------------------------------
# Test: Custom Sync Policy
# -----------------------------------------------------------------------------

run "test_custom_sync_policy" {
  command = plan

  variables {
    enabled               = true
    dns_resource_group    = "rg-dns"
    azure_tenant_id       = "tenant-id"
    azure_subscription_id = "sub-id"
    sync_policy           = "upsert-only"
  }

  assert {
    condition     = length(helm_release.external_dns) == 1
    error_message = "Should create external-dns with custom sync policy"
  }
}
