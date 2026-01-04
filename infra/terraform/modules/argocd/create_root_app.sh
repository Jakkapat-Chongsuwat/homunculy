#!/usr/bin/env bash
# shellcheck shell=bash
# =============================================================================
# Create ArgoCD Root Application (GitOps Bootstrap)
# =============================================================================
# Usage: create_root_app.sh <resource_group> <cluster_name> <app_name> <git_repo_url> <git_revision> <git_path>
# =============================================================================
set -euo pipefail

RESOURCE_GROUP="$1"
CLUSTER_NAME="$2"
APP_NAME="$3"
GIT_REPO_URL="$4"
GIT_REVISION="$5"
GIT_PATH="$6"

echo "Creating ArgoCD root application: ${APP_NAME}..."

PYTHONIOENCODING=utf-8 az aks command invoke \
  --resource-group "${RESOURCE_GROUP}" \
  --name "${CLUSTER_NAME}" \
  --command "cat <<'EOF' | kubectl apply -f -
apiVersion: argoproj.io/v1alpha1
kind: Application
metadata:
  name: ${APP_NAME}
  namespace: argocd
spec:
  project: default
  source:
    repoURL: ${GIT_REPO_URL}
    targetRevision: ${GIT_REVISION}
    path: ${GIT_PATH}
  destination:
    server: https://kubernetes.default.svc
    namespace: argocd
  syncPolicy:
    automated:
      prune: true
      selfHeal: true
    syncOptions:
      - CreateNamespace=true
EOF" 2>&1 | tr -d '\u2388'

echo "Root application ${APP_NAME} created successfully."
