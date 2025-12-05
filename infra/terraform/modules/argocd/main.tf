# =============================================================================
# ArgoCD Module - GitOps Deployment
# =============================================================================
# Purpose: Install and configure ArgoCD on AKS cluster
# =============================================================================

resource "helm_release" "argocd" {
  name             = "argocd"
  repository       = "https://argoproj.github.io/argo-helm"
  chart            = "argo-cd"
  version          = var.argocd_version
  namespace        = "argocd"
  create_namespace = true

  # Wait for deployment to complete
  wait    = true
  timeout = 600

  # Core settings
  values = [
    yamlencode({
      global = {
        logging = {
          level = var.environment == "prod" ? "info" : "debug"
        }
      }

      configs = {
        params = {
          # Enable insecure mode for internal access (use ingress TLS instead)
          "server.insecure" = true
        }
        cm = {
          # Enable Kustomize
          "kustomize.buildOptions" = "--enable-helm"
          # Application resync period
          "timeout.reconciliation" = "180s"
        }
        rbac = {
          "policy.default" = "role:readonly"
          "policy.csv"     = <<-EOT
            p, role:admin, applications, *, */*, allow
            p, role:admin, clusters, *, *, allow
            p, role:admin, repositories, *, *, allow
            g, admin, role:admin
          EOT
        }
      }

      # Server configuration
      server = {
        replicas = var.environment == "prod" ? 2 : 1

        resources = {
          requests = {
            cpu    = "100m"
            memory = "128Mi"
          }
          limits = {
            cpu    = "500m"
            memory = "512Mi"
          }
        }

        # Ingress for ArgoCD UI
        ingress = {
          enabled          = var.enable_ingress
          ingressClassName = "webapprouting.kubernetes.azure.com"
          hostname         = var.argocd_hostname
          annotations = {
            "nginx.ingress.kubernetes.io/backend-protocol" = "HTTP"
            "nginx.ingress.kubernetes.io/ssl-redirect"     = "false"
          }
        }
      }

      # Repo Server
      repoServer = {
        replicas = var.environment == "prod" ? 2 : 1
        resources = {
          requests = {
            cpu    = "100m"
            memory = "128Mi"
          }
          limits = {
            cpu    = "500m"
            memory = "512Mi"
          }
        }
      }

      # Application Controller
      controller = {
        replicas = 1
        resources = {
          requests = {
            cpu    = "100m"
            memory = "256Mi"
          }
          limits = {
            cpu    = "500m"
            memory = "512Mi"
          }
        }
      }

      # Redis (HA for prod)
      redis = {
        resources = {
          requests = {
            cpu    = "50m"
            memory = "64Mi"
          }
          limits = {
            cpu    = "200m"
            memory = "128Mi"
          }
        }
      }

      # Dex (SSO) - disabled by default
      dex = {
        enabled = false
      }

      # Notifications - disabled by default
      notifications = {
        enabled = false
      }
    })
  ]

  set_sensitive {
    name  = "configs.secret.argocdServerAdminPassword"
    value = bcrypt(var.admin_password)
  }
}

# =============================================================================
# ArgoCD Application - Bootstrap the GitOps apps
# =============================================================================

resource "kubectl_manifest" "argocd_app" {
  count = var.create_root_app ? 1 : 0

  yaml_body = yamlencode({
    apiVersion = "argoproj.io/v1alpha1"
    kind       = "Application"
    metadata = {
      name      = "homunculy-apps"
      namespace = "argocd"
      finalizers = [
        "resources-finalizer.argocd.argoproj.io"
      ]
    }
    spec = {
      project = "default"
      source = {
        repoURL        = var.git_repo_url
        targetRevision = var.git_target_revision
        path           = var.git_apps_path
      }
      destination = {
        server    = "https://kubernetes.default.svc"
        namespace = "homunculy"
      }
      syncPolicy = {
        automated = {
          prune    = true
          selfHeal = true
        }
        syncOptions = [
          "CreateNamespace=true"
          , "PruneLast=true"
        ]
      }
    }
  })

  depends_on = [helm_release.argocd]
}
