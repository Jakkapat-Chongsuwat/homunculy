# =============================================================================
# Container Apps Module - Main
# =============================================================================
# Purpose: Provision Azure Container Apps Environment and applications
# Following: Clean Architecture - Infrastructure layer
# Secrets: Retrieved from Azure Key Vault via managed identity
# =============================================================================

# -----------------------------------------------------------------------------
# Container Apps Environment
# -----------------------------------------------------------------------------

resource "azurerm_container_app_environment" "main" {
  name                       = "cae-${var.project_name}-${var.environment}"
  location                   = var.location
  resource_group_name        = var.resource_group_name
  log_analytics_workspace_id = var.log_analytics_workspace_id

  tags = merge(var.tags, {
    component = "container-apps"
  })
}

# -----------------------------------------------------------------------------
# User Assigned Managed Identity for Key Vault Access
# -----------------------------------------------------------------------------

resource "azurerm_user_assigned_identity" "container_apps" {
  name                = "id-${var.project_name}-containerapp-${var.environment}"
  resource_group_name = var.resource_group_name
  location            = var.location

  tags = var.tags
}

# Grant Key Vault Secrets User role to the managed identity
resource "azurerm_role_assignment" "keyvault_secrets_user" {
  scope                = var.keyvault_id
  role_definition_name = "Key Vault Secrets User"
  principal_id         = azurerm_user_assigned_identity.container_apps.principal_id
}

# -----------------------------------------------------------------------------
# Wait for RBAC propagation
# Azure RBAC can take up to 10 minutes to propagate. We add a delay to ensure
# the role assignment is effective before Container Apps try to access secrets.
# -----------------------------------------------------------------------------

resource "time_sleep" "rbac_propagation" {
  depends_on = [azurerm_role_assignment.keyvault_secrets_user]

  create_duration = "60s"
}

# -----------------------------------------------------------------------------
# Homunculy App (Python FastAPI)
# -----------------------------------------------------------------------------

resource "azurerm_container_app" "homunculy" {
  name                         = "ca-homunculy-${var.environment}"
  container_app_environment_id = azurerm_container_app_environment.main.id
  resource_group_name          = var.resource_group_name
  revision_mode                = "Single"

  tags = merge(var.tags, {
    component = "homunculy-app"
    runtime   = "python"
  })

  # Managed Identity for Key Vault access
  identity {
    type         = "UserAssigned"
    identity_ids = [azurerm_user_assigned_identity.container_apps.id]
  }

  # Registry authentication
  registry {
    server               = var.container_registry_login_server
    username             = var.container_registry_admin_username
    password_secret_name = "registry-password"
  }

  # Ensure role assignment is propagated before accessing Key Vault
  depends_on = [time_sleep.rbac_propagation]

  # Secrets - Key Vault references
  secret {
    name  = "registry-password"
    value = var.container_registry_admin_password
  }

  secret {
    name                = "db-password"
    key_vault_secret_id = "${var.keyvault_uri}secrets/db-password"
    identity            = azurerm_user_assigned_identity.container_apps.id
  }

  secret {
    name                = "openai-api-key"
    key_vault_secret_id = "${var.keyvault_uri}secrets/openai-api-key"
    identity            = azurerm_user_assigned_identity.container_apps.id
  }

  secret {
    name                = "elevenlabs-api-key"
    key_vault_secret_id = "${var.keyvault_uri}secrets/elevenlabs-api-key"
    identity            = azurerm_user_assigned_identity.container_apps.id
  }

  # Ingress configuration
  ingress {
    external_enabled = true
    target_port      = 8000
    transport        = "http"

    traffic_weight {
      percentage      = 100
      latest_revision = true
    }
  }

  template {
    min_replicas = var.homunculy_min_replicas
    max_replicas = var.homunculy_max_replicas

    container {
      name   = "homunculy-app"
      image  = "${var.container_registry_login_server}/homunculy-app:${var.homunculy_image_tag}"
      cpu    = var.homunculy_cpu
      memory = var.homunculy_memory

      # Environment variables
      env {
        name  = "APP_HOST"
        value = "0.0.0.0"
      }

      env {
        name  = "APP_PORT"
        value = "8000"
      }

      env {
        name  = "APP_DEBUG"
        value = "false"
      }

      env {
        name  = "DB_HOST"
        value = var.database_host
      }

      env {
        name  = "DB_PORT"
        value = "5432"
      }

      env {
        name  = "DB_NAME"
        value = var.database_name
      }

      env {
        name  = "DB_USER"
        value = var.database_username
      }

      env {
        name        = "DB_PASSWORD"
        secret_name = "db-password"
      }

      env {
        name  = "LLM_PROVIDER"
        value = "openai"
      }

      env {
        name        = "LLM_OPENAI_API_KEY"
        secret_name = "openai-api-key"
      }

      env {
        name  = "LLM_DEFAULT_MODEL"
        value = "gpt-4o-mini"
      }

      env {
        name  = "LLM_DEFAULT_TEMPERATURE"
        value = "0.7"
      }

      env {
        name  = "LLM_DEFAULT_MAX_TOKENS"
        value = "2000"
      }

      env {
        name  = "TTS_PROVIDER"
        value = "elevenlabs"
      }

      env {
        name        = "ELEVENLABS_API_KEY"
        secret_name = "elevenlabs-api-key"
      }

      env {
        name        = "TTS_ELEVENLABS_API_KEY"
        secret_name = "elevenlabs-api-key"
      }

      env {
        name  = "TTS_ELEVENLABS_MODEL_ID"
        value = "eleven_multilingual_v2"
      }

      env {
        name  = "TTS_ELEVENLABS_STREAMING_MODEL_ID"
        value = "eleven_turbo_v2_5"
      }

      env {
        name  = "LOGGING_LEVEL"
        value = "INFO"
      }

      env {
        name  = "LOGGING_FORMAT"
        value = "json"
      }

      # Health probes
      liveness_probe {
        path                    = "/health"
        port                    = 8000
        transport               = "HTTP"
        initial_delay           = 30
        interval_seconds        = 30
        timeout                 = 10
        failure_count_threshold = 3
      }

      readiness_probe {
        path                    = "/health"
        port                    = 8000
        transport               = "HTTP"
        initial_delay           = 10
        interval_seconds        = 10
        timeout                 = 5
        success_count_threshold = 1
        failure_count_threshold = 3
      }
    }

    # HTTP scaling rule
    http_scale_rule {
      name                = "http-scaling"
      concurrent_requests = 100
    }
  }
}

