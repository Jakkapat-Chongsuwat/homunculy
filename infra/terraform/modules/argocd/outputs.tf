# =============================================================================
# ArgoCD Module - Outputs
# =============================================================================

output "argocd_namespace" {
  description = "The namespace where ArgoCD is installed"
  value       = helm_release.argocd.namespace
}

output "argocd_server_service" {
  description = "ArgoCD server service name"
  value       = "argocd-server"
}

output "argocd_url" {
  description = "ArgoCD UI URL"
  value       = var.enable_ingress ? "https://${var.argocd_hostname}" : "Use kubectl port-forward"
}
