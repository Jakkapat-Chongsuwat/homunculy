# Argo CD bootstrap (Terraform)

This repo installs Argo CD via Terraform (safe for private AKS using `az aks command invoke`).

- `argocd-ilb.yaml` and `argocd-ingress.yaml` are used by the Terraform module during install.
- The Argo CD **root Application** is created by Terraform via `infra/terraform/modules/argocd/create_root_app.sh`.

If you want to stop Terraform from creating the root app, set `argocd_create_root_app = false` in your Terraform variables.
