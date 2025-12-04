# =============================================================================
# Kubernetes Add-ons Module - Main Configuration
# =============================================================================
# Purpose: Install and configure Kubernetes add-ons via Helm
# Includes: NGINX Ingress, Cert-Manager, External-DNS
# Following: Clean Architecture - single responsibility module
# =============================================================================

# -----------------------------------------------------------------------------
# NGINX Ingress Controller
# -----------------------------------------------------------------------------

resource "helm_release" "nginx_ingress" {
  count = var.install_nginx_ingress ? 1 : 0

  name             = "ingress-nginx"
  repository       = "https://kubernetes.github.io/ingress-nginx"
  chart            = "ingress-nginx"
  version          = var.nginx_ingress_version
  namespace        = "ingress-nginx"
  create_namespace = true

  values = [yamlencode({
    controller = {
      replicaCount = var.nginx_ingress_replica_count
      service = {
        externalTrafficPolicy = "Local"
        annotations = merge(
          { "service.beta.kubernetes.io/azure-load-balancer-health-probe-request-path" = "/healthz" },
          var.nginx_ingress_internal_only ? { "service.beta.kubernetes.io/azure-load-balancer-internal" = "true" } : {}
        )
      }
      metrics = {
        enabled = true
      }
      podAnnotations = {
        "prometheus.io/scrape" = "true"
        "prometheus.io/port"   = "10254"
      }
    }
  })]
}

# -----------------------------------------------------------------------------
# Cert-Manager for TLS Certificates
# -----------------------------------------------------------------------------

resource "helm_release" "cert_manager" {
  count = var.install_cert_manager ? 1 : 0

  name             = "cert-manager"
  repository       = "https://charts.jetstack.io"
  chart            = "cert-manager"
  version          = var.cert_manager_version
  namespace        = "cert-manager"
  create_namespace = true

  values = [yamlencode({
    installCRDs = true
    prometheus = {
      enabled = true
    }
    webhook = {
      timeoutSeconds = 30
    }
  })]
}

# Let's Encrypt ClusterIssuer for staging
resource "kubectl_manifest" "letsencrypt_staging" {
  count = var.install_cert_manager && var.create_cluster_issuers ? 1 : 0

  yaml_body = <<-YAML
    apiVersion: cert-manager.io/v1
    kind: ClusterIssuer
    metadata:
      name: letsencrypt-staging
    spec:
      acme:
        server: https://acme-staging-v02.api.letsencrypt.org/directory
        email: ${var.letsencrypt_email}
        privateKeySecretRef:
          name: letsencrypt-staging
        solvers:
        - http01:
            ingress:
              class: nginx
  YAML

  depends_on = [helm_release.cert_manager]
}

# Let's Encrypt ClusterIssuer for production
resource "kubectl_manifest" "letsencrypt_prod" {
  count = var.install_cert_manager && var.create_cluster_issuers ? 1 : 0

  yaml_body = <<-YAML
    apiVersion: cert-manager.io/v1
    kind: ClusterIssuer
    metadata:
      name: letsencrypt-prod
    spec:
      acme:
        server: https://acme-v02.api.letsencrypt.org/directory
        email: ${var.letsencrypt_email}
        privateKeySecretRef:
          name: letsencrypt-prod
        solvers:
        - http01:
            ingress:
              class: nginx
  YAML

  depends_on = [helm_release.cert_manager]
}

# -----------------------------------------------------------------------------
# External DNS for automatic DNS record management
# -----------------------------------------------------------------------------

resource "helm_release" "external_dns" {
  count = var.install_external_dns ? 1 : 0

  name             = "external-dns"
  repository       = "https://kubernetes-sigs.github.io/external-dns"
  chart            = "external-dns"
  version          = var.external_dns_version
  namespace        = "external-dns"
  create_namespace = true

  values = [yamlencode({
    provider = "azure"
    azure = {
      resourceGroup               = var.dns_resource_group
      tenantId                    = var.azure_tenant_id
      subscriptionId              = var.azure_subscription_id
      useManagedIdentityExtension = true
    }
    domainFilters = [var.domain_filter]
    txtOwnerId    = var.external_dns_txt_owner_id
    policy        = "sync"
    sources       = ["ingress", "service"]
  })]
}
