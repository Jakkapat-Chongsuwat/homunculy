# =============================================================================
# Terraform Backend Configuration
# =============================================================================
# Using Terraform Cloud for remote state management
# =============================================================================

terraform {
  cloud {
    organization = "Homunculy"

    workspaces {
      name = "homunculy-dev"
    }
  }
}

# Note: Set execution mode to "Local" in Terraform Cloud workspace settings
# This allows using local var files while storing state remotely
# Go to: app.terraform.io > Homunculy > homunculy-dev > Settings > General > Execution Mode > Local
