# GitHub Configuration

⚙️ **CI/CD & GitHub Settings** - Workflows, actions, and repository configuration.

## Contents

| Directory/File | Description |
|----------------|-------------|
| `workflows/` | GitHub Actions CI/CD pipelines |
| `CICD_SETUP.md` | Setup guide for CI/CD |

## Workflows

| Workflow | Trigger | Purpose |
|----------|---------|---------|
| `build-images.yml` | Push to main | Build & push Docker images |
| `deploy-apps.yml` | Manual/Release | Deploy apps to Azure |
| `terraform-ci.yml` | PR on infra | Validate Terraform changes |
| `terraform-deploy.yml` | Manual | Deploy infrastructure |

## Quick Reference

```bash
# Trigger deploy manually
gh workflow run deploy-apps.yml

# Check workflow status
gh run list --workflow=build-images.yml
```
