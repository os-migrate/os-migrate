#!/usr/bin/env bash
#
# Deploy AWX on a local kind cluster for the os-migrate AWX functional tests.
#
# Usage:
#   deploy-awx.sh install   Create the kind cluster (if missing), install the
#                           pinned AWX Operator and create the AWX instance.
#                           Returns as soon as everything is applied.
#   deploy-awx.sh wait      Wait until the AWX API answers and has capacity.
#   deploy-awx.sh password  Print the AWX admin password.
#   deploy-awx.sh all       install + wait.
#
# Splitting install and wait lets CI build the execution environment while
# the operator brings AWX up (that takes several minutes).
#
# Optional:
#   OSM_AWX_CLUSTER     kind cluster name     (default osm-awx)
#   OSM_AWX_NAMESPACE   AWX namespace         (default awx)
#   OSM_AWX_URL         AWX URL on the host   (default http://localhost:8080)
#   OSM_AWX_TIMEOUT     wait timeout, seconds (default 1500)
set -euo pipefail

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CLUSTER="${OSM_AWX_CLUSTER:-osm-awx}"
NAMESPACE="${OSM_AWX_NAMESPACE:-awx}"
AWX_URL="${OSM_AWX_URL:-http://localhost:8080}"
TIMEOUT="${OSM_AWX_TIMEOUT:-1500}"

install() {
  if kind get clusters 2>/dev/null | grep -qx "$CLUSTER"; then
    echo "kind cluster $CLUSTER already exists"
  else
    kind create cluster --name "$CLUSTER" --config "$HERE/kind-config.yml" --wait 120s
  fi
  kubectl config use-context "kind-$CLUSTER" >/dev/null

  echo "Installing AWX Operator"
  kubectl apply -k "$HERE/awx-operator"
  kubectl wait --for condition=established --timeout=120s crd/awxs.awx.ansible.com
  kubectl -n "$NAMESPACE" rollout status deployment/awx-operator-controller-manager --timeout=600s

  echo "Creating AWX instance"
  kubectl apply -f "$HERE/awx.yml"
}

wait_ready() {
  echo "Waiting for AWX at $AWX_URL (timeout ${TIMEOUT}s)"
  local deadline=$((SECONDS + TIMEOUT)) ping
  while (( SECONDS < deadline )); do
    if ping="$(curl -sf "$AWX_URL/api/v2/ping/" 2>/dev/null)" \
        && echo "$ping" | jq -e '(.instances | length) > 0 and ([.instances[].capacity] | add) > 0' >/dev/null 2>&1; then
      echo "AWX is up: $(echo "$ping" | jq -c '{version, instances: [.instances[] | {node, capacity}]}')"
      # The admin password secret is created by the operator before the API is up,
      # but double check authentication works before declaring victory.
      if curl -sf -u "admin:$(password)" "$AWX_URL/api/v2/me/" >/dev/null; then
        return 0
      fi
    fi
    sleep 15
    kubectl -n "$NAMESPACE" get pods --no-headers 2>/dev/null | sed 's/^/  /' || true
  done
  echo "ERROR: AWX did not become ready within ${TIMEOUT}s" >&2
  return 1
}

password() {
  kubectl -n "$NAMESPACE" get secret awx-admin-password -o jsonpath='{.data.password}' | base64 -d
}

case "${1:-all}" in
  install) install ;;
  wait) wait_ready ;;
  password) password ;;
  all) install; wait_ready ;;
  *) echo "Usage: $0 {install|wait|password|all}" >&2; exit 2 ;;
esac
