# =============================================================================
# Container Apps Module - Unit Tests
# =============================================================================
# Purpose: Validate Container Apps environment and app configurations
# Run: terraform test -filter=modules/container-apps/container-apps.tftest.hcl
# =============================================================================

# Mock providers to avoid real Azure calls
mock_provider "azurerm" {}
mock_provider "time" {}

variables {
  resource_group_name        = "rg-test"
  location                   = "eastus"
  project_name               = "homunculy"
  environment                = "dev"
  log_analytics_workspace_id = "/subscriptions/00000000-0000-0000-0000-000000000000/resourceGroups/rg-test/providers/Microsoft.OperationalInsights/workspaces/log-test"

  container_registry_login_server   = "acrhomunculydev.azurecr.io"
  container_registry_admin_username = "acrhomunculydev"
  container_registry_admin_password = "testpassword"

  homunculy_image_tag    = "v1.0.0"
  homunculy_min_replicas = 0
  homunculy_max_replicas = 5
  homunculy_cpu          = 0.5
  homunculy_memory       = "1Gi"

  chat_client_image_tag    = "v1.0.0"
  chat_client_min_replicas = 0
  chat_client_max_replicas = 5
  chat_client_cpu          = 0.25
  chat_client_memory       = "0.5Gi"

  database_host     = "psql-homunculy-dev.postgres.database.azure.com"
  database_name     = "homunculy"
  database_username = "homunculyadmin"

  keyvault_id  = "/subscriptions/00000000-0000-0000-0000-000000000000/resourceGroups/rg-test/providers/Microsoft.KeyVault/vaults/kv-test"
  keyvault_uri = "https://kv-test.vault.azure.net/"

  tags = {
    test = "true"
  }
}

# -----------------------------------------------------------------------------
# Test: Container Apps Environment name convention
# -----------------------------------------------------------------------------
run "environment_name" {
  command = plan

  assert {
    condition     = azurerm_container_app_environment.main.name == "cae-homunculy-dev"
    error_message = "Container Apps Environment name should follow pattern: cae-{project}-{environment}"
  }
}

# -----------------------------------------------------------------------------
# Test: Homunculy app name convention
# -----------------------------------------------------------------------------
run "homunculy_app_name" {
  command = plan

  assert {
    condition     = azurerm_container_app.homunculy.name == "ca-homunculy-dev"
    error_message = "Homunculy app name should follow pattern: ca-homunculy-{environment}"
  }
}

# -----------------------------------------------------------------------------
# Test: Chat client app name convention
# -----------------------------------------------------------------------------
run "chat_client_name" {
  command = plan

  assert {
    condition     = azurerm_container_app.chat_client.name == "ca-chat-client-dev"
    error_message = "Chat client name should follow pattern: ca-chat-client-{environment}"
  }
}

# -----------------------------------------------------------------------------
# Test: Homunculy app uses correct image tag
# -----------------------------------------------------------------------------
run "homunculy_image_tag" {
  command = plan

  assert {
    condition     = can(regex("homunculy-app:v1.0.0", azurerm_container_app.homunculy.template[0].container[0].image))
    error_message = "Homunculy should use image tag v1.0.0"
  }
}

# -----------------------------------------------------------------------------
# Test: Homunculy app has correct scaling
# -----------------------------------------------------------------------------
run "homunculy_scaling" {
  command = plan

  assert {
    condition     = azurerm_container_app.homunculy.template[0].min_replicas == 0
    error_message = "Dev min replicas should be 0"
  }

  assert {
    condition     = azurerm_container_app.homunculy.template[0].max_replicas == 5
    error_message = "Dev max replicas should be 5"
  }
}

# -----------------------------------------------------------------------------
# Test: Production has minimum 1 replica
# -----------------------------------------------------------------------------
run "prod_minimum_replicas" {
  command = plan

  variables {
    environment              = "prod"
    homunculy_min_replicas   = 1
    chat_client_min_replicas = 1
  }

  assert {
    condition     = azurerm_container_app.homunculy.template[0].min_replicas == 1
    error_message = "Prod should have minimum 1 replica"
  }
}

# -----------------------------------------------------------------------------
# Test: Apps have external ingress enabled
# -----------------------------------------------------------------------------
run "ingress_enabled" {
  command = plan

  assert {
    condition     = azurerm_container_app.homunculy.ingress[0].external_enabled == true
    error_message = "Homunculy should have external ingress"
  }

  assert {
    condition     = azurerm_container_app.chat_client.ingress[0].external_enabled == true
    error_message = "Chat client should have external ingress"
  }
}

