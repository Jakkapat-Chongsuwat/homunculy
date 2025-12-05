# =============================================================================
# AKS Module Outputs
# =============================================================================
# Purpose: Export AKS cluster information
# Following: Clean Code - meaningful outputs
# =============================================================================

output "cluster_id" {
  description = "ID of the AKS cluster"
  value       = azurerm_kubernetes_cluster.main.id
}

output "cluster_name" {
  description = "Name of the AKS cluster"
  value       = azurerm_kubernetes_cluster.main.name
}

output "cluster_fqdn" {
  description = "FQDN of the AKS cluster"
  value       = azurerm_kubernetes_cluster.main.fqdn
}

output "kube_config" {
  description = "Kubeconfig for the AKS cluster"
  value       = azurerm_kubernetes_cluster.main.kube_config
  sensitive   = true
}

output "kube_config_raw" {
  description = "Raw kubeconfig for the AKS cluster"
  value       = azurerm_kubernetes_cluster.main.kube_config_raw
  sensitive   = true
}

output "oidc_issuer_url" {
  description = "OIDC issuer URL for workload identity"
  value       = azurerm_kubernetes_cluster.main.oidc_issuer_url
}

output "kubelet_identity_object_id" {
  description = "Object ID of kubelet identity"
  value       = try(azurerm_kubernetes_cluster.main.kubelet_identity[0].object_id, null)
}

output "kubelet_identity_client_id" {
  description = "Client ID of kubelet identity"
  value       = try(azurerm_kubernetes_cluster.main.kubelet_identity[0].client_id, null)
}

output "node_resource_group" {
  description = "Resource group for AKS nodes"
  value       = azurerm_kubernetes_cluster.main.node_resource_group
}

output "identity_principal_id" {
  description = "Principal ID of AKS managed identity"
  value       = azurerm_user_assigned_identity.aks.principal_id
}

output "private_fqdn" {
  description = "Private FQDN of the AKS cluster (when private cluster is enabled)"
  value       = azurerm_kubernetes_cluster.main.private_fqdn
}

output "azure_policy_enabled" {
  description = "Whether Azure Policy is enabled"
  value       = azurerm_kubernetes_cluster.main.azure_policy_enabled
}

output "identity_client_id" {
  description = "Client ID of AKS managed identity"
  value       = azurerm_user_assigned_identity.aks.client_id
}

output "web_app_routing_enabled" {
  description = "Whether Azure Application Routing (managed NGINX) is enabled"
  value       = var.enable_app_routing
}
