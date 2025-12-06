# =============================================================================
# External-DNS Module
# =============================================================================
# Purpose: Install external-dns for automatic DNS record management
# Supports both public clusters (helm_release) and private clusters (az aks command invoke)
# =============================================================================

# =============================================================================
# Option 1: Public Cluster - Use Helm Provider directly
# =============================================================================

resource "helm_release" "external_dns" {
  count = var.enabled && !var.use_command_invoke ? 1 : 0

  name             = "external-dns"
  repository       = "https://kubernetes-sigs.github.io/external-dns"
  chart            = "external-dns"
  version          = var.chart_version
  namespace        = "external-dns"
  create_namespace = true
  wait             = true
  timeout          = 600

  values = [yamlencode({
    provider = "azure"
    azure = {
      resourceGroup               = var.dns_resource_group
      tenantId                    = var.azure_tenant_id
      subscriptionId              = var.azure_subscription_id
      useManagedIdentityExtension = true
    }
    domainFilters = var.domain_filters
    txtOwnerId    = var.txt_owner_id
    policy        = var.sync_policy
    sources       = var.sources
  })]
}

# =============================================================================
# Option 2: Private Cluster - Use az aks command invoke
# =============================================================================
# Command breakdown:
# 1. helm repo add   - Add external-dns Helm repository
# 2. helm repo update - Fetch latest chart versions
# 3. kubectl create ns - Create namespace
# 4. helm upgrade    - Install external-dns with Azure config
# =============================================================================

resource "null_resource" "external_dns" {
  count = var.enabled && var.use_command_invoke ? 1 : 0

  triggers = {
    chart_version = var.chart_version
    cluster_id    = var.aks_cluster_id
  }

  provisioner "local-exec" {
    interpreter = ["bash", "-c"]
    command     = <<-EOT
      set -e
      
      echo "=== Installing external-dns on private AKS cluster ==="
      
      # Convert domain filters array to comma-separated for --set
      DOMAIN_FILTERS="${join(",", var.domain_filters)}"
      
      az aks command invoke \
        --resource-group "${var.resource_group_name}" \
        --name "${var.aks_cluster_name}" \
        --command "
          helm repo add external-dns https://kubernetes-sigs.github.io/external-dns && \
          helm repo update && \
          kubectl create namespace external-dns --dry-run=client -o yaml | kubectl apply -f - && \
          helm upgrade --install external-dns external-dns/external-dns \
            --namespace external-dns \
            --version ${var.chart_version} \
            --set provider=azure \
            --set azure.resourceGroup=${var.dns_resource_group} \
            --set azure.tenantId=${var.azure_tenant_id} \
            --set azure.subscriptionId=${var.azure_subscription_id} \
            --set azure.useManagedIdentityExtension=true \
            --set txtOwnerId=${var.txt_owner_id} \
            --set policy=${var.sync_policy} \
            --set 'domainFilters={$DOMAIN_FILTERS}' \
            --set 'sources={${join(",", var.sources)}}' \
            --wait \
            --timeout 10m && \
          echo 'external-dns installed!' && \
          kubectl get pods -n external-dns
        "
      
      echo "=== external-dns installation complete ==="
    EOT
  }
}
