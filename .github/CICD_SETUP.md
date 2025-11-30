# GitHub Actions CI/CD Setup Guide

This guide explains how to set up GitHub Actions for deploying Homunculy to Azure Container Apps.

## Prerequisites

1. **Azure Subscription** with appropriate permissions
2. **Azure CLI** installed locally
3. **GitHub repository** with Actions enabled

## Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                              GitHub Actions                                  │
│                                                                              │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐    ┌────────────┐│
│  │ Terraform CI │───▶│ Build Images │───▶│ Deploy Apps  │───▶│Health Check││
│  │              │    │              │    │              │    │            ││
│  │ • Format     │    │ • Homunculy  │    │ • Update ACA │    │ • Verify   ││
│  │ • Validate   │    │ • Chat Client│    │ • Rollout    │    │ • Notify   ││
│  │ • Test       │    │              │    │              │    │            ││
│  └──────────────┘    └──────────────┘    └──────────────┘    └────────────┘│
│         │                   │                   │                           │
│         ▼                   ▼                   ▼                           │
│  ┌──────────────────────────────────────────────────────────────────────┐  │
│  │                        Terraform Deploy                               │  │
│  │  (Manual trigger for infrastructure changes)                          │  │
│  └──────────────────────────────────────────────────────────────────────┘  │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                              Azure                                           │
│                                                                              │
│  ┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐         │
│  │ Container       │    │ Container Apps  │    │ PostgreSQL      │         │
│  │ Registry (ACR)  │───▶│ Environment     │───▶│ Flexible Server │         │
│  └─────────────────┘    └─────────────────┘    └─────────────────┘         │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

## Step 1: Create Azure Service Principal (OIDC)

Using OIDC (OpenID Connect) is more secure than storing credentials.

```bash
# Login to Azure
az login

# Set subscription
SUBSCRIPTION_ID=$(az account show --query id -o tsv)
echo "Subscription ID: $SUBSCRIPTION_ID"

# Create service principal with federated credentials
az ad app create --display-name "homunculy-github-actions"

# Get the app ID
APP_ID=$(az ad app list --display-name "homunculy-github-actions" --query "[0].appId" -o tsv)
echo "App ID: $APP_ID"

# Create service principal
az ad sp create --id $APP_ID

# Get object ID of the service principal
SP_OBJECT_ID=$(az ad sp show --id $APP_ID --query id -o tsv)
echo "Service Principal Object ID: $SP_OBJECT_ID"

# Assign Contributor role to the subscription
az role assignment create \
  --assignee $SP_OBJECT_ID \
  --role "Contributor" \
  --scope "/subscriptions/$SUBSCRIPTION_ID"

# Get tenant ID
TENANT_ID=$(az account show --query tenantId -o tsv)
echo "Tenant ID: $TENANT_ID"
```

## Step 2: Configure Federated Credentials

```bash
# Replace with your GitHub username/org and repo
GITHUB_ORG="Jakkapat-Chongsuwat"
GITHUB_REPO="homunculy"

# Create federated credential for main branch
az ad app federated-credential create \
  --id $APP_ID \
  --parameters '{
    "name": "github-main",
    "issuer": "https://token.actions.githubusercontent.com",
    "subject": "repo:'$GITHUB_ORG'/'$GITHUB_REPO':ref:refs/heads/main",
    "audiences": ["api://AzureADTokenExchange"]
  }'

# Create federated credential for pull requests
az ad app federated-credential create \
  --id $APP_ID \
  --parameters '{
    "name": "github-pr",
    "issuer": "https://token.actions.githubusercontent.com",
    "subject": "repo:'$GITHUB_ORG'/'$GITHUB_REPO':pull_request",
    "audiences": ["api://AzureADTokenExchange"]
  }'

# Create federated credential for environments (dev, staging, prod)
for ENV in dev staging prod; do
  az ad app federated-credential create \
    --id $APP_ID \
    --parameters '{
      "name": "github-env-'$ENV'",
      "issuer": "https://token.actions.githubusercontent.com",
      "subject": "repo:'$GITHUB_ORG'/'$GITHUB_REPO':environment:'$ENV'",
      "audiences": ["api://AzureADTokenExchange"]
    }'
done
```

## Step 3: Create Terraform State Storage

