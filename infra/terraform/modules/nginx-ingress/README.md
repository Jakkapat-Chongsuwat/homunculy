# NGINX Ingress Controller Module

Deploys NGINX Ingress Controller on AKS for HTTP/HTTPS traffic routing.

## Features

- **Public Clusters**: Uses Helm provider directly
- **Private Clusters**: Uses `az aks command invoke`
- Azure Load Balancer integration with health probes
- Optional internal-only mode (no public IP)
- Prometheus metrics support

## Usage

### Public Cluster

```hcl
module "nginx_ingress" {
  source = "./modules/nginx-ingress"

  enabled       = true
  chart_version = "4.9.0"
  replica_count = 2
  internal_only = false
}
```

### Private Cluster

```hcl
module "nginx_ingress" {
  source = "./modules/nginx-ingress"

  enabled            = true
  use_command_invoke = true
  resource_group_name = azurerm_resource_group.main.name
  aks_cluster_name    = module.aks.cluster_name
  aks_cluster_id      = module.aks.cluster_id
}
```

## Inputs

| Name | Description | Type | Default |
|------|-------------|------|---------|
| `enabled` | Install NGINX Ingress | `bool` | `true` |
| `chart_version` | Helm chart version | `string` | `"4.9.0"` |
| `replica_count` | Number of replicas | `number` | `2` |
| `internal_only` | Internal LB only | `bool` | `false` |
| `enable_metrics` | Enable Prometheus | `bool` | `true` |
| `use_command_invoke` | Use for private clusters | `bool` | `false` |

## Outputs

| Name | Description |
|------|-------------|
| `namespace` | Namespace where installed |
| `service_name` | Ingress service name |
| `installation_method` | helm-release or az-aks-command-invoke |
