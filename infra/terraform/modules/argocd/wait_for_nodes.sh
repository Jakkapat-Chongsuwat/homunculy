#!/usr/bin/env bash
# shellcheck shell=bash
# =============================================================================
# AKS Node Readiness Guard for Argo CD
# =============================================================================
# Usage: wait_for_nodes.sh <resource_group> <cluster_name> [max_retries]
# Notes: Runs kubectl via az aks command invoke (safe for private clusters).
# =============================================================================
set -euo pipefail
RESOURCE_GROUP="$1"
CLUSTER_NAME="$2"
MAX_RETRIES="${3:-30}"

echo "Checking AKS node readiness..."
for i in $(seq 1 "${MAX_RETRIES}"); do
  READY=$(az aks command invoke \
    --resource-group "${RESOURCE_GROUP}" \
    --name "${CLUSTER_NAME}" \
    --command "kubectl get nodes -o json | jq -r '.items[] | select(.status.conditions[] | select(.type==\"Ready\" and .status==\"True\")) | .metadata.name' | wc -l" \
    --query "logs" -o tsv 2>/dev/null | grep -o '[0-9]*' | head -1 || echo "0")
  if [ "${READY}" -ge 1 ]; then
    echo "Nodes ready: ${READY}"
    exit 0
  fi
  echo "Waiting for nodes... attempt ${i}/${MAX_RETRIES}"
  sleep 10
done

echo "Warning: nodes not ready after $((MAX_RETRIES*10))s, continuing"
exit 0
