# =============================================================================
# VNet Module Variables
# =============================================================================
# Purpose: Define input variables for VNet module
# Following: Clean Code - meaningful names, clear descriptions
# =============================================================================

# -----------------------------------------------------------------------------
# Core Configuration
# -----------------------------------------------------------------------------

variable "resource_group_name" {
  type        = string
  description = "Name of the resource group"
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
# VNet Configuration
# -----------------------------------------------------------------------------

variable "address_space" {
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
# Feature Toggles
# -----------------------------------------------------------------------------

variable "create_bastion_subnet" {
  type        = bool
  description = "Whether to create bastion subnet for private cluster access"
  default     = false
}

variable "create_private_dns_zones" {
  type        = bool
  description = "Whether to create private DNS zones"
  default     = true
}
