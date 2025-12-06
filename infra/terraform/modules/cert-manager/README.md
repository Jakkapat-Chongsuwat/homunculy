# Cert-Manager Module

Deploys cert-manager for automatic TLS certificate management with Let's Encrypt.

## Features

- **Public Clusters**: Uses Helm provider directly
- **Private Clusters**: Uses `az aks command invoke`
- Let's Encrypt ClusterIssuers (staging & production)
- Prometheus metrics support

## Usage

### Public Cluster

```hcl
module "cert_manager" {
  source = "./modules/cert-manager"

  enabled           = true
  letsencrypt_email = "admin@example.com"
}
```

### Private Cluster

```hcl
module "cert_manager" {
  source = "./modules/cert-manager"

  enabled             = true
  letsencrypt_email   = "admin@example.com"
  use_command_invoke  = true
  resource_group_name = azurerm_resource_group.main.name
  aks_cluster_name    = module.aks.cluster_name
  aks_cluster_id      = module.aks.cluster_id
}
```

## Inputs

| Name | Description | Type | Default |
|------|-------------|------|---------|
| `enabled` | Install cert-manager | `bool` | `true` |
| `chart_version` | Helm chart version | `string` | `"v1.14.0"` |
| `letsencrypt_email` | Email for Let's Encrypt | `string` | required |
| `create_cluster_issuers` | Create ClusterIssuers | `bool` | `true` |
| `ingress_class` | Ingress class for ACME | `string` | `"nginx"` |
| `use_command_invoke` | Use for private clusters | `bool` | `false` |

## Outputs

| Name | Description |
|------|-------------|
| `namespace` | Namespace where installed |
| `staging_issuer` | Staging ClusterIssuer name |
| `production_issuer` | Production ClusterIssuer name |
