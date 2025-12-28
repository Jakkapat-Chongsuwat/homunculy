locals {
  coredns_custom_manifest = file("${path.module}/../../../k8s/platform/coredns/coredns-custom.yaml")
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
