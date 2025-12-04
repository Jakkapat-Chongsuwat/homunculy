# =============================================================================
# Velero Backup Module Variables
# =============================================================================
# Purpose: Define input variables for Velero module
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

variable "subscription_id" {
  type        = string
  description = "Azure subscription ID"
}

# -----------------------------------------------------------------------------
# AKS Integration
# -----------------------------------------------------------------------------

variable "oidc_issuer_url" {
  type        = string
  description = "OIDC issuer URL from AKS cluster"
}

# -----------------------------------------------------------------------------
# Storage Configuration
# -----------------------------------------------------------------------------

variable "create_storage_account" {
  type        = bool
  description = "Whether to create storage account for backups"
  default     = true
}

variable "storage_account_name" {
  type        = string
  description = "Existing storage account name (if not creating)"
  default     = ""
}

variable "storage_container_name" {
  type        = string
  description = "Existing storage container name (if not creating)"
  default     = "velero"
}

variable "storage_replication_type" {
  type        = string
  description = "Storage account replication type"
  default     = "GRS"
}

# -----------------------------------------------------------------------------
# Velero Configuration
# -----------------------------------------------------------------------------

variable "install_velero" {
  type        = bool
  description = "Whether to install Velero"
  default     = true
}

variable "velero_version" {
  type        = string
  description = "Velero Helm chart version"
  default     = "5.2.0"
}

variable "velero_azure_plugin_version" {
  type        = string
  description = "Velero Azure plugin version"
  default     = "v1.9.0"
}

# -----------------------------------------------------------------------------
# Backup Configuration
# -----------------------------------------------------------------------------

variable "backup_schedule" {
  type        = string
  description = "Cron schedule for automatic backups"
  default     = "0 2 * * *" # 2 AM daily
}

variable "backup_retention_days" {
  type        = number
  description = "Number of days to retain backups"
  default     = 30
}