# -----------------------------------------------------------------------------
# Chat Client (Blazor Server)
# -----------------------------------------------------------------------------

resource "azurerm_container_app" "chat_client" {
  name                         = "ca-chat-client-${var.environment}"
  container_app_environment_id = azurerm_container_app_environment.main.id
  resource_group_name          = var.resource_group_name
  revision_mode                = "Single"

  tags = merge(var.tags, {
    component = "chat-client"
    runtime   = "dotnet"
  })

  # Registry authentication
  registry {
    server               = var.container_registry_login_server
    username             = var.container_registry_admin_username
    password_secret_name = "registry-password"
  }

  # Secrets
  secret {
    name  = "registry-password"
    value = var.container_registry_admin_password
  }

  # Ingress configuration
  ingress {
    external_enabled = true
    target_port      = 8080
    transport        = "http"

    traffic_weight {
      percentage      = 100
      latest_revision = true
    }
  }

  template {
    min_replicas = var.chat_client_min_replicas
    max_replicas = var.chat_client_max_replicas

    container {
      name   = "chat-client"
      image  = "${var.container_registry_login_server}/chat-client:${var.chat_client_image_tag}"
      cpu    = var.chat_client_cpu
      memory = var.chat_client_memory

      # Environment variables
      env {
        name  = "ASPNETCORE_URLS"
        value = "http://+:8080"
      }

      env {
        name  = "ASPNETCORE_ENVIRONMENT"
        value = var.environment == "prod" ? "Production" : "Development"
      }

      env {
        name  = "ConnectionStrings__homunculy-app"
        value = "https://${azurerm_container_app.homunculy.ingress[0].fqdn}"
      }

      # Health probes
      liveness_probe {
        path                    = "/health"
        port                    = 8080
        transport               = "HTTP"
        initial_delay           = 30
        interval_seconds        = 30
        timeout                 = 10
        failure_count_threshold = 3
      }

      readiness_probe {
        path                    = "/health"
        port                    = 8080
        transport               = "HTTP"
        initial_delay           = 10
        interval_seconds        = 10
        timeout                 = 5
        success_count_threshold = 1
        failure_count_threshold = 3
      }
    }

    # HTTP scaling rule
    http_scale_rule {
      name                = "http-scaling"
      concurrent_requests = 50
    }
  }

  depends_on = [azurerm_container_app.homunculy]
}
