# Argo CD bootstrap (optional)

This folder is for installing Argo CD *after* the cluster exists, then creating a single “root” Application that points at the environment entrypoint:

- `infra/k8s/clusters/dev`
- `infra/k8s/clusters/prod`

## Recommended flow (install later)

1) Provision infra with Terraform **without** Argo CD (set `install_argocd = false` in your `aks.tfvars` and apply).
2) Install Argo CD into the cluster.
3) Apply `root-app.yaml` (edit placeholders first).

## Notes for private AKS

If your API server is private and you don’t have network access for `kubectl`, run these operations via `az aks command invoke`.

This repo also supports installing Argo CD via Terraform using `az aks command invoke` (see `infra/terraform/modules/argocd`). In that mode, these YAMLs are still the canonical manifests for ingress/ILB.
