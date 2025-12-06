# =============================================================================
# NGINX Ingress Controller - Variables
# =============================================================================

variable "enabled" {
  description = "Whether to install NGINX Ingress Controller"
  type        = bool
  default     = true
}

variable "chart_version" {
  description = "Helm chart version for ingress-nginx"
  type        = string
  default     = "4.9.0"
}

variable "replica_count" {
  description = "Number of NGINX Ingress Controller replicas"
  type        = number
  default     = 2
}

variable "internal_only" {
  description = "Create internal-only Azure Load Balancer (no public IP)"
  type        = bool
  default     = false
}

variable "enable_metrics" {
  description = "Enable Prometheus metrics endpoint"
  type        = bool
  default     = true
}

# =============================================================================
# Private Cluster Support
# =============================================================================

variable "use_command_invoke" {
  description = "Use az aks command invoke for private clusters"
  type        = bool
  default     = false
}

variable "resource_group_name" {
  description = "Azure Resource Group name (required for private cluster)"
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
