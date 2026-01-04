# =============================================================================
# Container Registry Module - Variables
# =============================================================================

variable "resource_group_name" {
  type        = string
  description = "Name of the resource group"
}

variable "location" {
  type        = string
  description = "Azure region for deployment"
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

variable "sku" {
  type        = string
  description = "Container Registry SKU"
  default     = "Basic"

  validation {
    condition     = contains(["Basic", "Standard", "Premium"], var.sku)
    error_message = "SKU must be Basic, Standard, or Premium"
  }
}

variable "admin_enabled" {
  type        = bool
  description = "Enable admin user for the registry"
  default     = false
}