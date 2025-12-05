# AKS Module

Azure Kubernetes Service (AKS) cluster configuration.

## Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           AKS Cluster Architecture                          │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│   ┌─────────────────────────────────────────────────────────────────────┐   │
│   │                    Azure Resource Group                              │   │
│   │                                                                     │   │
│   │   ┌─────────────────────────────────────────────────────────────┐   │   │
│   │   │                  AKS Cluster (Private)                      │   │   │
│   │   │                                                             │   │   │
│   │   │   ┌─────────────────────────────────────────────────────┐   │   │   │
│   │   │   │              System Node Pool                       │   │   │   │
│   │   │   │              ┌─────────────────────┐                │   │   │   │
│   │   │   │              │ Standard_B2s        │                │   │   │   │
│   │   │   │              │ (2 vCPU, 4GB RAM)   │                │   │   │   │
│   │   │   │              │ 1-3 nodes           │                │   │   │   │
│   │   │   │              └─────────────────────┘                │   │   │   │
│   │   │   └─────────────────────────────────────────────────────┘   │   │   │
│   │   │                                                             │   │   │
│   │   │   ┌─────────────────────────────────────────────────────┐   │   │   │
│   │   │   │           User Node Pool (Optional)                 │   │   │   │
│   │   │   │              ┌─────────────────────┐                │   │   │   │
│   │   │   │              │ Standard_B2s        │                │   │   │   │
│   │   │   │              │ (Workload VMs)      │                │   │   │   │
│   │   │   │              │ 0-5 nodes           │                │   │   │   │
│   │   │   │              └─────────────────────┘                │   │   │   │
│   │   │   └─────────────────────────────────────────────────────┘   │   │   │
│   │   │                                                             │   │   │
│   │   │   ┌────────────────────┐  ┌────────────────────┐            │   │   │
│   │   │   │ Azure App Routing  │  │ Azure Policy       │            │   │   │
│   │   │   │ (Ingress)          │  │ (Compliance)       │            │   │   │
│   │   │   └────────────────────┘  └────────────────────┘            │   │   │
│   │   │                                                             │   │   │
│   │   └─────────────────────────────────────────────────────────────┘   │   │
│   │                                                                     │   │
│   │   ┌────────────────────┐  ┌────────────────────┐                    │   │
│   │   │ Managed Identity   │  │ Log Analytics      │                    │   │
│   │   │ (Kubelet)          │  │ (OMS Agent)        │                    │   │
│   │   └────────────────────┘  └────────────────────┘                    │   │
│   │                                                                     │   │
│   └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

## Usage

```hcl
module "aks" {
  source = "./modules/aks"

  resource_group_name = azurerm_resource_group.main.name
  resource_group_id   = azurerm_resource_group.main.id
  location            = var.location
  project_name        = var.project_name
  environment         = var.environment

  kubernetes_version      = "1.34"
  sku_tier                = "Free"
  automatic_upgrade       = "patch"
  node_os_upgrade_channel = "NodeImage"

  # System node pool
  system_node_pool_vm_size    = "Standard_B2s"
  system_node_pool_node_count = 1
  system_node_pool_min_count  = 1
  system_node_pool_max_count  = 3

  # Network
  network_plugin    = "azure"
  network_policy    = "azure"
  dns_service_ip    = "10.0.0.10"
  service_cidr      = "10.0.0.0/16"
  load_balancer_sku = "standard"

  # Monitoring
  log_analytics_workspace_id = module.monitoring.log_analytics_workspace_id

  # Security
  private_cluster_enabled    = true
  azure_policy_enabled       = true
  microsoft_defender_enabled = true

  tags = var.tags
}
```

## Inputs

| Name | Description | Type | Default | Required |
|------|-------------|------|---------|:--------:|
| `resource_group_name` | Resource group name | `string` | - | ✅ |
| `resource_group_id` | Resource group ID | `string` | - | ✅ |
| `location` | Azure region | `string` | - | ✅ |
| `project_name` | Project name | `string` | - | ✅ |
| `environment` | Environment (dev, prod) | `string` | - | ✅ |
| `kubernetes_version` | Kubernetes version | `string` | - | ✅ |
| `sku_tier` | AKS SKU tier | `string` | `"Free"` | ❌ |
| `system_node_pool_vm_size` | VM size for system pool | `string` | `"Standard_B2s"` | ❌ |
| `private_cluster_enabled` | Enable private cluster | `bool` | `true` | ❌ |
| `azure_policy_enabled` | Enable Azure Policy | `bool` | `true` | ❌ |

## Outputs

| Name | Description |
|------|-------------|
| `cluster_id` | AKS cluster ID |
| `cluster_name` | AKS cluster name |
| `cluster_fqdn` | AKS cluster FQDN |
| `kubelet_identity` | Kubelet managed identity |
| `oidc_issuer_url` | OIDC issuer URL for workload identity |
| `kube_config` | Kubernetes config (sensitive) |

## Node Pool Sizing

```
┌──────────────────────────────────────────────────────────────────────────┐
│  VM Size Recommendations                                                 │
├──────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│  💰 Budget/Learning (B-series - Burstable):                              │
│  ├── Standard_B2s  │ 2 vCPU, 4 GB  │ ~$30/month  │ Light workloads       │
│  ├── Standard_B2ms │ 2 vCPU, 8 GB  │ ~$60/month  │ More memory           │
│  └── Standard_B4ms │ 4 vCPU, 16 GB │ ~$120/month │ Medium workloads      │
│                                                                          │
│  🏢 Production (D-series - General Purpose):                             │
│  ├── Standard_D2s_v3 │ 2 vCPU, 8 GB   │ ~$70/month  │ Small prod          │
│  ├── Standard_D4s_v3 │ 4 vCPU, 16 GB  │ ~$140/month │ Medium prod         │
│  └── Standard_D8s_v3 │ 8 vCPU, 32 GB  │ ~$280/month │ Large prod          │
│                                                                          │
│  🧠 Memory-Optimized (E-series):                                         │
│  └── Standard_E2s_v3 │ 2 vCPU, 16 GB  │ ~$100/month │ ML/Data workloads   │
│                                                                          │
└──────────────────────────────────────────────────────────────────────────┘
```

## Security Features

| Feature | Description |
|---------|-------------|
| **Private Cluster** | API server not exposed to internet |
| **Azure Policy** | Kubernetes policy enforcement |
| **Microsoft Defender** | Container vulnerability scanning |
| **Managed Identity** | No credentials to manage |
| **OIDC Issuer** | Workload identity for pods |

## Addons

| Addon | Description | Status |
|-------|-------------|--------|
| Azure App Routing | Managed NGINX ingress | ✅ Enabled |
| Azure Monitor | Container Insights | ✅ Enabled |
| Azure Policy | Governance policies | ⚙️ Optional |
| Microsoft Defender | Security scanning | ⚙️ Optional |
| Key Vault CSI | Secrets integration | ⚙️ Separate module |
