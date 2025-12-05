# =============================================================================
# VNet Module - Unit Tests
# =============================================================================
# Purpose: Validate VNet and subnet configuration
# Run: terraform test (from modules/vnet directory)
# =============================================================================

mock_provider "azurerm" {}

variables {
  resource_group_name = "rg-test"
  location            = "eastus"
  project_name        = "homunculy"
  environment         = "dev"

  address_space                           = ["10.0.0.0/8"]
  aks_subnet_address_prefix               = ["10.1.0.0/16"]
  database_subnet_address_prefix          = ["10.2.0.0/24"]
  private_endpoints_subnet_address_prefix = ["10.3.0.0/24"]
  bastion_subnet_address_prefix           = ["10.4.0.0/24"]

  create_bastion_subnet    = false
  create_private_dns_zones = true

  tags = {
    test = "true"
  }
}

# -----------------------------------------------------------------------------
# Test: VNet name convention
# -----------------------------------------------------------------------------
run "vnet_name_convention" {
  command = plan

  module {
    source = "./."
  }

  assert {
    condition     = azurerm_virtual_network.main.name == "vnet-homunculy-dev"
    error_message = "VNet name should follow pattern: vnet-{project}-{environment}"
  }
}

# -----------------------------------------------------------------------------
# Test: VNet address space
# -----------------------------------------------------------------------------
run "vnet_address_space" {
  command = plan

  module {
    source = "./."
  }

  assert {
    condition     = contains(azurerm_virtual_network.main.address_space, "10.0.0.0/8")
    error_message = "VNet should have the correct address space"
  }
}

# -----------------------------------------------------------------------------
# Test: AKS subnet name
# -----------------------------------------------------------------------------
run "aks_subnet_name" {
  command = plan

  module {
    source = "./."
  }

  assert {
    condition     = azurerm_subnet.aks.name == "snet-aks"
    error_message = "AKS subnet should be named snet-aks"
  }
}

# -----------------------------------------------------------------------------
# Test: AKS subnet address prefix
# -----------------------------------------------------------------------------
run "aks_subnet_address" {
  command = plan

  module {
    source = "./."
  }

  assert {
    condition     = azurerm_subnet.aks.address_prefixes[0] == "10.1.0.0/16"
    error_message = "AKS subnet should have correct address prefix"
  }
}

# -----------------------------------------------------------------------------
# Test: Database subnet name
# -----------------------------------------------------------------------------
run "database_subnet_name" {
  command = plan

  module {
    source = "./."
  }

  assert {
    condition     = azurerm_subnet.database.name == "snet-database"
    error_message = "Database subnet should be named snet-database"
  }
}

# -----------------------------------------------------------------------------
# Test: Private endpoints subnet
# -----------------------------------------------------------------------------
run "private_endpoints_subnet_name" {
  command = plan

  module {
    source = "./."
  }

  assert {
    condition     = azurerm_subnet.private_endpoints.name == "snet-private-endpoints"
    error_message = "Private endpoints subnet should be named snet-private-endpoints"
  }
}

# -----------------------------------------------------------------------------
# Test: NSG name convention
# -----------------------------------------------------------------------------
run "nsg_name_convention" {
  command = plan

  module {
    source = "./."
  }

  assert {
    condition     = azurerm_network_security_group.aks.name == "nsg-aks-homunculy-dev"
    error_message = "NSG name should follow pattern: nsg-aks-{project}-{environment}"
  }
}

# -----------------------------------------------------------------------------
# Test: Bastion subnet not created by default
# -----------------------------------------------------------------------------
run "bastion_subnet_not_created_by_default" {
  command = plan

  module {
    source = "./."
  }

  assert {
    condition     = length(azurerm_subnet.bastion) == 0
    error_message = "Bastion subnet should not be created by default"
  }
}

# -----------------------------------------------------------------------------
# Test: Bastion subnet created when enabled
# -----------------------------------------------------------------------------
run "bastion_subnet_created_when_enabled" {
  command = plan

  module {
    source = "./."
  }

  variables {
    create_bastion_subnet = true
  }

  assert {
    condition     = length(azurerm_subnet.bastion) == 1
    error_message = "Bastion subnet should be created when enabled"
  }
}

# -----------------------------------------------------------------------------
# Test: Bastion subnet name (must be exact)
# -----------------------------------------------------------------------------
run "bastion_subnet_exact_name" {
  command = plan

  module {
    source = "./."
  }

  variables {
    create_bastion_subnet = true
  }

  assert {
    condition     = azurerm_subnet.bastion[0].name == "AzureBastionSubnet"
    error_message = "Bastion subnet must be named exactly 'AzureBastionSubnet'"
  }
}

# -----------------------------------------------------------------------------
# Test: Private DNS zones created
# -----------------------------------------------------------------------------
run "postgresql_dns_zone_created" {
  command = plan

  module {
    source = "./."
  }

  assert {
    condition     = length(azurerm_private_dns_zone.postgresql) == 1
    error_message = "PostgreSQL private DNS zone should be created"
  }
}

run "keyvault_dns_zone_created" {
  command = plan

  module {
    source = "./."
  }

  assert {
    condition     = length(azurerm_private_dns_zone.keyvault) == 1
    error_message = "Key Vault private DNS zone should be created"
  }
}

run "acr_dns_zone_created" {
  command = plan

  module {
    source = "./."
  }

  assert {
    condition     = length(azurerm_private_dns_zone.acr) == 1
    error_message = "ACR private DNS zone should be created"
  }
}

# -----------------------------------------------------------------------------
# Test: DNS zones not created when disabled
# -----------------------------------------------------------------------------
run "dns_zones_not_created_when_disabled" {
  command = plan

  module {
    source = "./."
  }

  variables {
    create_private_dns_zones = false
  }

  assert {
    condition     = length(azurerm_private_dns_zone.postgresql) == 0
    error_message = "DNS zones should not be created when disabled"
  }
}

# -----------------------------------------------------------------------------
# Test: VNet tags applied
# -----------------------------------------------------------------------------
run "vnet_tags" {
  command = plan

  module {
    source = "./."
  }

  assert {
    condition     = azurerm_virtual_network.main.tags["test"] == "true"
    error_message = "VNet should have correct tags"
  }
}
