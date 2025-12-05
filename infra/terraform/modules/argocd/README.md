# ArgoCD Module

GitOps deployment controller for Kubernetes using ArgoCD.

## Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                          ArgoCD GitOps Flow                                 │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│   ┌─────────────────┐                         ┌─────────────────────────┐   │
│   │                 │    1. Developer pushes  │                         │   │
│   │   Developer     │ ────────────────────►   │   GitHub Repository     │   │
│   │                 │                         │   (K8s manifests)       │   │
│   └─────────────────┘                         └───────────┬─────────────┘   │
│                                                           │                 │
│                                               2. ArgoCD monitors repo       │
│                                                           │                 │
│                                                           ▼                 │
│   ┌─────────────────────────────────────────────────────────────────────┐   │
│   │                        AKS Cluster                                  │   │
│   │                                                                     │   │
│   │   ┌─────────────────────────────────────────────────────────────┐   │   │
│   │   │                   ArgoCD Namespace                          │   │   │
│   │   │                                                             │   │   │
│   │   │  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐       │   │   │
│   │   │  │              │  │              │  │              │       │   │   │
│   │   │  │  API Server  │  │ Repo Server  │  │ Controller   │       │   │   │
│   │   │  │              │  │              │  │              │       │   │   │
│   │   │  └──────────────┘  └──────────────┘  └──────┬───────┘       │   │   │
│   │   │                                             │               │   │   │
│   │   └─────────────────────────────────────────────┼───────────────┘   │   │
│   │                                                 │                   │   │
│   │                               3. Syncs K8s manifests                │   │
│   │                                                 │                   │   │
│   │                                                 ▼                   │   │
│   │   ┌─────────────────────────────────────────────────────────────┐   │   │
│   │   │                   Application Namespaces                    │   │   │
│   │   │                                                             │   │   │
│   │   │  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────┐  │   │   │
│   │   │  │ homunculy   │  │ rag-service │  │ management-service  │  │   │   │
│   │   │  │ (AI Chat)   │  │ (RAG API)   │  │ (User/Waifu mgmt)   │  │   │   │
│   │   │  └─────────────┘  └─────────────┘  └─────────────────────┘  │   │   │
│   │   │                                                             │   │   │
│   │   └─────────────────────────────────────────────────────────────┘   │   │
│   │                                                                     │   │
│   └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

## Usage

```hcl
module "argocd" {
  source = "./modules/argocd"

  environment    = "prod"
  admin_password = var.argocd_admin_password

  # Ingress configuration
  enable_ingress  = true
  argocd_hostname = "argocd.homunculy.io"

  # GitOps repository
  git_repo_url        = "https://github.com/Jakkapat-Chongsuwat/homunculy.git"
  git_target_revision = "main"
  git_apps_path       = "infra/k8s/overlays/prod"
}
```

## Inputs

| Name | Description | Type | Default | Required |
|------|-------------|------|---------|:--------:|
| `environment` | Environment name (dev, staging, prod) | `string` | - | ✅ |
| `admin_password` | ArgoCD admin password | `string` | - | ✅ |
| `argocd_version` | ArgoCD Helm chart version | `string` | `"5.51.6"` | ❌ |
| `enable_ingress` | Enable ingress for ArgoCD UI | `bool` | `true` | ❌ |
| `argocd_hostname` | Hostname for ArgoCD UI | `string` | `"argocd.homunculy.io"` | ❌ |
| `create_root_app` | Create root ArgoCD Application | `bool` | `true` | ❌ |
| `git_repo_url` | Git repository URL for syncing | `string` | `"https://github.com/..."` | ❌ |
| `git_target_revision` | Git branch/tag/commit to sync | `string` | `"main"` | ❌ |
| `git_apps_path` | Path to K8s manifests in repo | `string` | `"infra/k8s/overlays/prod"` | ❌ |

## Outputs

| Name | Description |
|------|-------------|
| `argocd_namespace` | Namespace where ArgoCD is installed |
| `argocd_url` | URL to access ArgoCD UI |

## Environment-Specific Configuration

```
┌─────────────────────────────────────────────────────────────────┐
│                    Dev Environment                              │
├─────────────────────────────────────────────────────────────────┤
│  - Server replicas: 1                                           │
│  - Repo server replicas: 1                                      │
│  - Log level: debug                                             │
│  - Lower resource limits                                        │
└─────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│                   Prod Environment                              │
├─────────────────────────────────────────────────────────────────┤
│  - Server replicas: 2 (HA)                                      │
│  - Repo server replicas: 2 (HA)                                 │
│  - Log level: info                                              │
│  - Higher resource limits                                       │
└─────────────────────────────────────────────────────────────────┘
```

## Components Installed

| Component | Description |
|-----------|-------------|
| **API Server** | Serves the ArgoCD UI and REST/gRPC API |
| **Repo Server** | Clones Git repos and generates K8s manifests |
| **Application Controller** | Monitors apps and syncs with Git |
| **Redis** | Caches Git repo data |

## Security

- Admin password is bcrypt hashed before storage
- RBAC configured with readonly default policy
- SSO (Dex) disabled by default
- Insecure mode enabled (use ingress TLS termination instead)

## Sync Policy

The root application is configured with:
- **Automated Sync**: Automatically syncs when Git changes detected
- **Self-Heal**: Reverts manual changes to match Git state
- **Prune**: Deletes resources removed from Git
- **CreateNamespace**: Creates namespaces as needed
