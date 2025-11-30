# =============================================================================
# Azure Provider Configuration
# =============================================================================
# Purpose: Configure Azure providers with recommended settings
# Following: Clean Code - explicit configuration, no hidden defaults
# =============================================================================

provider "azurerm" {
  features {
    key_vault {
      purge_soft_delete_on_destroy    = false
      recover_soft_deleted_key_vaults = true
    }

    resource_group {
      prevent_deletion_if_contains_resources = false
    }
  }

  subscription_id = var.subscription_id
}

provider "azapi" {}

provider "random" {}