# -----------------------------------------------------------------------------
# Test: Correct target ports
# -----------------------------------------------------------------------------
run "target_ports" {
  command = plan

  assert {
    condition     = azurerm_container_app.homunculy.ingress[0].target_port == 8000
    error_message = "Homunculy target port should be 8000"
  }

  assert {
    condition     = azurerm_container_app.chat_client.ingress[0].target_port == 8080
    error_message = "Chat client target port should be 8080"
  }
}

# -----------------------------------------------------------------------------
# Test: Apps have component tags
# -----------------------------------------------------------------------------
run "app_tags" {
  command = plan

  assert {
    condition     = azurerm_container_app.homunculy.tags["component"] == "homunculy-app"
    error_message = "Homunculy should have component=homunculy-app tag"
  }

  assert {
    condition     = azurerm_container_app.chat_client.tags["component"] == "chat-client"
    error_message = "Chat client should have component=chat-client tag"
  }
}

# -----------------------------------------------------------------------------
# Test: Revision mode is Single
# -----------------------------------------------------------------------------
run "revision_mode" {
  command = plan

  assert {
    condition     = azurerm_container_app.homunculy.revision_mode == "Single"
    error_message = "Homunculy revision mode should be Single"
  }

  assert {
    condition     = azurerm_container_app.chat_client.revision_mode == "Single"
    error_message = "Chat client revision mode should be Single"
  }
}

# -----------------------------------------------------------------------------
# Test: User Assigned Managed Identity is created
# -----------------------------------------------------------------------------
run "managed_identity_created" {
  command = plan

  assert {
    condition     = azurerm_user_assigned_identity.container_apps.name == "id-homunculy-containerapp-dev"
    error_message = "Managed Identity name should follow pattern: id-{project}-containerapp-{environment}"
  }
}

# -----------------------------------------------------------------------------
# Test: Role assignment for Key Vault Secrets User
# -----------------------------------------------------------------------------
run "keyvault_role_assignment" {
  command = plan

  assert {
    condition     = azurerm_role_assignment.keyvault_secrets_user.role_definition_name == "Key Vault Secrets User"
    error_message = "Role assignment should grant Key Vault Secrets User role"
  }

  assert {
    condition     = azurerm_role_assignment.keyvault_secrets_user.scope == "/subscriptions/00000000-0000-0000-0000-000000000000/resourceGroups/rg-test/providers/Microsoft.KeyVault/vaults/kv-test"
    error_message = "Role assignment scope should be the Key Vault"
  }
}

# -----------------------------------------------------------------------------
# Test: RBAC propagation delay is configured
# -----------------------------------------------------------------------------
run "rbac_propagation_delay" {
  command = plan

  assert {
    condition     = time_sleep.rbac_propagation.create_duration == "60s"
    error_message = "RBAC propagation delay should be 60 seconds"
  }
}

# -----------------------------------------------------------------------------
# Test: Homunculy app uses Key Vault references for secrets
# -----------------------------------------------------------------------------
run "homunculy_keyvault_secrets" {
  command = plan

  assert {
    condition     = length([for s in azurerm_container_app.homunculy.secret : s if s.name == "db-password"]) == 1
    error_message = "Homunculy should have db-password secret configured"
  }

  assert {
    condition     = length([for s in azurerm_container_app.homunculy.secret : s if s.name == "openai-api-key"]) == 1
    error_message = "Homunculy should have openai-api-key secret configured"
  }

  assert {
    condition     = length([for s in azurerm_container_app.homunculy.secret : s if s.name == "elevenlabs-api-key"]) == 1
    error_message = "Homunculy should have elevenlabs-api-key secret configured"
  }
}

# -----------------------------------------------------------------------------
# Test: Homunculy app has managed identity assigned
# -----------------------------------------------------------------------------
run "homunculy_managed_identity" {
  command = plan

  assert {
    condition     = azurerm_container_app.homunculy.identity[0].type == "UserAssigned"
    error_message = "Homunculy should have UserAssigned managed identity"
  }

  assert {
    condition     = length(azurerm_container_app.homunculy.identity[0].identity_ids) == 1
    error_message = "Homunculy should have exactly one identity assigned"
  }
}
