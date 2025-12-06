# =============================================================================
# ArgoCD Module - Outputs
# =============================================================================

output "argocd_namespace" {
  description = "The namespace where ArgoCD is installed"
  value       = "argocd"
}

output "argocd_server_service" {
  description = "ArgoCD server service name"
  value       = "argocd-server"
}

output "argocd_url" {
  description = "ArgoCD UI URL"
  value       = var.enable_ingress ? "https://${var.argocd_hostname}" : "Use kubectl port-forward"
}

output "installation_method" {
  description = "How ArgoCD was installed"
  value       = "aks-k8s-extension"
}
