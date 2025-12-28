# Homunculy Infrastructure

## Layout

Kubernetes (GitOps-ready):

```
infra/k8s/
  apps/               # one folder per app (base + overlays)
  platform/           # cluster/platform components (DNS, namespace, secrets, ingress, network policy)
  clusters/           # one entry per environment (dev/prod) composing apps + platform
```

Terraform:

```
infra/terraform/
  modules/
  stacks/
  environments/
```

## Deploy (Terraform)

```bash
cd infra/terraform/stacks/aks
terraform init
terraform apply -var-file=../../environments/prod/aks.tfvars
```

## Argo CD install (best practice)

Argo CD should be installed after the cluster exists (i.e., after `terraform apply` completes). The most common best-practice flow is:

1) Terraform provisions cloud + AKS
2) A bootstrap step (CI job or script) installs/updates Argo CD into the cluster
3) Argo CD then owns all Kubernetes app/platform manifests via GitOps

Installing Argo CD via Terraform (Helm/Kubernetes providers) can work, but it couples your infra apply to cluster access and often makes troubleshooting upgrades harder. A dedicated post-apply bootstrap step is usually simpler and more reliable.

This repo supports both approaches:

- **Install later (recommended operationally)**: keep Argo CD as a post-apply bootstrap step.
  - Store bootstrap manifests in `infra/k8s/bootstrap/argocd`.
  - The root app should point to `infra/k8s/clusters/<env>`.
- **Terraform-managed install (supported here)**: the `infra/terraform/modules/argocd` module installs Argo CD via `az aks command invoke` (works for private AKS) and can optionally create the root app.

### Apply Argo CD later (two-step)

1) First apply infra without Argo CD (set `install_argocd = false` in your environment tfvars and run `terraform apply`).
2) Later, enable Argo CD (set `install_argocd = true`) and re-run `terraform apply`.

If you prefer a non-Terraform bootstrap, install Argo CD after the cluster exists and apply the root app from `infra/k8s/bootstrap/argocd/root-app.yaml`.

## Apply manifests (Kustomize)

Dev:

```bash
kubectl apply -k infra/k8s/clusters/dev
```

Prod:

```bash
kubectl apply -k infra/k8s/clusters/prod
```

## Terraform checks

```bash
cd infra/terraform
terraform fmt -recursive
terraform validate
terraform test -verbose
```

## Destroy

```bash
cd infra/terraform/stacks/aks
terraform destroy -var-file=../../environments/prod/aks.tfvars
```
