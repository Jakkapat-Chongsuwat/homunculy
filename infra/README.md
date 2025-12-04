# Homunculy Infrastructure

Infrastructure as Code (IaC) for deploying Homunculy to Azure with support for multiple deployment architectures.

## Architecture Options

| Stack | Description | Use Case | Monthly Cost (Dev) |
|-------|-------------|----------|-------------------|
| **Container Apps** | Azure Container Apps (serverless) | Simple deployments, cost-effective | ~$20-40 |
| **AKS** | Azure Kubernetes Service | Full K8s control, GitOps, complex workloads | ~$80-100 |

---

## Container Apps Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         Azure Resource Group                                 │
│                         (rg-homunculy-dev)                                   │
│                                                                              │
│  ┌────────────────────────────────────────────────────────────────────────┐ │
│  │                 Azure Container Apps Environment                        │ │
│  │                 (cae-homunculy-dev)                                     │ │
│  │                                                                         │ │
│  │   ┌─────────────────────┐         ┌─────────────────────┐               │ │
│  │   │    chat-client      │────────▶│   homunculy-app     │               │ │
│  │   │   (Blazor Server)   │         │   (Python FastAPI)  │               │ │
│  │   │                     │         │                     │               │ │
│  │   │   Port: 8080        │         │   Port: 8000        │               │ │
│  │   │   0-2 replicas      │         │   0-2 replicas      │               │ │
│  │   └─────────────────────┘         └──────────┬──────────┘               │ │
│  │                                              │                          │ │
│  └──────────────────────────────────────────────┼──────────────────────────┘ │
│                                                 │                            │
│                                                 ▼                            │
│  ┌─────────────────────┐              ┌─────────────────────┐               │
│  │   PostgreSQL        │              │   Key Vault         │               │
│  │   Flexible Server   │              │   (Secrets)         │               │
│  │   (psql-homunculy)  │              │   - OpenAI Key      │               │
│  │                     │              │   - ElevenLabs Key  │               │
│  │   • homunculy DB    │              │   - DB Password     │               │
│  └─────────────────────┘              └─────────────────────┘               │
│                                                                              │
│  ┌─────────────────────┐              ┌─────────────────────┐               │
│  │   Container         │              │   Log Analytics     │               │
│  │   Registry (ACR)    │              │   Workspace         │               │
│  │                     │              │                     │               │
│  │   • homunculy-app   │              │   Application       │               │
│  │   • chat-client     │              │   Insights          │               │
│  └─────────────────────┘              └─────────────────────┘               │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## AKS Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         Azure Resource Group                                 │
│                         (rg-homunculy-aks-dev)                               │
│                                                                              │
│  ┌────────────────────────────────────────────────────────────────────────┐ │
│  │                    Azure Kubernetes Service                             │ │
│  │                    (aks-homunculy-dev)                                  │ │
│  │                                                                         │ │
│  │   ┌─────────────────────────────────────────────────────────────────┐  │ │
│  │   │                    System Node Pool                              │  │ │
│  │   │                    (1-3 nodes, Standard_B2s)                     │  │ │
│  │   │                                                                  │  │ │
│  │   │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐              │  │ │
│  │   │  │ chat-client │  │ homunculy   │  │ CoreDNS     │              │  │ │
│  │   │  │ Deployment  │  │ Deployment  │  │ kube-proxy  │              │  │ │
│  │   │  │             │  │             │  │ CSI drivers │              │  │ │
│  │   │  └─────────────┘  └──────┬──────┘  └─────────────┘              │  │ │
│  │   │                          │                                       │  │ │
│  │   └──────────────────────────┼───────────────────────────────────────┘  │ │
│  │                              │                                          │ │
│  │   Features:                  │                                          │ │
│  │   • Workload Identity        │                                          │ │
│  │   • Key Vault CSI Driver     │                                          │ │
│  │   • Azure CNI Networking     │                                          │ │
│  │   • Autoscaling (1-3 nodes)  │                                          │ │
│  │                              │                                          │ │
│  └──────────────────────────────┼──────────────────────────────────────────┘ │
│                                 │                                            │
│                                 ▼                                            │
│  ┌─────────────────────┐              ┌─────────────────────┐               │
│  │   PostgreSQL        │              │   Key Vault         │               │
│  │   Flexible Server   │              │   (Secrets)         │               │
│  │   (psql-homunculy)  │              │   - OpenAI Key      │               │
│  │                     │              │   - ElevenLabs Key  │               │
│  │   • homunculy DB    │              │   - DB Password     │               │
│  └─────────────────────┘              └─────────────────────┘               │
│                                                                              │
│  ┌─────────────────────┐              ┌─────────────────────┐               │
│  │   Container         │              │   Log Analytics     │               │
│  │   Registry (ACR)    │              │   Workspace         │               │
│  │                     │              │                     │               │
│  │   • homunculy-app   │              │   Application       │               │
│  │   • chat-client     │              │   Insights          │               │
│  └─────────────────────┘              └─────────────────────┘               │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Directory Structure

