# =============================================================================
# Kubernetes Add-ons Module Outputs
# =============================================================================
# Purpose: Export add-on information
# Following: Clean Architecture - clear interface contracts
# =============================================================================

output "nginx_ingress_installed" {
  description = "Whether NGINX Ingress was installed"
  value       = var.install_nginx_ingress
}

output "nginx_ingress_namespace" {
  description = "Namespace where NGINX Ingress is installed"
  value       = var.install_nginx_ingress ? "ingress-nginx" : null
}

output "cert_manager_installed" {
  description = "Whether cert-manager was installed"
  value       = var.install_cert_manager
}

output "cert_manager_namespace" {
  description = "Namespace where cert-manager is installed"
  value       = var.install_cert_manager ? "cert-manager" : null
}

output "external_dns_installed" {
  description = "Whether external-dns was installed"
  value       = var.install_external_dns
}

output "external_dns_namespace" {
  description = "Namespace where external-dns is installed"
  value       = var.install_external_dns ? "external-dns" : null
}
