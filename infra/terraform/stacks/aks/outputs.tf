# =============================================================================
# AKS Stack Outputs
# =============================================================================
# Purpose: Export key resource information for downstream consumers
# Following: Clean Code - meaningful outputs, clear descriptions
# =============================================================================

# -----------------------------------------------------------------------------
# AKS Cluster
# -----------------------------------------------------------------------------

output "aks_cluster_id" {
  description = "ID of the AKS cluster"
  value       = module.aks.cluster_id
}

output "aks_cluster_name" {
  description = "Name of the AKS cluster"
  value       = module.aks.cluster_name
}

output "aks_cluster_fqdn" {
  description = "FQDN of the AKS cluster"
  value       = module.aks.cluster_fqdn
}

output "aks_kube_config" {
  description = "Kubeconfig for AKS cluster"
  value       = module.aks.kube_config
  sensitive   = true
}

output "aks_kube_config_raw" {
  description = "Raw kubeconfig for AKS cluster"
  value       = module.aks.kube_config_raw
  sensitive   = true
}

output "aks_oidc_issuer_url" {
  description = "OIDC issuer URL for workload identity"
  value       = module.aks.oidc_issuer_url
}

# -----------------------------------------------------------------------------
# Container Registry
# -----------------------------------------------------------------------------

output "container_registry_name" {
  description = "Name of the Azure Container Registry"
  value       = module.container_registry.registry_name
}

output "container_registry_login_server" {
  description = "Login server URL for the container registry"
  value       = module.container_registry.login_server
}

# -----------------------------------------------------------------------------
# Database
# -----------------------------------------------------------------------------

output "database_server_fqdn" {
  description = "FQDN of the PostgreSQL server"
  value       = module.database.server_fqdn
  sensitive   = true
}

output "database_name" {
  description = "Name of the PostgreSQL database"
  value       = module.database.database_name
}

# -----------------------------------------------------------------------------
# Monitoring
# -----------------------------------------------------------------------------

output "log_analytics_workspace_id" {
  description = "ID of the Log Analytics workspace"
  value       = module.monitoring.log_analytics_workspace_id
}

output "application_insights_connection_string" {
  description = "Application Insights connection string"
  value       = module.monitoring.application_insights_connection_string
  sensitive   = true
}

# -----------------------------------------------------------------------------
# Key Vault
# -----------------------------------------------------------------------------

output "key_vault_uri" {
  description = "URI of the Key Vault"
  value       = module.keyvault.vault_uri
}

output "key_vault_name" {
  description = "Name of the Key Vault"
  value       = module.keyvault.vault_name
}

# -----------------------------------------------------------------------------
# ArgoCD
# -----------------------------------------------------------------------------

output "argocd_url" {
  description = "ArgoCD UI URL"
  value       = var.install_argocd ? module.argocd[0].argocd_url : null
}

output "argocd_namespace" {
  description = "ArgoCD namespace"
  value       = var.install_argocd ? module.argocd[0].argocd_namespace : null
}

# -----------------------------------------------------------------------------
# GitHub Actions OIDC
# -----------------------------------------------------------------------------

output "github_actions_client_id" {
  description = "Client ID used for GitHub Actions OIDC app"
  value       = local.gha_client_id
}

output "github_actions_service_principal_object_id" {
  description = "Service principal object ID for GitHub Actions OIDC app"
  value       = local.gha_sp_object_id
}
