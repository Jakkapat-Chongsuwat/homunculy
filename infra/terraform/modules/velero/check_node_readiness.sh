#!/bin/bash
# =============================================================================
# AKS Node Readiness Check
# =============================================================================
# Purpose: Wait for AKS nodes to be ready before deploying Velero
# Usage: Called by Terraform null_resource provisioner
# =============================================================================

set -e

RESOURCE_GROUP="$1"
CLUSTER_NAME="$2"
MAX_RETRIES="${3:-30}"

echo "=== Checking AKS node readiness ==="
echo "Resource Group: $RESOURCE_GROUP"
echo "Cluster: $CLUSTER_NAME"
echo "Max Retries: $MAX_RETRIES"

RETRY_COUNT=0

while [ "$RETRY_COUNT" -lt "$MAX_RETRIES" ]; do
  READY_NODES=$(az aks command invoke \
    --resource-group "$RESOURCE_GROUP" \
    --name "$CLUSTER_NAME" \
    --command "kubectl get nodes -o json | jq -r '.items[] | select(.status.conditions[] | select(.type==\"Ready\" and .status==\"True\")) | .metadata.name' | wc -l" \
    --query "logs" -o tsv 2>/dev/null | grep -o '[0-9]*' | head -1 || echo "0")
  
  if [ "$READY_NODES" -ge "1" ]; then
    echo "✓ AKS nodes are ready ($READY_NODES nodes)"
    exit 0
  fi
  
  echo "⏳ Waiting for nodes to be ready... (attempt $((RETRY_COUNT+1))/$MAX_RETRIES)"
  sleep 10
  RETRY_COUNT=$((RETRY_COUNT+1))
done

echo "⚠ Warning: Node readiness check timed out after $((MAX_RETRIES * 10)) seconds"
echo "Proceeding with deployment anyway..."
exit 0
