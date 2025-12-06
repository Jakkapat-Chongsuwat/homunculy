# =============================================================================
# Cert-Manager - Outputs
# =============================================================================

output "namespace" {
  description = "Namespace where cert-manager is installed"
  value       = "cert-manager"
}

output "staging_issuer" {
  description = "Name of the staging ClusterIssuer"
  value       = var.create_cluster_issuers ? "letsencrypt-staging" : null
}

output "production_issuer" {
  description = "Name of the production ClusterIssuer"
  value       = var.create_cluster_issuers ? "letsencrypt-prod" : null
}

output "installation_method" {
  description = "How cert-manager was installed"
  value       = var.use_command_invoke ? "az-aks-command-invoke" : "helm-release"
}

output "enabled" {
  description = "Whether cert-manager is enabled"
  value       = var.enabled
}
