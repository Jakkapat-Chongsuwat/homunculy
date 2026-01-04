#!/usr/bin/env bash
# shellcheck shell=bash
# =============================================================================
# Argo CD Install via az aks command invoke (private cluster safe)
# =============================================================================
# Usage: install_argocd.sh <resource_group> <cluster_name> <manifest_url> <enable_ingress> <public_ip>
# Applies manifest and waits for argocd-server rollout.
# =============================================================================
set -euo pipefail
RESOURCE_GROUP="${1:-}"
CLUSTER_NAME="${2:-}"
MANIFEST_URL="${3:-}"
ENABLE_INGRESS="${4:-true}"
PUBLIC_IP="${5:-}"

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BOOTSTRAP_DIR="${SCRIPT_DIR}/../../../k8s/bootstrap/argocd"

require_cmd() {
  local cmd="$1"
  if ! command -v "${cmd}" >/dev/null 2>&1; then
    echo "Missing required command: ${cmd}" >&2
    exit 1
  fi
}

require_arg() {
  local value="$1"
  local name="$2"
  if [ -z "${value}" ]; then
    echo "Missing required argument: ${name}" >&2
    exit 1
  fi
}

b64_encode_one_line() {
  if base64 --help 2>/dev/null | grep -q -- "-w"; then
    base64 -w0
  else
    base64 | tr -d '\n'
  fi
}

read_manifest_file() {
  local file_path="$1"
  cat "${file_path}"
}

render_manifest_template_optional_public_ip() {
  local file_path="$1"
  local public_ip="$2"
  if [ -n "${public_ip}" ]; then
    sed "s/\${PUBLIC_IP}/${public_ip}/g" "${file_path}"
  else
    cat "${file_path}"
  fi
}

encode_manifest_for_remote_apply() {
  local manifest_content="$1"
  printf '%s' "${manifest_content}" | b64_encode_one_line
}

build_argocd_cmd_params_patch_json() {
  local enable_ingress="$1"
  if [ "${enable_ingress}" = "true" ]; then
    echo '{"data":{"server.insecure":"true","server.rootpath":"/argocd","server.basehref":"/argocd"}}'
  else
    echo '{"data":{"server.insecure":"true"}}'
  fi
}

build_argocd_cm_patch_json() {
  echo '{"data":{"timeout.reconciliation":"30s"}}'
}

build_remote_kubectl_command() {
  local manifest_url="$1"
  local ilb_manifest_b64="$2"
  local enable_ingress="$3"
  local ingress_manifest_b64="$4"
  local cmd_params_patch_json="$5"
  local argocd_cm_patch_json="$6"

  local cmd
  cmd="kubectl create namespace argocd --dry-run=client -o yaml | kubectl apply -f - && \
kubectl apply -n argocd -f ${manifest_url} && \
echo '${ilb_manifest_b64}' | base64 -d | kubectl apply -f -"

  if [ "${enable_ingress}" = "true" ]; then
    cmd="${cmd} && echo '${ingress_manifest_b64}' | base64 -d | kubectl apply -f -"
  fi

  cmd="${cmd} && \
kubectl wait --for=condition=available --timeout=120s deployment/argocd-server -n argocd && \
kubectl patch configmap argocd-cmd-params-cm -n argocd --type merge -p '${cmd_params_patch_json}' && \
kubectl patch configmap argocd-cm -n argocd --type merge -p '${argocd_cm_patch_json}' && \
kubectl rollout restart deployment/argocd-server -n argocd && \
kubectl rollout restart statefulset/argocd-application-controller -n argocd && \
kubectl rollout status deploy/argocd-server -n argocd --timeout=300s && \
kubectl rollout status statefulset/argocd-application-controller -n argocd --timeout=300s && \
kubectl get svc -n argocd"

  printf '%s' "${cmd}"
}

run_aks_command_in_cluster() {
  local resource_group="$1"
  local cluster_name="$2"
  local remote_command="$3"

  local invoke_out exit_code

  invoke_out=$(PYTHONIOENCODING=utf-8 az aks command invoke \
    --resource-group "${resource_group}" \
    --name "${cluster_name}" \
    --command "${remote_command}" \
    -o json)

  printf '%s\n' "${invoke_out}"

  exit_code=$(printf '%s' "${invoke_out}" | tr -d '\r' | sed -n 's/.*"exitCode"[[:space:]]*:[[:space:]]*\(-\{0,1\}[0-9]\+\).*/\1/p' | head -n1)
  if [ -z "${exit_code}" ]; then
    echo "Could not read exitCode from az aks command invoke output" >&2
    exit 1
  fi
  if [ "${exit_code}" != "0" ]; then
    echo "az aks command invoke remote exitCode=${exit_code}" >&2
    exit "${exit_code}"
  fi
}

main() {
  require_arg "${RESOURCE_GROUP}" "resource_group"
  require_arg "${CLUSTER_NAME}" "cluster_name"
  require_arg "${MANIFEST_URL}" "manifest_url"

  require_cmd az
  require_cmd base64
  require_cmd sed
  require_cmd head
  require_cmd cat

  local ilb_manifest_content ingress_manifest_content
  local ilb_manifest_b64 ingress_manifest_b64
  local cmd_params_patch_json argocd_cm_patch_json remote_kubectl_cmd

  ilb_manifest_content=$(read_manifest_file "${BOOTSTRAP_DIR}/argocd-ilb.yaml")
  ilb_manifest_b64=$(encode_manifest_for_remote_apply "${ilb_manifest_content}")

  ingress_manifest_b64=""
  if [ "${ENABLE_INGRESS}" = "true" ]; then
    ingress_manifest_content=$(render_manifest_template_optional_public_ip "${BOOTSTRAP_DIR}/argocd-ingress.yaml" "${PUBLIC_IP}")
    ingress_manifest_b64=$(encode_manifest_for_remote_apply "${ingress_manifest_content}")
  fi

  cmd_params_patch_json=$(build_argocd_cmd_params_patch_json "${ENABLE_INGRESS}")
  argocd_cm_patch_json=$(build_argocd_cm_patch_json)
  remote_kubectl_cmd=$(build_remote_kubectl_command "${MANIFEST_URL}" "${ilb_manifest_b64}" "${ENABLE_INGRESS}" "${ingress_manifest_b64}" "${cmd_params_patch_json}" "${argocd_cm_patch_json}")

  echo "Installing Argo CD via manifest using az aks command invoke..."
  run_aks_command_in_cluster "${RESOURCE_GROUP}" "${CLUSTER_NAME}" "${remote_kubectl_cmd}"
  echo "Argo CD installation completed successfully."
}

main "$@"
