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

variable "public_network_access_enabled" {
  type        = bool
  description = "Whether PostgreSQL Flexible Server public network access is enabled. Set false for private (delegated subnet + private DNS) deployments."
  default     = true
}

variable "create_allow_azure_services_firewall_rule" {
  type        = bool
  description = "Whether to create the firewall rule that allows Azure services (0.0.0.0). Only applies when public network access is enabled."
  default     = true
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
