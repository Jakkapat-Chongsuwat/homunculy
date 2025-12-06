# =============================================================================
# External-DNS - Variables
# =============================================================================

variable "enabled" {
  description = "Whether to install external-dns"
  type        = bool
  default     = true
}

variable "chart_version" {
  description = "Helm chart version for external-dns"
  type        = string
  default     = "1.14.0"
}

# -----------------------------------------------------------------------------
# Azure Configuration
# -----------------------------------------------------------------------------

variable "dns_resource_group" {
  description = "Resource group containing Azure DNS zone"
  type        = string
}

variable "azure_tenant_id" {
  description = "Azure tenant ID"
  type        = string
}

variable "azure_subscription_id" {
  description = "Azure subscription ID"
  type        = string
}

# -----------------------------------------------------------------------------
# DNS Configuration
# -----------------------------------------------------------------------------

variable "domain_filters" {
  description = "List of domains to manage"
  type        = list(string)
  default     = []
}

variable "txt_owner_id" {
  description = "TXT record owner ID for external-dns"
  type        = string
  default     = "homunculy"
}

variable "sync_policy" {
  description = "DNS record sync policy (sync or upsert-only)"
  type        = string
  default     = "sync"
}

variable "sources" {
  description = "Kubernetes resources to watch for DNS records"
  type        = list(string)
  default     = ["ingress", "service"]
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
