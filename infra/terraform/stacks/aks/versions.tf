# =============================================================================
# Terraform Version Constraints
# =============================================================================
# Purpose: Define provider versions and requirements
# Following: Clean Code - Single Responsibility, explicit dependencies
# =============================================================================

terraform {
  required_version = ">= 1.9.0"

  required_providers {
    azurerm = {
      source  = "hashicorp/azurerm"
      version = "~> 4.0"
    }

    azapi = {
      source  = "Azure/azapi"
      version = "~> 2.0"
    }

    random = {
      source  = "hashicorp/random"
      version = "~> 3.6"
    }

    time = {
      source  = "hashicorp/time"
      version = "~> 0.12"
    }

    helm = {
      source  = "hashicorp/helm"
      version = "3.1.1"
    }

    kubectl = {
      source  = "gavinbunney/kubectl"
      version = "~> 1.14"
    }

    azuread = {
      source  = "hashicorp/azuread"
      version = "~> 3.0"
    }
  }
}
