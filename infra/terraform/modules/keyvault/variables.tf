# =============================================================================
# Key Vault Module - Variables
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

variable "tenant_id" {
  type        = string
  description = "Azure AD tenant ID"
}

variable "secret_names" {
  type        = list(string)
  description = "List of secret names to create"
  default     = []
}

variable "secret_values" {
  type        = map(string)
  description = "Map of secret names to values (sensitive)"
  sensitive   = true
  default     = {}
}

variable "access_policies" {
  type = list(object({
    object_id               = string
    secret_permissions      = list(string)
    key_permissions         = optional(list(string), [])
    certificate_permissions = optional(list(string), [])
  }))
  description = "Access policies for the Key Vault"
  default     = []
}
