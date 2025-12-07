# =============================================================================
# AKS Stack Variables
# =============================================================================
# Purpose: Define all input variables for AKS infrastructure
# Following: Clean Code - meaningful names, clear descriptions
# =============================================================================

# -----------------------------------------------------------------------------
# Core Configuration
# -----------------------------------------------------------------------------

variable "subscription_id" {
  type        = string
  description = "Azure subscription ID for deployment"
  default     = ""
}

variable "tenant_id" {
  type        = string
  description = "Azure tenant ID override (optional). Defaults to credentials' tenant."
  default     = ""
}

variable "github_actions_app_id" {
  type        = string
  description = "Existing GitHub Actions OIDC application (client) ID. Leave empty to let Terraform create one."
  default     = ""
}

variable "github_actions_app_display_name" {
  type        = string
  description = "Display name for the GitHub Actions OIDC app registration when created by Terraform."
  default     = "github-actions-homunculy-oidc"
}

variable "github_repo_owner" {
  type        = string
  description = "GitHub organization or user that owns the repository."
  default     = "Jakkapat-Chongsuwat"
}

variable "github_repo_name" {
  type        = string
  description = "GitHub repository name for federated credential subject."
  default     = "homunculy"
}

variable "github_branch" {
  type        = string
  description = "Branch to authorize for OIDC (refs/heads/<branch>)."
  default     = "main"
}

variable "github_oidc_audience" {
  type        = string
  description = "OIDC audience for GitHub Actions federated credential."
  default     = "api://AzureADTokenExchange"
}

variable "manage_github_federated_identity" {
  type        = bool
  description = "Whether to create the GitHub Actions federated identity credential (set false if it already exists)."
  default     = true
}

variable "enable_acr_pull" {
  type        = bool
  description = "Enable ACR pull role assignment for AKS"
  default     = true
}

variable "enable_keyvault_access" {
  type        = bool
  description = "Enable Key Vault secrets user role assignment for AKS"
  default     = true
}

variable "environment" {
  type        = string
  description = "Environment name (dev, staging, prod)"

  validation {
    condition     = contains(["dev", "staging", "prod"], var.environment)
    error_message = "Environment must be one of: dev, staging, prod"
  }
}

variable "location" {
  type        = string
  description = "Azure region for resource deployment"
  default     = "eastus"
}

variable "project_name" {
  type        = string
  description = "Project name used for resource naming"
  default     = "homunculy"
}

variable "tags" {
  type        = map(string)
  description = "Common tags applied to all resources"
  default     = {}
}

# -----------------------------------------------------------------------------
# AKS Cluster Configuration
# -----------------------------------------------------------------------------

variable "kubernetes_version" {
  type        = string
  description = "Kubernetes version for AKS cluster"
  default     = "1.29"
}

variable "aks_sku_tier" {
  type        = string
  description = "AKS SKU tier (Free, Standard, Premium)"
  default     = "Free"

  validation {
    condition     = contains(["Free", "Standard", "Premium"], var.aks_sku_tier)
    error_message = "AKS SKU tier must be one of: Free, Standard, Premium"
  }
}

variable "aks_automatic_upgrade" {
  type        = string
  description = "Automatic upgrade channel (none, patch, rapid, stable, node-image)"
  default     = "patch"
}

variable "node_os_upgrade_channel" {
  type        = string
  description = "Node OS upgrade channel (None, Unmanaged, SecurityPatch, NodeImage)"
  default     = "NodeImage"
}

# -----------------------------------------------------------------------------
# Node Pool Configuration
# -----------------------------------------------------------------------------

variable "system_node_pool_vm_size" {
  type        = string
  description = "VM size for system node pool"
  default     = "Standard_B2s"
}

variable "system_node_pool_node_count" {
  type        = number
  description = "Initial node count for system node pool"
  default     = 1
}

variable "system_node_pool_min_count" {
  type        = number
  description = "Minimum node count for system node pool autoscaling"
  default     = 1
}

variable "system_node_pool_max_count" {
  type        = number
  description = "Maximum node count for system node pool autoscaling"
  default     = 3
}

# -----------------------------------------------------------------------------
# Networking Configuration
# -----------------------------------------------------------------------------

variable "network_plugin" {
  type        = string
  description = "Network plugin for AKS (azure, kubenet, none)"
  default     = "azure"
}

variable "network_policy" {
  type        = string
  description = "Network policy for AKS (azure, calico, cilium)"
  default     = "azure"
}

variable "dns_service_ip" {
  type        = string
  description = "DNS service IP address"
  default     = "10.0.0.10"
}

variable "service_cidr" {
  type        = string
  description = "Service CIDR for Kubernetes services"
  default     = "10.0.0.0/16"
}

variable "load_balancer_sku" {
  type        = string
  description = "Load balancer SKU (basic, standard)"
  default     = "standard"
}

# -----------------------------------------------------------------------------
# Database Configuration
# -----------------------------------------------------------------------------

variable "db_sku_name" {
  type        = string
  description = "PostgreSQL Flexible Server SKU"
  default     = "B_Standard_B1ms"
}

variable "db_storage_mb" {
  type        = number
  description = "PostgreSQL storage size in MB"
  default     = 32768
}

variable "db_backup_retention_days" {
  type        = number
  description = "Database backup retention in days"
  default     = 7
}

