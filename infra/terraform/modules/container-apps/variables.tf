# =============================================================================
# Container Apps Module - Variables
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

# Log Analytics
variable "log_analytics_workspace_id" {
  type        = string
  description = "ID of the Log Analytics workspace"
}

# Container Registry
variable "container_registry_login_server" {
  type        = string
  description = "Login server for the container registry"
}

variable "container_registry_admin_username" {
  type        = string
  description = "Admin username for the container registry"
  sensitive   = true
}

variable "container_registry_admin_password" {
  type        = string
  description = "Admin password for the container registry"
  sensitive   = true
}

# Homunculy App Configuration
variable "homunculy_image_tag" {
  type        = string
  description = "Docker image tag for homunculy-app"
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

variable "homunculy_cpu" {
  type        = number
  description = "CPU cores for homunculy-app"
  default     = 0.5
}

variable "homunculy_memory" {
  type        = string
  description = "Memory for homunculy-app"
  default     = "1Gi"
}

# Chat Client Configuration
variable "chat_client_image_tag" {
  type        = string
  description = "Docker image tag for chat-client"
  default     = "latest"
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

variable "chat_client_cpu" {
  type        = number
  description = "CPU cores for chat-client"
  default     = 0.25
}

variable "chat_client_memory" {
  type        = string
  description = "Memory for chat-client"
  default     = "0.5Gi"
}

# Database Configuration
variable "database_host" {
  type        = string
  description = "PostgreSQL server hostname"
}

variable "database_name" {
  type        = string
  description = "PostgreSQL database name"
}

variable "database_username" {
  type        = string
  description = "PostgreSQL username"
  sensitive   = true
}

variable "database_password" {
  type        = string
  description = "PostgreSQL password"
  sensitive   = true
}

# Secrets
variable "openai_api_key" {
  type        = string
  description = "OpenAI API key"
  sensitive   = true
}

variable "elevenlabs_api_key" {
  type        = string
  description = "ElevenLabs API key"
  sensitive   = true
}

# Application Insights
variable "application_insights_connection_string" {
  type        = string
  description = "Application Insights connection string"
  sensitive   = true
  default     = ""
}
