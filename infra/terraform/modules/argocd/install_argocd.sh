#!/usr/bin/env bash
# shellcheck shell=bash
# =============================================================================
# Argo CD Install via az aks command invoke (private cluster safe)
# =============================================================================
# Usage: install_argocd.sh <resource_group> <cluster_name> <manifest_url> <public_ip>
# Applies manifest and waits for argocd-server rollout.
# =============================================================================
set -euo pipefail
RESOURCE_GROUP="$1"
CLUSTER_NAME="$2"
MANIFEST_URL="$3"
PUBLIC_IP="${4:-}"

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BOOTSTRAP_DIR="${SCRIPT_DIR}/../../../k8s/bootstrap/argocd"
ILB_MANIFEST_CONTENT=$(cat "${BOOTSTRAP_DIR}/argocd-ilb.yaml")

# Prepare ingress manifest if public IP is provided
if [ -n "${PUBLIC_IP}" ]; then
  INGRESS_MANIFEST_CONTENT=$(sed "s/\${PUBLIC_IP}/${PUBLIC_IP}/g" "${BOOTSTRAP_DIR}/argocd-ingress.yaml")
fi

echo "Installing Argo CD via manifest using az aks command invoke..."

# Build kubectl command
KUBECTL_CMD="kubectl create namespace argocd --dry-run=client -o yaml | kubectl apply -f - && \
kubectl apply -n argocd -f ${MANIFEST_URL} && \
cat <<'EOF' | kubectl apply -f -
${ILB_MANIFEST_CONTENT}
EOF"

# Add ingress manifest if public IP provided
if [ -n "${PUBLIC_IP}" ]; then
  KUBECTL_CMD="${KUBECTL_CMD} && cat <<'INGRESSEOF' | kubectl apply -f -
${INGRESS_MANIFEST_CONTENT}
INGRESSEOF"
fi

# Add configuration patch and rollout status
KUBECTL_CMD="${KUBECTL_CMD} && \
kubectl wait --for=condition=available --timeout=120s deployment/argocd-server -n argocd && \
kubectl patch configmap argocd-cmd-params-cm -n argocd --type merge -p '{\"data\":{\"server.insecure\":\"true\"}}' && \
kubectl rollout restart deployment/argocd-server -n argocd && \
kubectl rollout status deploy/argocd-server -n argocd --timeout=300s && \
kubectl get svc -n argocd"

PYTHONIOENCODING=utf-8 az aks command invoke \
  --resource-group "${RESOURCE_GROUP}" \
  --name "${CLUSTER_NAME}" \
  --command "${KUBECTL_CMD}" 2>&1 | tr -d '\u2388'

echo "Argo CD installation invoked."
