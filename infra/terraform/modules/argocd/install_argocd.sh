#!/usr/bin/env bash
# shellcheck shell=bash
# =============================================================================
# Argo CD Install via az aks command invoke (private cluster safe)
# =============================================================================
# Usage: install_argocd.sh <resource_group> <cluster_name> <manifest_url>
# Applies manifest and waits for argocd-server rollout.
# =============================================================================
set -euo pipefail
RESOURCE_GROUP="$1"
CLUSTER_NAME="$2"
MANIFEST_URL="$3"

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ILB_MANIFEST_CONTENT=$(cat "${SCRIPT_DIR}/argocd-ilb.yaml")

echo "Installing Argo CD via manifest using az aks command invoke..."
PYTHONIOENCODING=utf-8 az aks command invoke \
  --resource-group "${RESOURCE_GROUP}" \
  --name "${CLUSTER_NAME}" \
  --command "\
    kubectl create namespace argocd --dry-run=client -o yaml | kubectl apply -f - && \
    kubectl apply -n argocd -f ${MANIFEST_URL} && \
    cat <<'EOF' | kubectl apply -f -
${ILB_MANIFEST_CONTENT}
EOF
    kubectl rollout status deploy/argocd-server -n argocd --timeout=300s && \
    kubectl get svc -n argocd
  " 2>&1 | tr -d '\u2388'

echo "Argo CD installation invoked."
