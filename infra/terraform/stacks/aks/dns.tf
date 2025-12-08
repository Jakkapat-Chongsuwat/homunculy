# =============================================================================
# CoreDNS Custom Stub Domains (Privatelink PostgreSQL)
# =============================================================================
# Applies a custom CoreDNS server block that forwards PostgreSQL zones to
# Azure DNS (168.63.129.16) so pods can resolve the privatelink endpoint.
# Executed via AKS runCommand to work with private clusters.
# =============================================================================

locals {
  coredns_custom_manifest = file("${path.module}/../../../k8s/platform/coredns-custom.yaml")
}

resource "azapi_resource_action" "coredns_custom" {
  type        = "Microsoft.ContainerService/managedClusters@2024-02-01"
  resource_id = module.aks.cluster_id
  action      = "runCommand"
  method      = "POST"

  body = {
    command = <<-EOT
set -euo pipefail

cat <<'EOF' >/tmp/coredns-custom.yaml
${local.coredns_custom_manifest}
EOF

kubectl apply -f /tmp/coredns-custom.yaml
kubectl rollout restart -n kube-system deployment/coredns
    EOT
  }

  response_export_values = ["properties.logs"]

  depends_on = [module.aks]
}
