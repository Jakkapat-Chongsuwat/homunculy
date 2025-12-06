# External-DNS Module

Deploys external-dns for automatic DNS record management with Azure DNS.

## Features

- **Public Clusters**: Uses Helm provider directly
- **Private Clusters**: Uses `az aks command invoke`
- Azure DNS integration with Managed Identity
- Configurable sync policy and domain filters

## Usage

### Public Cluster

```hcl
module "external_dns" {
  source = "./modules/external-dns"

  enabled               = true
  dns_resource_group    = "rg-dns"
  azure_tenant_id       = data.azurerm_client_config.current.tenant_id
  azure_subscription_id = data.azurerm_client_config.current.subscription_id
  domain_filters        = ["homunculy.io"]
}
```

### Private Cluster

```hcl
module "external_dns" {
  source = "./modules/external-dns"

  enabled               = true
  dns_resource_group    = "rg-dns"
  azure_tenant_id       = data.azurerm_client_config.current.tenant_id
  azure_subscription_id = data.azurerm_client_config.current.subscription_id
  domain_filters        = ["homunculy.io"]
  
  use_command_invoke  = true
  resource_group_name = azurerm_resource_group.main.name
  aks_cluster_name    = module.aks.cluster_name
  aks_cluster_id      = module.aks.cluster_id
}
```

## Inputs

| Name | Description | Type | Default |
|------|-------------|------|---------|
| `enabled` | Install external-dns | `bool` | `true` |
| `chart_version` | Helm chart version | `string` | `"1.14.0"` |
| `dns_resource_group` | RG with DNS zone | `string` | required |
| `azure_tenant_id` | Azure tenant ID | `string` | required |
| `azure_subscription_id` | Azure subscription ID | `string` | required |
| `domain_filters` | Domains to manage | `list(string)` | `[]` |
| `sync_policy` | sync or upsert-only | `string` | `"sync"` |
| `use_command_invoke` | Use for private clusters | `bool` | `false` |

## Outputs

| Name | Description |
|------|-------------|
| `namespace` | Namespace where installed |
| `managed_domains` | List of managed domains |
| `installation_method` | helm-release or az-aks-command-invoke |
