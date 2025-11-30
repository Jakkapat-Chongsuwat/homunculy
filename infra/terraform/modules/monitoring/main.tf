# =============================================================================
# Monitoring Module - Main
# =============================================================================
# Purpose: Provision monitoring infrastructure (Log Analytics + App Insights)
# Following: Clean Architecture - Infrastructure layer
# =============================================================================

resource "azurerm_log_analytics_workspace" "main" {
  name                = "log-${var.project_name}-${var.environment}"
  location            = var.location
  resource_group_name = var.resource_group_name
  sku                 = "PerGB2018"
  retention_in_days   = var.retention_in_days

  tags = merge(var.tags, {
    component = "monitoring"
  })
}

resource "azurerm_application_insights" "main" {
  name                = "appi-${var.project_name}-${var.environment}"
  location            = var.location
  resource_group_name = var.resource_group_name
  workspace_id        = azurerm_log_analytics_workspace.main.id
  application_type    = "web"

  tags = merge(var.tags, {
    component = "monitoring"
  })
}
