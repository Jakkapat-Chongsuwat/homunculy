# =============================================================================
# AKS Module - Main Configuration
# =============================================================================
# Purpose: Create and configure Azure Kubernetes Service cluster
# Following: Clean Architecture - single responsibility module
# =============================================================================

# -----------------------------------------------------------------------------
# User Assigned Identity for AKS
# -----------------------------------------------------------------------------

resource "azurerm_user_assigned_identity" "aks" {
  name                = "id-${var.project_name}-aks-${var.environment}"
  resource_group_name = var.resource_group_name
  location            = var.location

  tags = var.tags
}

# -----------------------------------------------------------------------------
# AKS Cluster
# -----------------------------------------------------------------------------

resource "azurerm_kubernetes_cluster" "main" {
  name                = "aks-${var.project_name}-${var.environment}"
  resource_group_name = var.resource_group_name
  location            = var.location
  dns_prefix          = "${var.project_name}-${var.environment}"

  kubernetes_version        = var.kubernetes_version
  sku_tier                  = var.sku_tier
  automatic_upgrade_channel = var.automatic_upgrade
  node_os_upgrade_channel   = var.node_os_upgrade_channel

  # Private cluster configuration
  private_cluster_enabled             = var.private_cluster_enabled
  private_dns_zone_id                 = var.private_cluster_enabled ? var.private_dns_zone_id : null
  private_cluster_public_fqdn_enabled = var.private_cluster_enabled ? false : null

  # Azure Policy addon
  azure_policy_enabled = var.azure_policy_enabled

  # Enable OIDC for workload identity
  oidc_issuer_enabled       = true
  workload_identity_enabled = true

  # Default node pool (system)
  default_node_pool {
    name                        = "system"
    vm_size                     = var.system_node_pool_vm_size
    node_count                  = var.system_node_pool_node_count
    auto_scaling_enabled        = true
    min_count                   = var.system_node_pool_min_count
    max_count                   = var.system_node_pool_max_count
    os_disk_size_gb             = 30
    os_disk_type                = "Managed"
    temporary_name_for_rotation = "systemtemp"
    vnet_subnet_id              = var.aks_subnet_id

    upgrade_settings {
      max_surge                     = "10%"
      drain_timeout_in_minutes      = 0
      node_soak_duration_in_minutes = 0
    }
  }

  # Identity
  identity {
    type         = "UserAssigned"
    identity_ids = [azurerm_user_assigned_identity.aks.id]
  }

  # Network configuration
  network_profile {
    network_plugin    = var.network_plugin
    network_policy    = var.network_policy
    dns_service_ip    = var.dns_service_ip
    service_cidr      = var.service_cidr
    load_balancer_sku = var.load_balancer_sku
  }

  # Azure Monitor integration
  oms_agent {
    log_analytics_workspace_id = var.log_analytics_workspace_id
  }

  # Key Vault secrets provider
  key_vault_secrets_provider {
    secret_rotation_enabled = true
  }

  # Microsoft Defender for Containers
  dynamic "microsoft_defender" {
    for_each = var.microsoft_defender_enabled ? [1] : []
    content {
      log_analytics_workspace_id = var.log_analytics_workspace_id
    }
  }

  tags = var.tags

  lifecycle {
    ignore_changes = [
      default_node_pool[0].node_count,
    ]
  }
}

# -----------------------------------------------------------------------------
# ACR Pull Role Assignment
# -----------------------------------------------------------------------------

resource "azurerm_role_assignment" "aks_acr_pull" {
  count = var.container_registry_id != "" ? 1 : 0

  principal_id                     = try(azurerm_kubernetes_cluster.main.kubelet_identity[0].object_id, null)
  role_definition_name             = "AcrPull"
  scope                            = var.container_registry_id
  skip_service_principal_aad_check = true
}

# -----------------------------------------------------------------------------
# Key Vault Access for AKS
# -----------------------------------------------------------------------------

resource "azurerm_role_assignment" "aks_keyvault_secrets_user" {
  count = var.keyvault_id != "" ? 1 : 0

  principal_id                     = try(azurerm_kubernetes_cluster.main.key_vault_secrets_provider[0].secret_identity[0].object_id, null)
  role_definition_name             = "Key Vault Secrets User"
  scope                            = var.keyvault_id
  skip_service_principal_aad_check = true
}

# -----------------------------------------------------------------------------
# User Node Pool (optional - for workloads)
# -----------------------------------------------------------------------------

resource "azurerm_kubernetes_cluster_node_pool" "user" {
  count = var.create_user_node_pool ? 1 : 0

  name                  = "user"
  kubernetes_cluster_id = azurerm_kubernetes_cluster.main.id
  vm_size               = var.user_node_pool_vm_size
  node_count            = var.user_node_pool_node_count
  auto_scaling_enabled  = true
  min_count             = var.user_node_pool_min_count
  max_count             = var.user_node_pool_max_count
  os_disk_size_gb       = 30
  os_disk_type          = "Managed"
  mode                  = "User"

  node_labels = {
    "workload" = "user"
  }

  node_taints = []

  upgrade_settings {
    max_surge                     = "10%"
    drain_timeout_in_minutes      = 0
    node_soak_duration_in_minutes = 0
  }

  tags = var.tags

  lifecycle {
    ignore_changes = [
      node_count,
    ]
  }
}
