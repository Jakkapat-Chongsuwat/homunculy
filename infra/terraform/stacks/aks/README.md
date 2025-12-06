# 🏰 AKS Stack - Private Kubernetes Cluster

> **"Gated Community with No Public Entrance"** - Hackers can't even SEE your city from the internet.

## Architecture

```
                                      ☁️ INTERNET
                                           │
                         ┌─────────────────┴─────────────────┐
                         │  📡 External DNS (you buy domain) │
                         │  api.homunculy.com → Load Balancer│
                         └─────────────────┬─────────────────┘
                                           │
                                           ▼
                      ┌────────────────────────────────────────┐
                      │     🚪 CITY GATE                       │
                      │     Azure Application Routing          │
                      │     (Managed NGINX + TLS)              │
                      │                                        │
                      │  ✅ WITH: HTTPS only, TLS termination  │
                      │  ❌ WITHOUT: Direct pod exposure = 💀  │
                      └────────────────────────────────────────┘
                                           │
    ════════════════════════════════════════════════════════════════════
                  🧱🧱🧱 CITY WALLS - Private VNet (10.0.0.0/8) 🧱🧱🧱
                                                                        
                  ✅ WITH: API server invisible to internet             
                  ❌ WITHOUT: Hackers scan & attack your cluster        
    ════════════════════════════════════════════════════════════════════
         │                         │                        │
         ▼                         ▼                        ▼
    ┌──────────────┐       ┌───────────────┐       ┌───────────────┐
    │  🏛️ CITY HALL │       │  💰 TREASURY  │       │  👑 ROYAL     │
    │   AKS Cluster │◄─────►│  PostgreSQL   │       │     VAULT     │
    │               │       │               │       │   Key Vault   │
    │  ┌─────────┐  │       │  Citizens'    │       │               │
    │  │🏠 Pods  │  │       │  Data & Gold  │       │  👑 API Keys  │
    │  │(Workers)│  │       │               │       │  🔐 TLS Certs │
    │  └─────────┘  │       │ ✅ Private    │       │  🗝️ Secrets   │
    │               │       │    Endpoint   │       │               │
    │ ✅ Workloads  │       │ ❌ Public =   │       │ ✅ Rotated    │
    │    isolated   │       │    SQL inject │       │ ❌ Hardcode = │
    │ 10.1.0.0/16   │       │ 10.2.0.0/24   │       │    leaked 💀  │
    └──────────────┘       └───────────────┘       └───────────────┘
           │
           │  Inside City Hall:
           │
           ├── ⚔️ Armory ──────────── Container Registry
           │   ✅ Private images  ❌ Docker Hub = supply chain attack
           │
           ├── 🗼 Watchtower ───────── Log Analytics
           │   ✅ See all activity  ❌ No logs = blind to attacks
           │
           ├── 🛡️ Royal Guard ──────── Microsoft Defender
           │   ✅ Runtime protection  ❌ No defender = malware runs free
           │
           │  City Laws & Patrols:
           │
           ├── 📜 City Laws ─────────── Azure Policy
           │   ✅ Block privileged pods  ❌ No policy = root containers
           │
           ├── 🚔 Street Patrol ────── Network Policy
           │   ✅ Pod-to-pod firewall  ❌ No policy = lateral movement
           │
           │  City Services:
           │
           ├── 🎭 Identity Masks ───── Workload Identity
           │   ✅ No credentials in code  ❌ Hardcoded keys = breach
           │
           ├── 🔑 Secret Tunnels ───── Key Vault CSI
           │   ✅ Secrets as volumes  ❌ Env vars = exposed in logs
           │
           └── 🏺 Time Capsule ─────── Velero Backup
               ✅ Recover from disaster  ❌ No backup = game over
```

## City Analogy

| Azure Resource | 🏰 City Building | Role |
|----------------|------------------|------|
| **Infrastructure** | | |
| Private VNet | 🧱 City Walls | Surrounds everything, no gaps |
| AKS Cluster | 🏛️ City Hall | Central government, runs the city |
| Subnets | 🏘️ Districts | AKS district, DB district, Vault district |
| **Services** | | |
| App Routing | 🚪 City Gate | Only way in, checks every visitor |
| PostgreSQL | 💰 Treasury | Gold vault for all citizen data |
| Key Vault | 👑 Royal Vault | Crown jewels: API keys, TLS certs |
| ACR | ⚔️ Armory | Stores all weapons (container images) |
| **Security Forces** | | |
| Network Policy | 🚔 Street Patrol | Controls who can visit whom |
| Azure Policy | 📜 City Laws | "No privileged containers!" |
| Defender | 🛡️ Royal Guard | Hunts threats in real-time |
| RBAC | 🎖️ Rank Badges | King, Knight, Peasant access levels |
| **Operations** | | |
| Log Analytics | 🗼 Watchtower | Sees everything, logs all activity |
| Monitoring | 📊 Census Bureau | Tracks population (CPU/memory) |
| Velero | 🏺 Time Capsule | Backup the entire city daily |
| **Addons** | | |
| OIDC/Workload ID | 🎭 Masks | Pods wear trusted identities |
| Key Vault CSI | 🔑 Secret Tunnels | Secrets flow directly to pods |
| Auto-upgrade | 🔧 Maintenance Crew | Keeps walls patched automatically |

