# =============================================================================
# NGINX Ingress Controller - Outputs
# =============================================================================

output "namespace" {
  description = "Namespace where NGINX Ingress is installed"
  value       = "ingress-nginx"
}

output "service_name" {
  description = "Name of the NGINX Ingress service"
  value       = "ingress-nginx-controller"
}

output "installation_method" {
  description = "How NGINX Ingress was installed"
  value       = var.use_command_invoke ? "az-aks-command-invoke" : "helm-release"
}

output "enabled" {
  description = "Whether NGINX Ingress is enabled"
  value       = var.enabled
}
