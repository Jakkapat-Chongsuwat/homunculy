# =============================================================================
# Terraform Backend Configuration
# =============================================================================
# Purpose: Configure remote state storage in Azure Blob Storage
# Note: Values are provided via backend.tfvars per environment
# =============================================================================

terraform {
  backend "azurerm" {
    # These values are provided via -backend-config flag
    # resource_group_name  = "rg-homunculy-tfstate"
    # storage_account_name = "sthomunculytfstate"
    # container_name       = "tfstate"
    # key                  = "dev.terraform.tfstate"
  }
}
