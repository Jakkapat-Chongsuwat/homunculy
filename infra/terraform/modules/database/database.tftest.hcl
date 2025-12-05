# =============================================================================
# Database Module - Unit Tests
# =============================================================================
# Purpose: Validate PostgreSQL Flexible Server configuration
# Run: terraform test (from modules/database directory)
# =============================================================================

# Mock provider to avoid real Azure calls
mock_provider "azurerm" {}

variables {
  resource_group_name   = "rg-test"
  location              = "eastus"
  project_name          = "homunculy"
  environment           = "dev"
  sku_name              = "B_Standard_B1ms"
  storage_mb            = 32768
  backup_retention_days = 7
  database_name         = "homunculy"
  admin_password        = "TestPassword123!"
  tags = {
    test = "true"
  }
}

# -----------------------------------------------------------------------------
# Test: Server name follows naming convention
# -----------------------------------------------------------------------------
run "server_name_convention" {
  command = plan

  module {
    source = "./."
  }

  assert {
    condition     = azurerm_postgresql_flexible_server.main.name == "psql-homunculy-dev"
    error_message = "PostgreSQL server name should follow pattern: psql-{project}-{environment}"
  }
}

# -----------------------------------------------------------------------------
# Test: Server uses PostgreSQL 16
# -----------------------------------------------------------------------------
run "server_version" {
  command = plan

  module {
    source = "./."
  }

  assert {
    condition     = azurerm_postgresql_flexible_server.main.version == "16"
    error_message = "PostgreSQL version should be 16"
  }
}

# -----------------------------------------------------------------------------
# Test: Dev environment has geo-redundant backup disabled
# -----------------------------------------------------------------------------
run "dev_backup_settings" {
  command = plan

  module {
    source = "./."
  }

  assert {
    condition     = azurerm_postgresql_flexible_server.main.geo_redundant_backup_enabled == false
    error_message = "Dev environment should not have geo-redundant backups"
  }
}

# -----------------------------------------------------------------------------
# Test: Production environment has geo-redundant backup enabled
# -----------------------------------------------------------------------------
run "prod_backup_settings" {
  command = plan

  variables {
    environment = "prod"
  }

  module {
    source = "./."
  }

  assert {
    condition     = azurerm_postgresql_flexible_server.main.geo_redundant_backup_enabled == true
    error_message = "Prod environment should have geo-redundant backups enabled"
  }
}

# -----------------------------------------------------------------------------
# Test: Database name is correct
# -----------------------------------------------------------------------------
run "database_name_check" {
  command = plan

  module {
    source = "./."
  }

  assert {
    condition     = azurerm_postgresql_flexible_server_database.main.name == "homunculy"
    error_message = "Database name should be 'homunculy'"
  }

  assert {
    condition     = azurerm_postgresql_flexible_server_database.main.charset == "UTF8"
    error_message = "Database charset should be UTF8"
  }
}

# -----------------------------------------------------------------------------
# Test: Firewall rule allows Azure services
# -----------------------------------------------------------------------------
run "azure_services_firewall" {
  command = plan

  module {
    source = "./."
  }

  assert {
    condition     = azurerm_postgresql_flexible_server_firewall_rule.allow_azure_services.start_ip_address == "0.0.0.0"
    error_message = "Firewall should allow Azure services (0.0.0.0)"
  }
}

# -----------------------------------------------------------------------------
# Test: Server configuration for timezone
# -----------------------------------------------------------------------------
run "server_timezone_config" {
  command = plan

  module {
    source = "./."
  }

  assert {
    condition     = azurerm_postgresql_flexible_server_configuration.timezone.value == "UTC"
    error_message = "Server timezone should be UTC"
  }
}
