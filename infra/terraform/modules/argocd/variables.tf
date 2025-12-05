# =============================================================================
# ArgoCD Module - Variables
# =============================================================================

variable "environment" {
  description = "Environment name (dev, staging, prod)"
  type        = string
}

variable "argocd_version" {
  description = "ArgoCD Helm chart version"
  type        = string
  default     = "5.51.6"
}

variable "admin_password" {
  description = "ArgoCD admin password"
  type        = string
  sensitive   = true
}

variable "enable_ingress" {
  description = "Enable ingress for ArgoCD UI"
  type        = bool
  default     = true
}

variable "argocd_hostname" {
  description = "Hostname for ArgoCD UI"
  type        = string
  default     = "argocd.homunculy.io"
}

variable "create_root_app" {
  description = "Create the root ArgoCD Application for GitOps bootstrap"
  type        = bool
  default     = true
}

variable "git_repo_url" {
  description = "Git repository URL for ArgoCD to sync"
  type        = string
  default     = "https://github.com/Jakkapat-Chongsuwat/homunculy.git"
}

variable "git_target_revision" {
  description = "Git branch/tag/commit to sync"
  type        = string
  default     = "main"
}

variable "git_apps_path" {
  description = "Path to Kubernetes manifests in the repo"
  type        = string
  default     = "infra/k8s/overlays/prod"
}
