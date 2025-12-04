# =============================================================================
# Container Apps Stack Variables
# =============================================================================
# Purpose: Define all input variables for Container Apps infrastructure
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
# Container Apps Configuration
# -----------------------------------------------------------------------------

variable "homunculy_image_tag" {
  type        = string
  description = "Docker image tag for homunculy-app"
  default     = "latest"
}

variable "chat_client_image_tag" {
  type        = string
  description = "Docker image tag for chat-client"
  default     = "latest"
}

variable "homunculy_min_replicas" {
  type        = number
  description = "Minimum replicas for homunculy-app"
  default     = 0
}

variable "homunculy_max_replicas" {
  type        = number
  description = "Maximum replicas for homunculy-app"
  default     = 5
}

variable "chat_client_min_replicas" {
  type        = number
  description = "Minimum replicas for chat-client"
  default     = 0
}

variable "chat_client_max_replicas" {
  type        = number
  description = "Maximum replicas for chat-client"
  default     = 5
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