```
infra/
└── terraform/
    ├── stacks/                         # Deployment architectures
    │   ├── container-apps/             # Container Apps stack
    │   │   ├── main.tf
    │   │   ├── variables.tf
    │   │   ├── outputs.tf
    │   │   ├── providers.tf
    │   │   ├── backend.tf
    │   │   ├── versions.tf
    │   │   └── tests/
    │   │       └── stack.tftest.hcl
    │   └── aks/                        # AKS stack
    │       ├── main.tf
    │       ├── variables.tf
    │       ├── outputs.tf
    │       ├── providers.tf
    │       ├── backend.tf
    │       ├── versions.tf
    │       └── tests/
    │           └── stack.tftest.hcl
    ├── modules/                        # Reusable modules
    │   ├── aks/                        # AKS cluster
    │   ├── container-apps/             # Container Apps
    │   ├── container-registry/         # ACR (shared)
    │   ├── database/                   # PostgreSQL (shared)
    │   ├── keyvault/                   # Key Vault (shared)
    │   └── monitoring/                 # Log Analytics (shared)
    ├── environments/                   # Environment configurations
    │   ├── dev/
    │   │   ├── backend.tfvars
    │   │   ├── container-apps.tfvars
    │   │   └── aks.tfvars
    │   └── prod/
    │       ├── backend.tfvars
    │       ├── container-apps.tfvars
    │       └── aks.tfvars
    └── tests/                          # Module unit tests
        ├── aks.tftest.hcl
        ├── container-apps.tftest.hcl
        ├── container-registry.tftest.hcl
        ├── database.tftest.hcl
        ├── keyvault.tftest.hcl
        └── monitoring.tftest.hcl
```

---

## Quick Start

### Prerequisites

1. **Azure CLI** installed and logged in
2. **Terraform** >= 1.9.0
3. **Azure Subscription** with appropriate permissions

### Set Environment Variables

```bash
export TF_VAR_subscription_id=$(az account show --query id -o tsv)
export TF_VAR_openai_api_key="your-openai-key"
export TF_VAR_elevenlabs_api_key="your-elevenlabs-key"
```

### Deploy Container Apps (Dev)

```bash
cd infra/terraform/stacks/container-apps

# Initialize
terraform init

# Plan
terraform plan -var-file=../../environments/dev/container-apps.tfvars

# Apply
terraform apply -var-file=../../environments/dev/container-apps.tfvars
```

### Deploy AKS (Dev)

```bash
cd infra/terraform/stacks/aks

# Initialize
terraform init

# Plan
terraform plan -var-file=../../environments/dev/aks.tfvars

# Apply
terraform apply -var-file=../../environments/dev/aks.tfvars
```

---

## Testing

### Run All Module Tests

```bash
cd infra/terraform
terraform test
```

### Run Specific Module Test

```bash
terraform test -filter=tests/aks.tftest.hcl
terraform test -filter=tests/container-apps.tftest.hcl
terraform test -filter=tests/database.tftest.hcl
```

### Run Stack Integration Tests

```bash
# Container Apps stack
cd stacks/container-apps
terraform test

# AKS stack
cd stacks/aks
terraform test
```

---

## Terraform Cloud Workspaces

Create these workspaces in Terraform Cloud:

| Workspace | Tags | Description |
|-----------|------|-------------|
| `homunculy-container-apps-dev` | container-apps, dev | Dev Container Apps |
| `homunculy-container-apps-prod` | container-apps, prod | Prod Container Apps |
| `homunculy-aks-dev` | aks, dev | Dev AKS |
| `homunculy-aks-prod` | aks, prod | Prod AKS |

Set **Execution Mode** to **Local** for all workspaces.

---

## Destroying Infrastructure

### Container Apps

```bash
cd infra/terraform/stacks/container-apps
terraform destroy -var-file=../../environments/dev/container-apps.tfvars
```

### AKS

```bash
cd infra/terraform/stacks/aks
terraform destroy -var-file=../../environments/dev/aks.tfvars
```

---

## CI/CD Pipeline

GitHub Actions workflows in `.github/workflows/`:

| Workflow | Trigger | Description |
|----------|---------|-------------|
| `deploy-infra.yml` | Push to main | Deploy/update infrastructure |
| `build-images.yml` | Push to main | Build and push Docker images |
| `destroy-infra.yml` | Manual | Tear down infrastructure |

### GitHub Secrets Required

| Secret | Description |
|--------|-------------|
| `AZURE_CLIENT_ID` | Azure Service Principal App ID |
| `AZURE_TENANT_ID` | Azure Tenant ID |
| `AZURE_SUBSCRIPTION_ID` | Azure Subscription ID |
| `TF_VAR_openai_api_key` | OpenAI API Key |
| `TF_VAR_elevenlabs_api_key` | ElevenLabs API Key |

---

## Cost Comparison

| Component | Container Apps (Dev) | Container Apps (Prod) | AKS (Dev) | AKS (Prod) |
|-----------|---------------------|----------------------|-----------|------------|
| Compute | Pay-per-use | Pay-per-use | ~$60/mo | ~$200/mo |
| Database | ~$15/mo | ~$100/mo | ~$15/mo | ~$100/mo |
| Registry | ~$5/mo | ~$20/mo | ~$5/mo | ~$20/mo |
| Key Vault | ~$1/mo | ~$1/mo | ~$1/mo | ~$1/mo |
| Monitoring | ~$5/mo | ~$20/mo | ~$5/mo | ~$20/mo |
| **Total** | **~$25-50/mo** | **~$150-250/mo** | **~$85-100/mo** | **~$350-450/mo** |

**Recommendation:**
- **Dev/Staging**: Use Container Apps (cost-effective, serverless)
- **Production**: Use AKS if you need advanced Kubernetes features, GitOps, or custom networking

---

## Security

- ✅ All secrets stored in Azure Key Vault
- ✅ Managed Identities for authentication (no stored credentials)
- ✅ OIDC for GitHub Actions
- ✅ RBAC enabled on Key Vault
- ✅ Network policies for AKS
- ✅ Workload Identity for AKS pods

---

## Migration Path

To migrate from Container Apps to AKS:

1. Deploy AKS stack (creates separate resource group)
2. Create Kubernetes manifests for your apps
3. Update CI/CD to deploy to AKS
4. Test thoroughly in AKS environment
5. Switch DNS/traffic to AKS
6. Destroy Container Apps stack

Both stacks can run simultaneously during migration.
