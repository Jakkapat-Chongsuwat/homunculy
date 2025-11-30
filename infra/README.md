# Homunculy Infrastructure

This directory contains Infrastructure as Code (IaC) for deploying Homunculy to Azure Container Apps.

## Architecture

```
                    ┌─────────────────────────────────────────────────────────────────┐
                    │                    Azure Resource Group                          │
                    │                                                                   │
                    │  ┌──────────────────────────────────────────────────────────────┐│
                    │  │              Azure Container Apps Environment                ││
                    │  │                                                              ││
                    │  │  ┌─────────────────┐    ┌─────────────────┐                  ││
                    │  │  │   chat-client   │───▶│  homunculy-app  │                  ││
                    │  │  │  (Blazor Web)   │    │   (Python API)  │                  ││
                    │  │  │                 │    │                 │                  ││
                    │  │  │  Port: 8080     │    │  Port: 8000     │                  ││
                    │  │  └─────────────────┘    └────────┬────────┘                  ││
                    │  │                                  │                            ││
                    │  │                                  ▼                            ││
                    │  │                         ┌─────────────────┐                  ││
                    │  │                         │  PostgreSQL     │                  ││
                    │  │                         │  Flexible Server│                  ││
                    │  │                         └─────────────────┘                  ││
                    │  │                                                              ││
                    │  └──────────────────────────────────────────────────────────────┘│
                    │                                                                   │
                    │  ┌─────────────────┐    ┌─────────────────┐                      │
                    │  │   Key Vault     │    │ Container Reg.  │                      │
                    │  │   (Secrets)     │    │   (Images)      │                      │
                    │  └─────────────────┘    └─────────────────┘                      │
                    │                                                                   │
                    │  ┌─────────────────┐    ┌─────────────────┐                      │
                    │  │  Log Analytics  │    │   App Insights  │                      │
                    │  │   Workspace     │    │   (Monitoring)  │                      │
                    │  └─────────────────┘    └─────────────────┘                      │
                    │                                                                   │
                    └─────────────────────────────────────────────────────────────────┘
```

## Directory Structure

```
infra/
├── terraform/
│   ├── environments/
│   │   ├── dev/
│   │   │   └── terraform.tfvars
│   │   ├── staging/
│   │   │   └── terraform.tfvars
│   │   └── prod/
│   │       └── terraform.tfvars
│   ├── modules/
│   │   ├── container-apps/
│   │   │   ├── main.tf
│   │   │   ├── variables.tf
│   │   │   └── outputs.tf
│   │   ├── container-registry/
│   │   │   ├── main.tf
│   │   │   ├── variables.tf
│   │   │   └── outputs.tf
│   │   ├── database/
│   │   │   ├── main.tf
│   │   │   ├── variables.tf
│   │   │   └── outputs.tf
│   │   ├── keyvault/
│   │   │   ├── main.tf
│   │   │   ├── variables.tf
│   │   │   └── outputs.tf
│   │   └── monitoring/
│   │       ├── main.tf
│   │       ├── variables.tf
│   │       └── outputs.tf
│   ├── main.tf
│   ├── variables.tf
│   ├── outputs.tf
│   ├── providers.tf
│   ├── versions.tf
│   └── backend.tf
└── README.md
```

## Prerequisites

1. **Azure Subscription** with appropriate permissions
2. **Terraform** >= 1.9.0
3. **Azure CLI** installed and logged in
4. **GitHub** repository with Actions enabled

## Quick Start

### 1. Initialize Backend Storage

```bash
# Create storage account for Terraform state
az group create --name rg-homunculy-tfstate --location eastus

az storage account create \
  --name sthomunculytfstate \
  --resource-group rg-homunculy-tfstate \
  --sku Standard_LRS \
  --encryption-services blob

az storage container create \
  --name tfstate \
  --account-name sthomunculytfstate
```

### 2. Configure Variables

Copy the example variables file and configure:

```bash
cd infra/terraform/environments/dev
cp terraform.tfvars.example terraform.tfvars
# Edit terraform.tfvars with your values
```

### 3. Deploy

```bash
cd infra/terraform

# Initialize
terraform init -backend-config=environments/dev/backend.tfvars

# Plan
terraform plan -var-file=environments/dev/terraform.tfvars

# Apply
terraform apply -var-file=environments/dev/terraform.tfvars
```

## Environment Variables

### GitHub Secrets Required

| Secret | Description |
|--------|-------------|
| `AZURE_CLIENT_ID` | Azure Service Principal App ID |
| `AZURE_TENANT_ID` | Azure Tenant ID |
| `AZURE_SUBSCRIPTION_ID` | Azure Subscription ID |
| `OPENAI_API_KEY` | OpenAI API Key |
| `ELEVENLABS_API_KEY` | ElevenLabs API Key |

### Azure Key Vault Secrets

Secrets are stored in Azure Key Vault and injected at runtime:

- `openai-api-key`
- `elevenlabs-api-key`
- `db-password`

## CI/CD Pipeline

GitHub Actions workflows are configured in `.github/workflows/`:

- **`deploy-infra.yml`**: Deploy/update infrastructure
- **`deploy-apps.yml`**: Build and deploy applications
- **`destroy-infra.yml`**: Tear down infrastructure (manual)

## Scaling

Container Apps are configured with automatic scaling:

```hcl
scale {
  min_replicas = 0
  max_replicas = 10
  
  rules {
    name = "http-rule"
    http {
      concurrent_requests = 100
    }
  }
}
```

## Testing

### Unit Tests

```bash
cd infra/terraform
terraform validate
terraform fmt -check
```

### Integration Tests

Use Terratest for integration testing (see `tests/` directory).

## Security

- All secrets stored in Azure Key Vault
- Managed Identities for authentication
- OIDC for GitHub Actions (no stored credentials)
- Private endpoints for databases
- Network segmentation with VNet

## Cost Optimization

- Container Apps use consumption plan (pay-per-use)
- Auto-scaling to zero when idle
- Dev environment uses smaller SKUs
- Shared resources across environments where possible
