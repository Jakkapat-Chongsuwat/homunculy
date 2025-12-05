# =============================================================================
# Kubernetes Add-ons Module - Unit Tests
# =============================================================================
# Purpose: Validate Kubernetes add-ons configuration (NGINX, Cert-Manager, External-DNS)
# Run: terraform test (from modules/kubernetes-addons directory)
# =============================================================================

# Mock providers to avoid real Helm/Kubernetes calls
mock_provider "helm" {}
mock_provider "kubectl" {}

# -----------------------------------------------------------------------------
# Common test variables
# -----------------------------------------------------------------------------
variables {
  # NGINX Ingress
  install_nginx_ingress       = true
  nginx_ingress_version       = "4.9.0"
  nginx_ingress_replica_count = 2
  nginx_ingress_internal_only = false

  # Cert-Manager
  install_cert_manager   = true
  cert_manager_version   = "v1.14.0"
  create_cluster_issuers = true
  letsencrypt_email      = "test@example.com"

  # External DNS
  install_external_dns      = true
  external_dns_version      = "1.14.0"
  dns_resource_group        = "rg-dns"
  azure_tenant_id           = "00000000-0000-0000-0000-000000000000"
  azure_subscription_id     = "00000000-0000-0000-0000-000000000000"
  domain_filter             = "example.com"
  external_dns_txt_owner_id = "homunculy"
}

# =============================================================================
# NGINX Ingress Controller Tests
# =============================================================================

# -----------------------------------------------------------------------------
# Test: NGINX Ingress release name
# -----------------------------------------------------------------------------
run "nginx_ingress_name" {
  command = plan

  module {
    source = "./."
  }

  assert {
    condition     = helm_release.nginx_ingress[0].name == "ingress-nginx"
    error_message = "NGINX Ingress should be named 'ingress-nginx'"
  }
}

# -----------------------------------------------------------------------------
# Test: NGINX Ingress chart repository
# -----------------------------------------------------------------------------
run "nginx_ingress_repository" {
  command = plan

  module {
    source = "./."
  }

  assert {
    condition     = helm_release.nginx_ingress[0].repository == "https://kubernetes.github.io/ingress-nginx"
    error_message = "NGINX Ingress should use official Kubernetes repository"
  }
}

# -----------------------------------------------------------------------------
# Test: NGINX Ingress namespace
# -----------------------------------------------------------------------------
run "nginx_ingress_namespace" {
  command = plan

  module {
    source = "./."
  }

  assert {
    condition     = helm_release.nginx_ingress[0].namespace == "ingress-nginx"
    error_message = "NGINX Ingress should be in 'ingress-nginx' namespace"
  }
}

# -----------------------------------------------------------------------------
# Test: NGINX Ingress creates namespace
# -----------------------------------------------------------------------------
run "nginx_ingress_creates_namespace" {
  command = plan

  module {
    source = "./."
  }

  assert {
    condition     = helm_release.nginx_ingress[0].create_namespace == true
    error_message = "NGINX Ingress should create its namespace"
  }
}

# -----------------------------------------------------------------------------
# Test: NGINX Ingress not installed when disabled
# -----------------------------------------------------------------------------
run "nginx_ingress_disabled" {
  command = plan

  variables {
    install_nginx_ingress = false
  }

  module {
    source = "./."
  }

  assert {
    condition     = length(helm_release.nginx_ingress) == 0
    error_message = "NGINX Ingress should not be installed when disabled"
  }
}

# =============================================================================
# Cert-Manager Tests
# =============================================================================

# -----------------------------------------------------------------------------
# Test: Cert-Manager release name
# -----------------------------------------------------------------------------
run "cert_manager_name" {
  command = plan

  module {
    source = "./."
  }

  assert {
    condition     = helm_release.cert_manager[0].name == "cert-manager"
    error_message = "Cert-Manager should be named 'cert-manager'"
  }
}

# -----------------------------------------------------------------------------
# Test: Cert-Manager chart repository
# -----------------------------------------------------------------------------
run "cert_manager_repository" {
  command = plan

  module {
    source = "./."
  }

  assert {
    condition     = helm_release.cert_manager[0].repository == "https://charts.jetstack.io"
    error_message = "Cert-Manager should use Jetstack repository"
  }
}

# -----------------------------------------------------------------------------
# Test: Cert-Manager namespace
# -----------------------------------------------------------------------------
run "cert_manager_namespace" {
  command = plan

  module {
    source = "./."
  }

  assert {
    condition     = helm_release.cert_manager[0].namespace == "cert-manager"
    error_message = "Cert-Manager should be in 'cert-manager' namespace"
  }
}

# -----------------------------------------------------------------------------
# Test: Cert-Manager creates namespace
# -----------------------------------------------------------------------------
run "cert_manager_creates_namespace" {
  command = plan

  module {
    source = "./."
  }

  assert {
    condition     = helm_release.cert_manager[0].create_namespace == true
    error_message = "Cert-Manager should create its namespace"
  }
}

