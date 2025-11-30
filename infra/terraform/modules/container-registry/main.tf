# =============================================================================
# Container Registry Module - Main
# =============================================================================
# Purpose: Provision Azure Container Registry for Docker images
# Following: Clean Architecture - Infrastructure layer
# =============================================================================

resource "azurerm_container_registry" "main" {
  name                = "acr${replace(var.project_name, "-", "")}${var.environment}"
  resource_group_name = var.resource_group_name
  location            = var.location
  sku                 = var.sku
  admin_enabled       = var.admin_enabled

  tags = merge(var.tags, {
    component = "container-registry"
  })
}
