# =============================================================================
# Cert-Manager Module
# =============================================================================
# Purpose: Install cert-manager for TLS certificate automation
# Supports both public clusters (helm_release) and private clusters (az aks command invoke)
# =============================================================================

# =============================================================================
# Option 1: Public Cluster - Use Helm Provider directly
# =============================================================================

resource "helm_release" "cert_manager" {
  count = var.enabled && !var.use_command_invoke ? 1 : 0

  name             = "cert-manager"
  repository       = "https://charts.jetstack.io"
  chart            = "cert-manager"
  version          = var.chart_version
  namespace        = "cert-manager"
  create_namespace = true
  wait             = true
  timeout          = 600

  values = [yamlencode({
    installCRDs = true
    prometheus = {
      enabled = var.enable_metrics
    }
    webhook = {
      timeoutSeconds = 30
    }
  })]
}

# Let's Encrypt ClusterIssuer - Staging (for testing)
resource "kubectl_manifest" "letsencrypt_staging" {
  count = var.enabled && !var.use_command_invoke && var.create_cluster_issuers ? 1 : 0

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
              class: ${var.ingress_class}
  YAML

  depends_on = [helm_release.cert_manager]
}

# Let's Encrypt ClusterIssuer - Production
resource "kubectl_manifest" "letsencrypt_prod" {
  count = var.enabled && !var.use_command_invoke && var.create_cluster_issuers ? 1 : 0

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
              class: ${var.ingress_class}
  YAML

  depends_on = [helm_release.cert_manager]
}

# =============================================================================
# Option 2: Private Cluster - Use az aks command invoke
# =============================================================================
# Command breakdown:
# 1. helm repo add   - Add jetstack Helm repository
# 2. helm repo update - Fetch latest chart versions
# 3. kubectl create ns - Create namespace (idempotent)
# 4. helm upgrade    - Install cert-manager with CRDs
# 5. kubectl apply   - Create ClusterIssuers for Let's Encrypt
# =============================================================================

resource "null_resource" "cert_manager" {
  count = var.enabled && var.use_command_invoke ? 1 : 0

  triggers = {
    chart_version = var.chart_version
    cluster_id    = var.aks_cluster_id
  }

  provisioner "local-exec" {
    interpreter = ["bash", "-c"]
    command     = <<-EOT
      set -e
      
      echo "=== Installing cert-manager on private AKS cluster ==="
      
      az aks command invoke \
        --resource-group "${var.resource_group_name}" \
        --name "${var.aks_cluster_name}" \
        --command "
          helm repo add jetstack https://charts.jetstack.io && \
          helm repo update && \
          kubectl create namespace cert-manager --dry-run=client -o yaml | kubectl apply -f - && \
          helm upgrade --install cert-manager jetstack/cert-manager \
            --namespace cert-manager \
            --version ${var.chart_version} \
            --set installCRDs=true \
            --set prometheus.enabled=${var.enable_metrics} \
            --set webhook.timeoutSeconds=30 \
            --wait \
            --timeout 10m && \
          echo 'cert-manager installed!' && \
          kubectl get pods -n cert-manager
        "
      
      echo "=== cert-manager installation complete ==="
    EOT
  }
}

# Create ClusterIssuers for private cluster
resource "null_resource" "cluster_issuers" {
  count = var.enabled && var.use_command_invoke && var.create_cluster_issuers ? 1 : 0

  triggers = {
    email         = var.letsencrypt_email
    ingress_class = var.ingress_class
  }

  provisioner "local-exec" {
    interpreter = ["bash", "-c"]
    command     = <<-EOT
      set -e
      
      echo "=== Creating ClusterIssuers ==="
      
      az aks command invoke \
        --resource-group "${var.resource_group_name}" \
        --name "${var.aks_cluster_name}" \
        --command "
          cat <<'ISSUEREOF' | kubectl apply -f -
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
          class: ${var.ingress_class}
---
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
          class: ${var.ingress_class}
ISSUEREOF
          echo 'ClusterIssuers created!'
        "
      
      echo "=== ClusterIssuers created ==="
    EOT
  }

  depends_on = [null_resource.cert_manager]
}
