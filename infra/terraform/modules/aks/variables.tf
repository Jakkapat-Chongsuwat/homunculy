# =============================================================================
# AKS Module Variables
# =============================================================================
# Purpose: Define input variables for AKS module
# Following: Clean Code - meaningful names, clear descriptions
# =============================================================================

# -----------------------------------------------------------------------------
# Core Configuration
# -----------------------------------------------------------------------------

variable "resource_group_name" {
  type        = string
  description = "Name of the resource group"
}

variable "resource_group_id" {
  type        = string
  description = "ID of the resource group"
}

variable "location" {
  type        = string
  description = "Azure region for resources"
}

variable "project_name" {
  type        = string
  description = "Project name for resource naming"
}

variable "environment" {
  type        = string
  description = "Environment name (dev, staging, prod)"
}

variable "tags" {
  type        = map(string)
  description = "Tags to apply to resources"
  default     = {}
}

# -----------------------------------------------------------------------------
# Cluster Configuration
# -----------------------------------------------------------------------------

variable "kubernetes_version" {
  type        = string
  description = "Kubernetes version"
  default     = "1.29"
}

variable "sku_tier" {
  type        = string
  description = "AKS SKU tier (Free, Standard, Premium)"
  default     = "Free"
}

variable "automatic_upgrade" {
  type        = string
  description = "Automatic upgrade channel"
  default     = "patch"
}

variable "node_os_upgrade_channel" {
  type        = string
  description = "Node OS upgrade channel"
  default     = "NodeImage"
}

# -----------------------------------------------------------------------------
# System Node Pool
# -----------------------------------------------------------------------------

variable "system_node_pool_vm_size" {
  type        = string
  description = "VM size for system node pool"
  default     = "Standard_B2s"
}

variable "system_node_pool_node_count" {
  type        = number
  description = "Initial node count for system pool"
  default     = 1
}

variable "system_node_pool_min_count" {
  type        = number
  description = "Minimum nodes for system pool"
  default     = 1
}

variable "system_node_pool_max_count" {
  type        = number
  description = "Maximum nodes for system pool"
  default     = 3
}

# -----------------------------------------------------------------------------
# User Node Pool (optional)
# -----------------------------------------------------------------------------

variable "create_user_node_pool" {
  type        = bool
  description = "Whether to create a user node pool"
  default     = false
}

variable "user_node_pool_vm_size" {
  type        = string
  description = "VM size for user node pool"
  default     = "Standard_B2s"
}

variable "user_node_pool_node_count" {
  type        = number
  description = "Initial node count for user pool"
  default     = 1
}

variable "user_node_pool_min_count" {
  type        = number
  description = "Minimum nodes for user pool"
  default     = 0
}

variable "user_node_pool_max_count" {
  type        = number
  description = "Maximum nodes for user pool"
  default     = 5
}

# -----------------------------------------------------------------------------
# Network Configuration
# -----------------------------------------------------------------------------

variable "network_plugin" {
  type        = string
  description = "Network plugin (azure, kubenet)"
  default     = "azure"
}

variable "network_policy" {
  type        = string
  description = "Network policy (azure, calico)"
  default     = "azure"
}

variable "dns_service_ip" {
  type        = string
  description = "DNS service IP"
  default     = "10.0.0.10"
}

variable "service_cidr" {
  type        = string
  description = "Service CIDR"
  default     = "10.0.0.0/16"
}

variable "load_balancer_sku" {
  type        = string
  description = "Load balancer SKU"
  default     = "standard"
}

# -----------------------------------------------------------------------------
# Integrations
# -----------------------------------------------------------------------------

variable "log_analytics_workspace_id" {
  type        = string
  description = "Log Analytics workspace ID for monitoring"
}

variable "container_registry_id" {
  type        = string
  description = "Container Registry ID for ACR pull access"
  default     = null
  nullable    = true
}

variable "enable_acr_pull" {
  type        = bool
  description = "Enable ACR pull role assignment (set to true when container_registry_id is provided)"
  default     = false
}

variable "keyvault_id" {
  type        = string
  description = "Key Vault ID for secrets access"
  default     = null
  nullable    = true
}

variable "enable_keyvault_access" {
  type        = bool
  description = "Enable Key Vault secrets user role assignment (set to true when keyvault_id is provided)"
  default     = false
}

# -----------------------------------------------------------------------------
# Production Security Features
# -----------------------------------------------------------------------------

variable "private_cluster_enabled" {
  type        = bool
  description = "Enable private cluster (API server not publicly accessible)"
  default     = false
}

variable "private_dns_zone_id" {
  type        = string
  description = "Private DNS zone ID for private cluster"
  default     = null
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

variable "aks_subnet_id" {
  type        = string
  description = "Subnet ID for AKS nodes (for VNet integration)"
  default     = null
}

# -----------------------------------------------------------------------------
# Application Routing Add-on (Managed NGINX Ingress)
# -----------------------------------------------------------------------------

variable "enable_app_routing" {
  type        = bool
  description = "Enable Azure Application Routing add-on (managed NGINX ingress)"
  default     = false
}

variable "app_routing_dns_zone_ids" {
  type        = list(string)
  description = "List of Azure DNS zone IDs for automatic DNS management"
  default     = []
}
