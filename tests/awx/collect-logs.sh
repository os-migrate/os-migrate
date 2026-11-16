#!/usr/bin/env bash
#
# Collect AWX / kind diagnostics into a directory (default ./awx-artifacts).
# Best effort: never fails, so it can run in a CI failure handler.
set -uo pipefail

OUT="${1:-${OSM_AWX_ARTIFACTS:-awx-artifacts}}"
NAMESPACE="${OSM_AWX_NAMESPACE:-awx}"
CONTROLLER_HOST="${CONTROLLER_HOST:-http://localhost:8080}"
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
mkdir -p "$OUT/k8s"

kubectl get all,pvc,events -A -o wide >"$OUT/k8s/all.txt" 2>&1
kubectl -n "$NAMESPACE" get awx -o yaml >"$OUT/k8s/awx-cr.yaml" 2>&1
kubectl -n "$NAMESPACE" describe pods >"$OUT/k8s/describe-pods.txt" 2>&1
for pod in $(kubectl -n "$NAMESPACE" get pods -o name 2>/dev/null); do
  name="${pod#pod/}"
  kubectl -n "$NAMESPACE" logs "$pod" --all-containers --prefix \
    >"$OUT/k8s/logs-${name}.txt" 2>&1
done

password="${CONTROLLER_PASSWORD:-$("$HERE/deploy-awx.sh" password 2>/dev/null)}"
if [ -n "$password" ]; then
  for endpoint in ping jobs project_updates; do
    curl -s -u "admin:${password}" "${CONTROLLER_HOST}/api/v2/${endpoint}/?order_by=-id" \
      >"$OUT/awx-api-${endpoint}.json" 2>&1
  done
  # Output of the last project updates (a failed sync is a common culprit).
  for id in $(jq -r '.results[:3][]?.id' "$OUT/awx-api-project_updates.json" 2>/dev/null); do
    curl -s -u "admin:${password}" \
      "${CONTROLLER_HOST}/api/v2/project_updates/${id}/stdout/?format=txt" \
      >"$OUT/awx-project-update-${id}.txt" 2>&1
  done
fi

df -h >"$OUT/df.txt" 2>&1
free -m >"$OUT/free.txt" 2>&1
docker images >"$OUT/docker-images.txt" 2>&1
echo "Diagnostics collected in $OUT"
exit 0
