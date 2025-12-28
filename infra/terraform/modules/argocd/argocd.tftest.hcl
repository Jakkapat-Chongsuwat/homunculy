mock_provider "null" {}

run "install_resources_created" {
  command = plan

  variables {
    environment         = "dev"
    admin_password      = "test-password"
    resource_group_name = "rg-test"
    aks_cluster_name    = "aks-test"
    aks_cluster_id      = "/subscriptions/xxx/aks"
    public_ip           = "1.2.3.4"
  }

  assert {
    condition     = null_resource.argocd_install.triggers.public_ip == "1.2.3.4"
    error_message = "Expected argocd_install to be configured with provided public_ip"
  }

  assert {
    condition     = null_resource.wait_for_nodes.triggers.cluster_id == "/subscriptions/xxx/aks"
    error_message = "Expected wait_for_nodes to be configured with provided cluster_id"
  }
}

run "root_app_enabled_creates_resource" {
  command = plan

  variables {
    environment         = "dev"
    admin_password      = "test-password"
    resource_group_name = "rg-test"
    aks_cluster_name    = "aks-test"
    aks_cluster_id      = "/subscriptions/xxx/aks"
    create_root_app     = true
    git_repo_url        = "https://github.com/custom/repo.git"
    git_target_revision = "feature/branch"
    git_apps_path       = "infra/k8s/clusters/dev"
  }

  assert {
    condition     = length(null_resource.root_app) == 1
    error_message = "Expected root_app resource when create_root_app=true"
  }
}

run "root_app_disabled_creates_no_resource" {
  command = plan

  variables {
    environment         = "dev"
    admin_password      = "test-password"
    resource_group_name = "rg-test"
    aks_cluster_name    = "aks-test"
    aks_cluster_id      = "/subscriptions/xxx/aks"
    create_root_app     = false
  }

  assert {
    condition     = length(null_resource.root_app) == 0
    error_message = "Expected no root_app resource when create_root_app=false"
  }
}