```bash
# Create resource group for Terraform state
az group create --name rg-homunculy-tfstate --location eastus

# Create storage account (name must be globally unique)
STORAGE_ACCOUNT="sthomunculytfstate"
az storage account create \
  --name $STORAGE_ACCOUNT \
  --resource-group rg-homunculy-tfstate \
  --sku Standard_LRS \
  --encryption-services blob

# Create container for state files
az storage container create \
  --name tfstate \
  --account-name $STORAGE_ACCOUNT

# Grant Storage Blob Data Contributor to service principal
az role assignment create \
  --assignee $SP_OBJECT_ID \
  --role "Storage Blob Data Contributor" \
  --scope "/subscriptions/$SUBSCRIPTION_ID/resourceGroups/rg-homunculy-tfstate"
```

## Step 4: Configure GitHub Secrets

Go to your GitHub repository → Settings → Secrets and variables → Actions

Add the following **Repository Secrets**:

| Secret Name | Value | Description |
|-------------|-------|-------------|
| `AZURE_CLIENT_ID` | `$APP_ID` from Step 1 | Azure AD Application ID |
| `AZURE_TENANT_ID` | `$TENANT_ID` from Step 1 | Azure AD Tenant ID |
| `AZURE_SUBSCRIPTION_ID` | `$SUBSCRIPTION_ID` from Step 1 | Azure Subscription ID |
| `OPENAI_API_KEY` | Your OpenAI key | For LLM integration |
| `ELEVENLABS_API_KEY` | Your ElevenLabs key | For TTS integration |

## Step 5: Create GitHub Environments

Go to your GitHub repository → Settings → Environments

Create the following environments:

### `dev`
- No protection rules (auto-deploy)

### `staging`
- Required reviewers: Add yourself or team members
- Wait timer: 0 minutes

### `prod`
- Required reviewers: Add 2+ team members
- Wait timer: 15 minutes
- Deployment branches: Only `main`

### `prod-destroy` (for safety)
- Required reviewers: Add 2+ team members
- This prevents accidental infrastructure destruction

## Step 6: Verify Setup

```bash
# Print summary
echo "==========================================="
echo "GitHub Actions Setup Complete!"
echo "==========================================="
echo ""
echo "Add these secrets to GitHub:"
echo "  AZURE_CLIENT_ID: $APP_ID"
echo "  AZURE_TENANT_ID: $TENANT_ID"
echo "  AZURE_SUBSCRIPTION_ID: $SUBSCRIPTION_ID"
echo ""
echo "Terraform state storage:"
echo "  Resource Group: rg-homunculy-tfstate"
echo "  Storage Account: $STORAGE_ACCOUNT"
echo "  Container: tfstate"
echo ""
echo "==========================================="
```

## Workflow Triggers

| Workflow | Trigger | Purpose |
|----------|---------|---------|
| `terraform-ci.yml` | PR/Push to `infra/terraform/**` | Validate & test Terraform |
| `terraform-deploy.yml` | Manual dispatch | Deploy infrastructure |
| `build-images.yml` | Push to `homunculy/**` or `chat-client/**` | Build Docker images |
| `deploy-apps.yml` | After image build or manual | Deploy to Container Apps |

## Usage Examples

### Deploy Infrastructure (First Time)

1. Go to Actions → Terraform Deploy
2. Click "Run workflow"
3. Select environment: `dev`
4. Select action: `plan`
5. Review the plan in the workflow summary
6. Run again with action: `apply`

### Deploy Application Updates

Application deployments happen automatically:
1. Push code to `homunculy/` or `chat-client/`
2. `build-images.yml` builds and pushes to ACR
3. `deploy-apps.yml` updates Container Apps

### Manual Deployment

1. Go to Actions → Deploy Apps
2. Click "Run workflow"
3. Select environment and service
4. Optionally specify an image tag

## Troubleshooting

### OIDC Authentication Fails

```bash
# Verify federated credentials
az ad app federated-credential list --id $APP_ID
```

### Terraform State Lock

```bash
# Force unlock (use with caution)
terraform force-unlock <LOCK_ID>
```

### Container App Not Starting

```bash
# Check logs
az containerapp logs show \
  --name ca-homunculy-dev \
  --resource-group rg-homunculy-dev \
  --follow
```
