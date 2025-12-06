# =============================================================================
# External-DNS - Outputs
# =============================================================================

output "namespace" {
  description = "Namespace where external-dns is installed"
  value       = "external-dns"
}

output "installation_method" {
  description = "How external-dns was installed"
  value       = var.use_command_invoke ? "az-aks-command-invoke" : "helm-release"
}

output "enabled" {
  description = "Whether external-dns is enabled"
  value       = var.enabled
}

output "managed_domains" {
  description = "Domains managed by external-dns"
  value       = var.domain_filters
}
