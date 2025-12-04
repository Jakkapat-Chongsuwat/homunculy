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

# -----------------------------------------------------------------------------
# Helm Provider (for Kubernetes add-ons)
# -----------------------------------------------------------------------------

provider "helm" {
  kubernetes {
    host                   = try(module.aks.cluster_fqdn, "https://localhost")
    cluster_ca_certificate = try(base64decode(module.aks.kube_config[0].cluster_ca_certificate), "")
    client_certificate     = try(base64decode(module.aks.kube_config[0].client_certificate), "")
    client_key             = try(base64decode(module.aks.kube_config[0].client_key), "")
  }
}

# -----------------------------------------------------------------------------
# Kubectl Provider (for raw manifests like ClusterIssuers)
# -----------------------------------------------------------------------------

provider "kubectl" {
  host                   = try(module.aks.cluster_fqdn, "https://localhost")
  cluster_ca_certificate = try(base64decode(module.aks.kube_config[0].cluster_ca_certificate), "")
  client_certificate     = try(base64decode(module.aks.kube_config[0].client_certificate), "")
  client_key             = try(base64decode(module.aks.kube_config[0].client_key), "")
  load_config_file       = false
}
