# =============================================================================
# NGINX Ingress Controller Module
# =============================================================================
# Purpose: Install NGINX Ingress Controller on AKS
# Supports both public clusters (helm_release) and private clusters (az aks command invoke)
# =============================================================================

# =============================================================================
# Option 1: Public Cluster - Use Helm Provider directly
# =============================================================================

resource "helm_release" "nginx_ingress" {
  count = var.enabled && !var.use_command_invoke ? 1 : 0

  name             = "ingress-nginx"
  repository       = "https://kubernetes.github.io/ingress-nginx"
  chart            = "ingress-nginx"
  version          = var.chart_version
  namespace        = "ingress-nginx"
  create_namespace = true
  wait             = true
  timeout          = 600

  values = [yamlencode({
    controller = {
      replicaCount = var.replica_count
      service = {
        externalTrafficPolicy = "Local"
        annotations = merge(
          {
            "service.beta.kubernetes.io/azure-load-balancer-health-probe-request-path" = "/healthz"
          },
          var.internal_only ? {
            "service.beta.kubernetes.io/azure-load-balancer-internal" = "true"
          } : {}
        )
      }
      metrics = {
        enabled = var.enable_metrics
      }
      podAnnotations = var.enable_metrics ? {
        "prometheus.io/scrape" = "true"
        "prometheus.io/port"   = "10254"
      } : {}
    }
  })]
}

# =============================================================================
# Option 2: Private Cluster - Use az aks command invoke
# =============================================================================
# Command breakdown:
# 1. helm repo add     - Add ingress-nginx Helm repository
# 2. helm repo update  - Fetch latest chart versions
# 3. kubectl create ns - Create namespace (idempotent with --dry-run)
# 4. helm upgrade      - Install or upgrade the chart
#    --install         - Install if not present
#    --wait            - Wait for pods to be ready
#    --timeout         - Maximum wait time
# =============================================================================

resource "null_resource" "nginx_ingress" {
  count = var.enabled && var.use_command_invoke ? 1 : 0

  triggers = {
    chart_version = var.chart_version
    cluster_id    = var.aks_cluster_id
  }

  provisioner "local-exec" {
    interpreter = ["bash", "-c"]
    command     = <<-EOT
      set -e
      
      echo "=== Installing NGINX Ingress on private AKS cluster ==="
      
      az aks command invoke \
        --resource-group "${var.resource_group_name}" \
        --name "${var.aks_cluster_name}" \
        --command "
          helm repo add ingress-nginx https://kubernetes.github.io/ingress-nginx && \
          helm repo update && \
          kubectl create namespace ingress-nginx --dry-run=client -o yaml | kubectl apply -f - && \
          helm upgrade --install ingress-nginx ingress-nginx/ingress-nginx \
            --namespace ingress-nginx \
            --version ${var.chart_version} \
            --set controller.replicaCount=${var.replica_count} \
            --set controller.service.externalTrafficPolicy=Local \
            --set controller.service.annotations.'service\.beta\.kubernetes\.io/azure-load-balancer-health-probe-request-path'=/healthz \
            ${var.internal_only ? "--set controller.service.annotations.'service\\.beta\\.kubernetes\\.io/azure-load-balancer-internal'=true" : ""} \
            --set controller.metrics.enabled=${var.enable_metrics} \
            --wait \
            --timeout 10m && \
          echo 'NGINX Ingress installed!' && \
          kubectl get pods -n ingress-nginx
        "
      
      echo "=== NGINX Ingress installation complete ==="
    EOT
  }
}
