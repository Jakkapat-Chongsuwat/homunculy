output "vnet_id" {
  description = "ID of the virtual network"
  value       = azurerm_virtual_network.main.id
}

output "vnet_name" {
  description = "Name of the virtual network"
  value       = azurerm_virtual_network.main.name
}

output "aks_subnet_id" {
  description = "ID of the AKS subnet"
  value       = azurerm_subnet.aks.id
}

output "database_subnet_id" {
  description = "ID of the database subnet"
  value       = azurerm_subnet.database.id
}

output "private_endpoints_subnet_id" {
  description = "ID of the private endpoints subnet"
  value       = azurerm_subnet.private_endpoints.id
}

output "bastion_subnet_id" {
  description = "ID of the bastion subnet"
  value       = var.create_bastion_subnet ? azurerm_subnet.bastion[0].id : null
}

output "postgresql_private_dns_zone_id" {
  description = "ID of PostgreSQL private DNS zone"
  value       = var.create_private_dns_zones ? azurerm_private_dns_zone.postgresql[0].id : null
}

output "keyvault_private_dns_zone_id" {
  description = "ID of Key Vault private DNS zone"
  value       = var.create_private_dns_zones ? azurerm_private_dns_zone.keyvault[0].id : null
}

output "acr_private_dns_zone_id" {
  description = "ID of ACR private DNS zone"
  value       = var.create_private_dns_zones ? azurerm_private_dns_zone.acr[0].id : null
}

output "nsg_aks_id" {
  description = "ID of AKS network security group"
  value       = azurerm_network_security_group.aks.id
}

output "nsg_aks_name" {
  description = "Name of AKS network security group"
  value       = azurerm_network_security_group.aks.name
}

