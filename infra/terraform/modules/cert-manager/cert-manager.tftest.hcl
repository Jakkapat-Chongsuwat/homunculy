# =============================================================================
# Cert-Manager - Unit Tests
# =============================================================================

# -----------------------------------------------------------------------------
# Mock Providers
# -----------------------------------------------------------------------------

mock_provider "helm" {}
mock_provider "kubectl" {}
mock_provider "null" {}

# -----------------------------------------------------------------------------
# Test: Disabled
# -----------------------------------------------------------------------------

run "test_disabled" {
  command = plan

  variables {
    enabled           = false
    letsencrypt_email = "test@example.com"
  }

  assert {
    condition     = length(helm_release.cert_manager) == 0
    error_message = "cert-manager should not be created when disabled"
  }
}

# -----------------------------------------------------------------------------
# Test: Public Cluster with Helm
# -----------------------------------------------------------------------------

run "test_public_cluster_helm" {
  command = plan

  variables {
    enabled            = true
    use_command_invoke = false
    chart_version      = "v1.14.0"
    letsencrypt_email  = "admin@homunculy.io"
  }

  assert {
    condition     = length(helm_release.cert_manager) == 1
    error_message = "Should create helm_release for public cluster"
  }

  assert {
    condition     = helm_release.cert_manager[0].namespace == "cert-manager"
    error_message = "Should install in cert-manager namespace"
  }

  assert {
    condition     = helm_release.cert_manager[0].version == "v1.14.0"
    error_message = "Should use specified chart version"
  }
}

# -----------------------------------------------------------------------------
# Test: ClusterIssuers Created
# -----------------------------------------------------------------------------

run "test_cluster_issuers_created" {
  command = plan

  variables {
    enabled                = true
    use_command_invoke     = false
    create_cluster_issuers = true
    letsencrypt_email      = "admin@homunculy.io"
  }

  assert {
    condition     = length(kubectl_manifest.letsencrypt_staging) == 1
    error_message = "Should create staging ClusterIssuer"
  }

  assert {
    condition     = length(kubectl_manifest.letsencrypt_prod) == 1
    error_message = "Should create production ClusterIssuer"
  }
}

# -----------------------------------------------------------------------------
# Test: ClusterIssuers Disabled
# -----------------------------------------------------------------------------

run "test_cluster_issuers_disabled" {
  command = plan

  variables {
    enabled                = true
    use_command_invoke     = false
    create_cluster_issuers = false
    letsencrypt_email      = "admin@homunculy.io"
  }

  assert {
    condition     = length(kubectl_manifest.letsencrypt_staging) == 0
    error_message = "Should NOT create staging ClusterIssuer when disabled"
  }

  assert {
    condition     = length(kubectl_manifest.letsencrypt_prod) == 0
    error_message = "Should NOT create production ClusterIssuer when disabled"
  }
}

# -----------------------------------------------------------------------------
# Test: Private Cluster
# -----------------------------------------------------------------------------

run "test_private_cluster_command_invoke" {
  command = plan

  variables {
    enabled             = true
    use_command_invoke  = true
    letsencrypt_email   = "admin@homunculy.io"
    resource_group_name = "rg-test"
    aks_cluster_name    = "aks-test"
    aks_cluster_id      = "/subscriptions/xxx/aks"
  }

  assert {
    condition     = length(null_resource.cert_manager) == 1
    error_message = "Should create null_resource for private cluster"
  }

  assert {
    condition     = length(helm_release.cert_manager) == 0
    error_message = "Should NOT create helm_release for private cluster"
  }
}

# -----------------------------------------------------------------------------
# Test: Outputs
# -----------------------------------------------------------------------------

run "test_outputs" {
  command = plan

  variables {
    enabled                = true
    create_cluster_issuers = true
    letsencrypt_email      = "admin@homunculy.io"
  }

  assert {
    condition     = output.namespace == "cert-manager"
    error_message = "Output namespace should be cert-manager"
  }

  assert {
    condition     = output.staging_issuer == "letsencrypt-staging"
    error_message = "Output staging_issuer should be letsencrypt-staging"
  }

  assert {
    condition     = output.production_issuer == "letsencrypt-prod"
    error_message = "Output production_issuer should be letsencrypt-prod"
  }
}
