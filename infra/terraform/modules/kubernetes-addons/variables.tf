# =============================================================================
# Kubernetes Add-ons Module Variables
# =============================================================================
# Purpose: Define input variables for Kubernetes add-ons
# Following: Clean Code - meaningful names, clear descriptions
# =============================================================================

# -----------------------------------------------------------------------------
# NGINX Ingress Configuration
# -----------------------------------------------------------------------------

variable "install_nginx_ingress" {
  type        = bool
  description = "Whether to install NGINX Ingress Controller"
  default     = false
}

variable "nginx_ingress_version" {
  type        = string
  description = "Version of NGINX Ingress Controller Helm chart"
  default     = "4.9.0"
}

variable "nginx_ingress_replica_count" {
  type        = number
  description = "Number of NGINX Ingress Controller replicas"
  default     = 2
}

variable "nginx_ingress_internal_only" {
  type        = bool
  description = "Whether to create internal-only load balancer"
  default     = false
}

variable "nginx_ingress_values" {
  type        = string
  description = "Additional Helm values for NGINX Ingress"
  default     = ""
}

# -----------------------------------------------------------------------------
# Cert-Manager Configuration
# -----------------------------------------------------------------------------

variable "install_cert_manager" {
  type        = bool
  description = "Whether to install cert-manager"
  default     = false
}

variable "cert_manager_version" {
  type        = string
  description = "Version of cert-manager Helm chart"
  default     = "v1.14.0"
}

variable "create_cluster_issuers" {
  type        = bool
  description = "Whether to create Let's Encrypt ClusterIssuers"
  default     = true
}

variable "letsencrypt_email" {
  type        = string
  description = "Email for Let's Encrypt registration"
  default     = ""
}

# -----------------------------------------------------------------------------
# External DNS Configuration
# -----------------------------------------------------------------------------

variable "install_external_dns" {
  type        = bool
  description = "Whether to install external-dns"
  default     = false
}

variable "external_dns_version" {
  type        = string
  description = "Version of external-dns Helm chart"
  default     = "1.14.0"
}

variable "dns_resource_group" {
  type        = string
  description = "Resource group containing DNS zone"
  default     = ""
}

variable "azure_tenant_id" {
  type        = string
  description = "Azure tenant ID"
  default     = ""
}

variable "azure_subscription_id" {
  type        = string
  description = "Azure subscription ID"
  default     = ""
}

variable "domain_filter" {
  type        = string
  description = "Domain to manage with external-dns"
  default     = ""
}

variable "external_dns_txt_owner_id" {
  type        = string
  description = "TXT record owner ID for external-dns"
  default     = "homunculy"
}
