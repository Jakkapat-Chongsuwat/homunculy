# =============================================================================
# Database Module - Variables
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

variable "sku_name" {
  type        = string
  description = "PostgreSQL Flexible Server SKU"
  default     = "B_Standard_B1ms"
}

variable "storage_mb" {
  type        = number
  description = "Storage size in MB"
  default     = 32768
}

variable "backup_retention_days" {
  type        = number
  description = "Backup retention in days"
  default     = 7
}

variable "database_name" {
  type        = string
  description = "Name of the database to create"
  default     = "homunculy"
}

variable "admin_password" {
  type        = string
  description = "Admin password for PostgreSQL"
  sensitive   = true
}

variable "delegated_subnet_id" {
  type        = string
  description = "ID of the subnet delegated for PostgreSQL Flexible Server"
  default     = null
}

variable "private_dns_zone_id" {
  type        = string
  description = "ID of the private DNS zone for PostgreSQL"
  default     = null
}

variable "allowed_subnet_id" {
  type        = string
  description = "Subnet ID allowed to access the database"
  default     = null
}
