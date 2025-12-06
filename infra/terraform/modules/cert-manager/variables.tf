# =============================================================================
# Cert-Manager - Variables
# =============================================================================

variable "enabled" {
  description = "Whether to install cert-manager"
  type        = bool
  default     = true
}

variable "chart_version" {
  description = "Helm chart version for cert-manager"
  type        = string
  default     = "v1.14.0"
}

variable "enable_metrics" {
  description = "Enable Prometheus metrics"
  type        = bool
  default     = true
}

variable "create_cluster_issuers" {
  description = "Create Let's Encrypt ClusterIssuers"
  type        = bool
  default     = true
}

variable "letsencrypt_email" {
  description = "Email for Let's Encrypt registration"
  type        = string
}

variable "ingress_class" {
  description = "Ingress class for ACME HTTP01 solver"
  type        = string
  default     = "nginx"
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