# -----------------------------------------------------------------------------
# Secret Configuration (provided at runtime)
# -----------------------------------------------------------------------------

variable "openai_api_key" {
  type        = string
  description = "OpenAI API key for LLM integration"
  sensitive   = true
  default     = ""
}

variable "elevenlabs_api_key" {
  type        = string
  description = "ElevenLabs API key for TTS"
  sensitive   = true
  default     = ""
}

# -----------------------------------------------------------------------------
# Production Security Features
# -----------------------------------------------------------------------------

variable "enable_vnet_integration" {
  type        = bool
  description = "Enable VNet integration with dedicated subnets"
  default     = false
}

variable "private_cluster_enabled" {
  type        = bool
  description = "Enable private cluster (API server not publicly accessible)"
  default     = false
}

variable "azure_policy_enabled" {
  type        = bool
  description = "Enable Azure Policy addon for pod security and compliance"
  default     = false
}

variable "microsoft_defender_enabled" {
  type        = bool
  description = "Enable Microsoft Defender for Containers"
  default     = false
}

# -----------------------------------------------------------------------------
# VNet Configuration
# -----------------------------------------------------------------------------

variable "vnet_address_space" {
  type        = list(string)
  description = "Address space for the virtual network"
  default     = ["10.0.0.0/8"]
}

variable "aks_subnet_address_prefix" {
  type        = list(string)
  description = "Address prefix for AKS subnet"
  default     = ["10.1.0.0/16"]
}

variable "database_subnet_address_prefix" {
  type        = list(string)
  description = "Address prefix for database subnet"
  default     = ["10.2.0.0/24"]
}

variable "private_endpoints_subnet_address_prefix" {
  type        = list(string)
  description = "Address prefix for private endpoints subnet"
  default     = ["10.3.0.0/24"]
}

variable "bastion_subnet_address_prefix" {
  type        = list(string)
  description = "Address prefix for bastion subnet"
  default     = ["10.4.0.0/24"]
}

# -----------------------------------------------------------------------------
# User Node Pool Configuration
# -----------------------------------------------------------------------------

variable "create_user_node_pool" {
  type        = bool
  description = "Whether to create a user node pool for workloads"
  default     = false
}

variable "user_node_pool_vm_size" {
  type        = string
  description = "VM size for user node pool"
  default     = "Standard_B2s"
}

variable "user_node_pool_node_count" {
  type        = number
  description = "Initial node count for user node pool"
  default     = 1
}

variable "user_node_pool_min_count" {
  type        = number
  description = "Minimum node count for user node pool"
  default     = 0
}

variable "user_node_pool_max_count" {
  type        = number
  description = "Maximum node count for user node pool"
  default     = 5
}

# -----------------------------------------------------------------------------
# Kubernetes Add-ons
# -----------------------------------------------------------------------------

# =============================================================================
# Option 1: Azure Application Routing (RECOMMENDED - Managed NGINX)
# =============================================================================
# Use this for single `terraform apply` experience
# No bastion, no helm, no SSH - fully managed by Azure
# =============================================================================

variable "enable_app_routing" {
  type        = bool
  description = "Enable Azure Application Routing add-on (managed NGINX ingress). RECOMMENDED for single terraform apply experience."
  default     = true
}

variable "app_routing_dns_zone_ids" {
  type        = list(string)
  description = "List of Azure DNS zone IDs for automatic DNS management with App Routing"
  default     = []
}

# -----------------------------------------------------------------------------
# Velero Backup Configuration
# -----------------------------------------------------------------------------

variable "install_velero" {
  type        = bool
  description = "Whether to install Velero for backup"
  default     = false
}

variable "velero_backup_schedule" {
  type        = string
  description = "Cron schedule for automatic backups"
  default     = "0 2 * * *"
}

variable "velero_backup_retention_days" {
  type        = number
  description = "Number of days to retain backups"
  default     = 30
}

# -----------------------------------------------------------------------------
# ArgoCD Configuration
# -----------------------------------------------------------------------------

variable "install_argocd" {
  type        = bool
  description = "Whether to install ArgoCD for GitOps"
  default     = true
}

variable "argocd_version" {
  type        = string
  description = "ArgoCD Helm chart version"
  default     = "5.51.6"
}

variable "argocd_admin_password" {
  type        = string
  description = "ArgoCD admin password"
  sensitive   = true
  default     = ""
}

variable "argocd_enable_ingress" {
  type        = bool
  description = "Enable ingress for ArgoCD UI"
  default     = true
}

variable "argocd_hostname" {
  type        = string
  description = "Hostname for ArgoCD UI"
  default     = "argocd.homunculy.io"
}

variable "argocd_create_root_app" {
  type        = bool
  description = "Create the root ArgoCD Application for GitOps bootstrap"
  default     = true
}

variable "argocd_git_repo_url" {
  type        = string
  description = "Git repository URL for ArgoCD to sync"
  default     = "https://github.com/Jakkapat-Chongsuwat/homunculy.git"
}

variable "argocd_git_target_revision" {
  type        = string
  description = "Git branch/tag/commit to sync"
  default     = "main"
}

variable "argocd_git_apps_path" {
  type        = string
  description = "Path to Kubernetes manifests in the repo"
  default     = "infra/k8s/overlays/prod"
}
