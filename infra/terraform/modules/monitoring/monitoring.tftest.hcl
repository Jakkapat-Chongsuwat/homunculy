# =============================================================================
# Monitoring Module - Unit Tests
# =============================================================================
# Purpose: Validate Log Analytics and Application Insights configuration
# Run: terraform test (from modules/monitoring directory)
# =============================================================================

# Mock provider to avoid real Azure calls
mock_provider "azurerm" {}

variables {
  resource_group_name = "rg-test"
  location            = "eastus"
  project_name        = "homunculy"
  environment         = "dev"
  retention_in_days   = 30
  tags = {
    test = "true"
  }
}

# -----------------------------------------------------------------------------
# Test: Log Analytics workspace name convention
# -----------------------------------------------------------------------------
run "log_analytics_name" {
  command = plan

  module {
    source = "./."
  }

  assert {
    condition     = azurerm_log_analytics_workspace.main.name == "log-homunculy-dev"
    error_message = "Log Analytics name should follow pattern: log-{project}-{environment}"
  }
}

# -----------------------------------------------------------------------------
# Test: Log Analytics uses correct SKU
# -----------------------------------------------------------------------------
run "log_analytics_sku" {
  command = plan

  module {
    source = "./."
  }

  assert {
    condition     = azurerm_log_analytics_workspace.main.sku == "PerGB2018"
    error_message = "Log Analytics should use PerGB2018 SKU"
  }
}

# -----------------------------------------------------------------------------
# Test: Retention period is correct
# -----------------------------------------------------------------------------
run "log_analytics_retention" {
  command = plan

  module {
    source = "./."
  }

  assert {
    condition     = azurerm_log_analytics_workspace.main.retention_in_days == 30
    error_message = "Dev retention should be 30 days"
  }
}

# -----------------------------------------------------------------------------
# Test: Production has longer retention
# -----------------------------------------------------------------------------
run "prod_retention" {
  command = plan

  variables {
    environment       = "prod"
    retention_in_days = 90
  }

  module {
    source = "./."
  }

  assert {
    condition     = azurerm_log_analytics_workspace.main.retention_in_days == 90
    error_message = "Prod retention should be 90 days"
  }
}

# -----------------------------------------------------------------------------
# Test: Application Insights name convention
# -----------------------------------------------------------------------------
run "app_insights_name" {
  command = plan

  module {
    source = "./."
  }

  assert {
    condition     = azurerm_application_insights.main.name == "appi-homunculy-dev"
    error_message = "App Insights name should follow pattern: appi-{project}-{environment}"
  }
}

# -----------------------------------------------------------------------------
# Test: Application Insights type is web
# -----------------------------------------------------------------------------
run "app_insights_type" {
  command = plan

  module {
    source = "./."
  }

  assert {
    condition     = azurerm_application_insights.main.application_type == "web"
    error_message = "App Insights application type should be 'web'"
  }
}

# -----------------------------------------------------------------------------
# Test: Resources have component tag
# -----------------------------------------------------------------------------
run "monitoring_tags" {
  command = plan

  module {
    source = "./."
  }

  assert {
    condition     = contains(keys(azurerm_log_analytics_workspace.main.tags), "component")
    error_message = "Log Analytics should have 'component' tag"
  }

  assert {
    condition     = contains(keys(azurerm_application_insights.main.tags), "component")
    error_message = "App Insights should have 'component' tag"
  }
}
