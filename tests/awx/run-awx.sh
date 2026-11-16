#!/usr/bin/env bash
#
# Run the os-migrate AWX functional tests.
#
# Expects AWX to be running in the kind cluster (tests/awx/deploy-awx.sh) and
# the os-migrate execution environment image to be loaded into it.
#
# It starts two gostack fake-OpenStack instances (source and destination) on
# the host, reachable from the AWX job pods through the kind network gateway,
# seeds the source cloud, configures AWX (EE, credential type, credential,
# project, inventory, job template), runs the migration job template and
# checks the destination cloud.
#
# Required:
#   GOSTACK_BIN            Path to a built gostack `fake-openstack` binary.
#
# Optional:
#   OSM_AWX_SCM_URL        Git URL AWX syncs the project from
#                          (default https://github.com/os-migrate/os-migrate).
#   OSM_AWX_SCM_BRANCH     Branch, tag or commit to sync (default: local HEAD,
#                          which must be pushed to OSM_AWX_SCM_URL).
#   OSM_AWX_EE_IMAGE       EE image loaded into kind (default os-migrate-aee:ci)
#   OSM_AWX_GOSTACK_HOST   Address of the host as seen from kind pods
#                          (default: IPv4 gateway of the "kind" docker network)
#   OSM_AWX_SRC_PORT       Source cloud port       (default 15001)
#   OSM_AWX_DST_PORT       Destination cloud port  (default 15002)
#   OSM_AWX_WORKDIR        Scratch dir             (default: mktemp)
#   OSM_AWX_ARTIFACTS      Logs and job outputs    (default: $OSM_AWX_WORKDIR/artifacts)
#   CONTROLLER_HOST        AWX URL                 (default http://localhost:8080)
#   CONTROLLER_USERNAME    AWX user                (default admin)
#   CONTROLLER_PASSWORD    AWX password            (default: read from the cluster)
#
# The collection must be importable as os_migrate.os_migrate with vendored
# modules linked (make vendor-links), and awx.awx must be installed
# (tests/awx/requirements.yml). See .github/workflows/awx-test.yml.
set -euo pipefail

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$HERE/../.." && pwd)"

: "${GOSTACK_BIN:?Set GOSTACK_BIN to a built gostack fake-openstack binary}"
SCM_URL="${OSM_AWX_SCM_URL:-https://github.com/os-migrate/os-migrate}"
SCM_BRANCH="${OSM_AWX_SCM_BRANCH:-$(git -C "$REPO_ROOT" rev-parse HEAD)}"
EE_IMAGE="${OSM_AWX_EE_IMAGE:-os-migrate-aee:ci}"
SRC_PORT="${OSM_AWX_SRC_PORT:-15001}"
DST_PORT="${OSM_AWX_DST_PORT:-15002}"
WORKDIR="${OSM_AWX_WORKDIR:-$(mktemp -d)}"
ARTIFACTS="${OSM_AWX_ARTIFACTS:-$WORKDIR/artifacts}"
mkdir -p "$WORKDIR" "$ARTIFACTS"

export CONTROLLER_HOST="${CONTROLLER_HOST:-http://localhost:8080}"
export CONTROLLER_USERNAME="${CONTROLLER_USERNAME:-admin}"
export CONTROLLER_VERIFY_SSL=false
if [ -z "${CONTROLLER_PASSWORD:-}" ]; then
  CONTROLLER_PASSWORD="$("$HERE/deploy-awx.sh" password)"
fi
export CONTROLLER_PASSWORD

if [ -z "${OSM_AWX_GOSTACK_HOST:-}" ]; then
  OSM_AWX_GOSTACK_HOST="$(docker network inspect kind \
    | jq -r '[.[0].IPAM.Config[] | .Gateway // empty | select(test("^[0-9.]+$"))][0] // empty')"
fi
: "${OSM_AWX_GOSTACK_HOST:?Could not determine the kind network gateway, set OSM_AWX_GOSTACK_HOST}"
SRC_URL="http://${OSM_AWX_GOSTACK_HOST}:${SRC_PORT}"
DST_URL="http://${OSM_AWX_GOSTACK_HOST}:${DST_PORT}"

pids=()
# cleanup is invoked indirectly via 'trap ... EXIT', which shellcheck cannot
# see (SC2317/SC2329).
# shellcheck disable=SC2317,SC2329
cleanup() {
  for pid in "${pids[@]:-}"; do
    if [ -n "$pid" ]; then
      kill "$pid" 2>/dev/null || true
    fi
  done
}
trap cleanup EXIT

start_instance() {
  local port="$1" url="$2" name="$3"
  # Bind on all interfaces so the AWX job pods (inside kind) can reach it;
  # advertise the gateway address in the Keystone catalog for the same reason.
  "$GOSTACK_BIN" --bind 0.0.0.0 --port "$port" --base-url "$url" \
    --pid-file "$WORKDIR/gostack-${port}.pid" \
    >"$ARTIFACTS/gostack-${name}.log" 2>&1 &
  pids+=("$!")
  for _ in $(seq 1 50); do
    if curl -sf "$url/v3" >/dev/null 2>&1; then
      echo "gostack $name ready on $url"
      return 0
    fi
    sleep 0.2
  done
  echo "ERROR: gostack $name did not become ready on $url" >&2
  cat "$ARTIFACTS/gostack-${name}.log" >&2
  return 1
}

start_instance "$SRC_PORT" "$SRC_URL" src
start_instance "$DST_PORT" "$DST_URL" dst

cat >"$WORKDIR/awx-vars.yml" <<EOF
osm_awx_scm_url: ${SCM_URL}
osm_awx_scm_branch: ${SCM_BRANCH}
osm_awx_ee_image: ${EE_IMAGE}
osm_awx_artifacts_dir: ${ARTIFACTS}
os_migrate_src_auth:
  auth_url: ${SRC_URL}/v3
  username: admin
  password: password
  project_name: admin
  user_domain_name: Default
  project_domain_name: Default
os_migrate_dst_auth:
  auth_url: ${DST_URL}/v3
  username: admin
  password: password
  project_name: admin
  user_domain_name: Default
  project_domain_name: Default
EOF

echo "AWX project: ${SCM_URL} @ ${SCM_BRANCH}"
echo "AWX EE image: ${EE_IMAGE}"

run_playbook() {
  echo "=============================================================="
  echo "Running tests/awx/$1"
  echo "=============================================================="
  ansible-playbook -i "$REPO_ROOT/inventory/localhost.yml" \
    -e @"$WORKDIR/awx-vars.yml" "$HERE/$1"
}

run_playbook seed.yml
run_playbook configure_awx.yml
run_playbook run_awx_jobs.yml
run_playbook verify.yml

echo "AWX functional tests passed"
