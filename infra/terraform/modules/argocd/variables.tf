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

# =============================================================================
# AKS Extension Configuration
# =============================================================================

variable "resource_group_name" {
  description = "Azure Resource Group name (required for private cluster)"
  type        = string
  default     = ""
}

variable "workload_identity_client_id" {
  description = "Managed identity client ID for ArgoCD workloads (enables Azure workload identity). Leave empty to skip."
  type        = string
  default     = ""
}

variable "workload_identity_sso_client_id" {
  description = "Managed identity client ID for ArgoCD UI SSO (optional). Leave empty to skip."
  type        = string
  default     = ""
}

variable "aks_cluster_name" {
  description = "AKS cluster name (required for private cluster)"
  type        = string
  default     = ""
}

variable "aks_cluster_id" {
  description = "AKS cluster resource ID (used for trigger)"
  type        = string
  default     = ""
}

variable "argocd_manifest_url" {
  description = "Argo CD manifest URL to apply (defaults to stable install.yaml)"
  type        = string
  default     = ""
}

variable "public_ip" {
  description = "Public IP address for nip.io ingress (optional, for public access)"
  type        = string
  default     = ""
}