# -----------------------------------------------------------------------------
# Test: Cert-Manager not installed when disabled
# -----------------------------------------------------------------------------
run "cert_manager_disabled" {
  command = plan

  variables {
    install_cert_manager = false
  }

  module {
    source = "./."
  }

  assert {
    condition     = length(helm_release.cert_manager) == 0
    error_message = "Cert-Manager should not be installed when disabled"
  }
}

# -----------------------------------------------------------------------------
# Test: ClusterIssuers created when enabled
# -----------------------------------------------------------------------------
run "cluster_issuers_created" {
  command = plan

  module {
    source = "./."
  }

  assert {
    condition     = length(kubectl_manifest.letsencrypt_staging) == 1
    error_message = "Let's Encrypt staging issuer should be created"
  }

  assert {
    condition     = length(kubectl_manifest.letsencrypt_prod) == 1
    error_message = "Let's Encrypt production issuer should be created"
  }
}

# -----------------------------------------------------------------------------
# Test: ClusterIssuers not created when disabled
# -----------------------------------------------------------------------------
run "cluster_issuers_disabled" {
  command = plan

  variables {
    create_cluster_issuers = false
  }

  module {
    source = "./."
  }

  assert {
    condition     = length(kubectl_manifest.letsencrypt_staging) == 0
    error_message = "Let's Encrypt staging issuer should not be created when disabled"
  }

  assert {
    condition     = length(kubectl_manifest.letsencrypt_prod) == 0
    error_message = "Let's Encrypt production issuer should not be created when disabled"
  }
}

# =============================================================================
# External DNS Tests
# =============================================================================

# -----------------------------------------------------------------------------
# Test: External DNS release name
# -----------------------------------------------------------------------------
run "external_dns_name" {
  command = plan

  module {
    source = "./."
  }

  assert {
    condition     = helm_release.external_dns[0].name == "external-dns"
    error_message = "External DNS should be named 'external-dns'"
  }
}

# -----------------------------------------------------------------------------
# Test: External DNS chart repository
# -----------------------------------------------------------------------------
run "external_dns_repository" {
  command = plan

  module {
    source = "./."
  }

  assert {
    condition     = helm_release.external_dns[0].repository == "https://kubernetes-sigs.github.io/external-dns"
    error_message = "External DNS should use kubernetes-sigs repository"
  }
}

# -----------------------------------------------------------------------------
# Test: External DNS namespace
# -----------------------------------------------------------------------------
run "external_dns_namespace" {
  command = plan

  module {
    source = "./."
  }

  assert {
    condition     = helm_release.external_dns[0].namespace == "external-dns"
    error_message = "External DNS should be in 'external-dns' namespace"
  }
}

# -----------------------------------------------------------------------------
# Test: External DNS creates namespace
# -----------------------------------------------------------------------------
run "external_dns_creates_namespace" {
  command = plan

  module {
    source = "./."
  }

  assert {
    condition     = helm_release.external_dns[0].create_namespace == true
    error_message = "External DNS should create its namespace"
  }
}

# -----------------------------------------------------------------------------
# Test: External DNS not installed when disabled
# -----------------------------------------------------------------------------
run "external_dns_disabled" {
  command = plan

  variables {
    install_external_dns = false
  }

  module {
    source = "./."
  }

  assert {
    condition     = length(helm_release.external_dns) == 0
    error_message = "External DNS should not be installed when disabled"
  }
}

# =============================================================================
# Version Pinning Tests
# =============================================================================

# -----------------------------------------------------------------------------
# Test: NGINX Ingress version is pinned
# -----------------------------------------------------------------------------
run "nginx_version_pinned" {
  command = plan

  module {
    source = "./."
  }

  assert {
    condition     = helm_release.nginx_ingress[0].version == "4.9.0"
    error_message = "NGINX Ingress version should be pinned to 4.9.0"
  }
}

# -----------------------------------------------------------------------------
# Test: Cert-Manager version is pinned
# -----------------------------------------------------------------------------
run "cert_manager_version_pinned" {
  command = plan

  module {
    source = "./."
  }

  assert {
    condition     = helm_release.cert_manager[0].version == "v1.14.0"
    error_message = "Cert-Manager version should be pinned to v1.14.0"
  }
}

# -----------------------------------------------------------------------------
# Test: External DNS version is pinned
# -----------------------------------------------------------------------------
run "external_dns_version_pinned" {
  command = plan

  module {
    source = "./."
  }

  assert {
    condition     = helm_release.external_dns[0].version == "1.14.0"
    error_message = "External DNS version should be pinned to 1.14.0"
  }
}

# =============================================================================
# All Components Disabled Test
# =============================================================================

# -----------------------------------------------------------------------------
# Test: No resources when all disabled
# -----------------------------------------------------------------------------
run "all_disabled" {
  command = plan

  variables {
    install_nginx_ingress = false
    install_cert_manager  = false
    install_external_dns  = false
  }

  module {
    source = "./."
  }

  assert {
    condition     = length(helm_release.nginx_ingress) == 0
    error_message = "NGINX Ingress should not exist when disabled"
  }

  assert {
    condition     = length(helm_release.cert_manager) == 0
    error_message = "Cert-Manager should not exist when disabled"
  }

  assert {
    condition     = length(helm_release.external_dns) == 0
    error_message = "External DNS should not exist when disabled"
  }
}
