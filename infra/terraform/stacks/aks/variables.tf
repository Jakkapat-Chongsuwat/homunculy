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