## Ingress Flow

```
HTTPS Request → Azure App Routing → Private Load Balancer → AKS Pods
                     │
                     └── TLS cert from Key Vault (automatic)
```

## Network Security Groups (NSG)

```
┌─────────────────────────────────────────────────────────────────────────┐
│  🚔 NSG: nsg-aks-homunculy-prod                                         │
│  Associated with: aks-subnet (10.1.0.0/16)                              │
├─────────────────────────────────────────────────────────────────────────┤
│  INBOUND RULES (processed low→high priority)                           │
│  ┌─────────┬─────────────────────────────┬───────────────────────────┐  │
│  │ Priority│ Rule                        │ Purpose                   │  │
│  ├─────────┼─────────────────────────────┼───────────────────────────┤  │
│  │  65000  │ AllowVnetInBound           │ Pod↔Pod, Node↔Node        │  │
│  │  65001  │ AllowAzureLoadBalancerIn   │ Health probes from LB     │  │
│  │  65500  │ ⛔ DenyAllInBound          │ Block everything else     │  │
│  └─────────┴─────────────────────────────┴───────────────────────────┘  │
│                                                                         │
│  OUTBOUND RULES                                                         │
│  ┌─────────┬─────────────────────────────┬───────────────────────────┐  │
│  │ Priority│ Rule                        │ Purpose                   │  │
│  ├─────────┼─────────────────────────────┼───────────────────────────┤  │
│  │  65000  │ AllowVnetOutBound          │ Pod→DB, Pod→KeyVault      │  │
│  │  65001  │ AllowInternetOutBound      │ Pull images, call APIs    │  │
│  │  65500  │ ⛔ DenyAllOutBound         │ Block everything else     │  │
│  └─────────┴─────────────────────────────┴───────────────────────────┘  │
│                                                                         │
│  📝 Notes:                                                              │
│  • 65000-65500 are Azure defaults (cannot delete)                       │
│  • Custom rules: priority 100-4096                                      │
│  • Ports: DYNAMIC - no fixed ports, uses service tags                   │
│  • "VirtualNetwork" tag = entire VNet + peered VNets                    │
│  • "AzureLoadBalancer" tag = Azure's health probe IPs                   │
└─────────────────────────────────────────────────────────────────────────┘

Why DenyAll at 65500?
├── Security best practice: "deny by default"
├── Only explicitly allowed traffic gets through
└── Acts as catch-all safety net
```

## Quick Start

```bash
cd infra/terraform/stacks/aks
terraform init -backend-config=../../environments/prod/backend.tfvars
terraform plan -var-file=../../environments/prod/aks.tfvars
terraform apply -var-file=../../environments/prod/aks.tfvars
```

## Modules

| Module | Purpose |
|--------|---------|
| `vnet` | Private network + subnets + DNS zones |
| `aks` | Kubernetes cluster + App Routing |
| `database` | PostgreSQL Flexible Server |
| `keyvault` | Secrets + TLS certificates |
| `container-registry` | Container images |
| `monitoring` | Log Analytics + metrics |
| `argocd` | GitOps continuous deployment |
| `velero` | Backup (public clusters only) |

## Key Configuration

```hcl
# Private cluster - no public API
private_cluster_enabled = true

# Azure-managed NGINX (no helm/bastion needed)
enable_app_routing = true

# Security addons
azure_policy_enabled       = true
microsoft_defender_enabled = true

# ArgoCD GitOps
install_argocd = true
```

## ArgoCD GitOps Flow

```
┌─────────────────┐     1. Push code      ┌─────────────────┐
│                 │ ───────────────────►  │                 │
│   Developer     │                       │   GitHub Repo   │
│                 │                       │                 │
└─────────────────┘                       └────────┬────────┘
                                                   │
                                     2. ArgoCD watches repo
                                                   │
                                                   ▼
                                          ┌─────────────────┐
                                          │                 │
                                          │   ArgoCD        │
                                          │   (in cluster)  │
                                          │                 │
                                          └────────┬────────┘
                                                   │
                                     3. Syncs K8s manifests
                                                   │
                                                   ▼
                                          ┌─────────────────┐
                                          │                 │
                                          │   AKS Cluster   │
                                          │   (Workloads)   │
                                          │                 │
                                          └─────────────────┘
```

## Cost Optimization

```
┌─────────────────────────────────────────────────────────────────────────┐
│  💰 Budget-Friendly Configuration                                       │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  AKS Node Pool: Standard_B2s (Burstable)                                │
│  ├── 2 vCPU, 4 GB RAM                                                   │
│  ├── Uses B-series quota (separate from D-series)                       │
│  └── ~$30/month vs ~$70/month for D2s_v3                                │
│                                                                         │
│  PostgreSQL: B_Standard_B1ms (Burstable)                                │
│  ├── 1 vCPU, 2 GB RAM                                                   │
│  └── ~$15/month vs ~$100/month for GP tier                              │
│                                                                         │
│  Total Stack: ~$50-80/month for dev/learning                            │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```
