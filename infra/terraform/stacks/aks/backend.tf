# =============================================================================
# Terraform Backend Configuration
# =============================================================================
# Using Terraform Cloud for remote state management
# =============================================================================

terraform {
  cloud {
    organization = "Homunculy"

    workspaces {
      tags = ["aks"]
    }
  }
}

# Note: Create workspaces in Terraform Cloud with tags:
# - homunculy-aks-dev (tags: aks, dev)
# - homunculy-aks-prod (tags: aks, prod)
# Set execution mode to "Local" in workspace settings
