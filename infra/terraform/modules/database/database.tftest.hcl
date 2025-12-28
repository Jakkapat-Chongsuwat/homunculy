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

run "azure_services_firewall" {
  command = plan

  module {
    source = "./."
  }

  assert {
    condition     = azurerm_postgresql_flexible_server_firewall_rule.allow_azure_services[0].start_ip_address == "0.0.0.0"
    error_message = "Firewall should allow Azure services (0.0.0.0)"
  }
}

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
