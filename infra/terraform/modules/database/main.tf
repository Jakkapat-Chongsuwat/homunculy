# =============================================================================
# Database Module - Main
# =============================================================================
# Purpose: Provision Azure PostgreSQL Flexible Server
# Following: Clean Architecture - Infrastructure layer
# =============================================================================

resource "azurerm_postgresql_flexible_server" "main" {
  name                          = "psql-${var.project_name}-${var.environment}"
  resource_group_name           = var.resource_group_name
  location                      = var.location
  version                       = "16"
  administrator_login           = "homunculyadmin"
  administrator_password        = var.admin_password
  sku_name                      = var.sku_name
  storage_mb                    = var.storage_mb
  backup_retention_days         = var.backup_retention_days
  geo_redundant_backup_enabled  = var.environment == "prod" ? true : false
  public_network_access_enabled = var.delegated_subnet_id == null ? true : false
  
  # VNet integration (private access)
  delegated_subnet_id = var.delegated_subnet_id
  private_dns_zone_id = var.private_dns_zone_id

  # Zone redundancy for production
  zone = var.environment == "prod" ? "1" : null

  tags = merge(var.tags, {
    component = "database"
  })

  lifecycle {
    prevent_destroy = false  # Set to true in production
    ignore_changes  = [zone] # Zone cannot be changed after creation
  }

  depends_on = [
    var.private_dns_zone_id
  ]
}

# Database
resource "azurerm_postgresql_flexible_server_database" "main" {
  name      = var.database_name
  server_id = azurerm_postgresql_flexible_server.main.id
  charset   = "UTF8"
  collation = "en_US.utf8"
}

# Firewall rule to allow Azure services (only when public access is enabled)
resource "azurerm_postgresql_flexible_server_firewall_rule" "allow_azure_services" {
  count = var.delegated_subnet_id == null ? 1 : 0

  name             = "AllowAzureServices"
  server_id        = azurerm_postgresql_flexible_server.main.id
  start_ip_address = "0.0.0.0"
  end_ip_address   = "0.0.0.0"
}

# Server configuration for performance
resource "azurerm_postgresql_flexible_server_configuration" "timezone" {
  name      = "timezone"
  server_id = azurerm_postgresql_flexible_server.main.id
  value     = "UTC"
}

resource "azurerm_postgresql_flexible_server_configuration" "log_connections" {
  name      = "log_connections"
  server_id = azurerm_postgresql_flexible_server.main.id
  value     = "on"
}
