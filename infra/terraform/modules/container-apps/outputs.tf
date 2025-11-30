# =============================================================================
# Container Apps Module - Outputs
# =============================================================================

output "environment_id" {
  description = "ID of the Container Apps Environment"
  value       = azurerm_container_app_environment.main.id
}

output "environment_name" {
  description = "Name of the Container Apps Environment"
  value       = azurerm_container_app_environment.main.name
}

output "homunculy_app_id" {
  description = "ID of the homunculy-app container app"
  value       = azurerm_container_app.homunculy.id
}

output "homunculy_app_name" {
  description = "Name of the homunculy-app container app"
  value       = azurerm_container_app.homunculy.name
}

output "homunculy_app_fqdn" {
  description = "FQDN of the homunculy-app container app"
  value       = azurerm_container_app.homunculy.ingress[0].fqdn
}

output "homunculy_app_url" {
  description = "URL of the homunculy-app container app"
  value       = "https://${azurerm_container_app.homunculy.ingress[0].fqdn}"
}

output "chat_client_id" {
  description = "ID of the chat-client container app"
  value       = azurerm_container_app.chat_client.id
}

output "chat_client_name" {
  description = "Name of the chat-client container app"
  value       = azurerm_container_app.chat_client.name
}

output "chat_client_fqdn" {
  description = "FQDN of the chat-client container app"
  value       = azurerm_container_app.chat_client.ingress[0].fqdn
}

output "chat_client_url" {
  description = "URL of the chat-client container app"
  value       = "https://${azurerm_container_app.chat_client.ingress[0].fqdn}"
}
