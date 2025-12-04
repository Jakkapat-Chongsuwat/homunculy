# =============================================================================
# Terraform Backend Configuration
# =============================================================================
# Using Terraform Cloud for remote state management
# =============================================================================

terraform {
  cloud {
    organization = "Homunculy"

    workspaces {
      tags = ["container-apps"]
    }
  }
}

# Note: Create workspaces in Terraform Cloud with tags:
# - homunculy-container-apps-dev (tags: container-apps, dev)
# - homunculy-container-apps-prod (tags: container-apps, prod)
# Set execution mode to "Local" in workspace settings
