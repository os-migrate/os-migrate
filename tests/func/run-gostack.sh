#!/usr/bin/env bash
#
# Run the os-migrate functional test suite (tests/func) against two gostack
# fake-OpenStack instances (a "source" and a "destination" cloud).
#
# It starts the two fake clouds, generates a clouds.yaml and an auth vars file
# pointing at them, then runs the tenant and admin functional playbooks.
#
# Required:
#   GOSTACK_BIN   Path to a built gostack `fake-openstack` binary.
#                 (CI builds it from the gostack repo's main branch.)
#
# Optional:
#   OSM_FUNC_SRC_PORT   Source cloud port       (default 15001)
#   OSM_FUNC_DST_PORT   Destination cloud port  (default 15002)
#   OSM_FUNC_WORKDIR    Scratch dir for config/data (default: mktemp)
#   OSM_FUNC_PLAYBOOKS  Space-separated playbooks   (default: both)
#
# The collection must be importable as os_migrate.os_migrate and openstack.cloud
# must be available on ANSIBLE_COLLECTIONS_PATH, with vendored modules linked
# (make vendor-links). See .github/workflows/func-test.yml for the full setup.
set -euo pipefail

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$HERE/../.." && pwd)"

: "${GOSTACK_BIN:?Set GOSTACK_BIN to a built gostack fake-openstack binary}"
SRC_PORT="${OSM_FUNC_SRC_PORT:-15001}"
DST_PORT="${OSM_FUNC_DST_PORT:-15002}"
WORKDIR="${OSM_FUNC_WORKDIR:-$(mktemp -d)}"
PLAYBOOKS="${OSM_FUNC_PLAYBOOKS:-test_as_tenant.yml test_as_admin.yml}"

SRC_URL="http://127.0.0.1:${SRC_PORT}"
DST_URL="http://127.0.0.1:${DST_PORT}"
mkdir -p "$WORKDIR"

pids=()
# shellcheck disable=SC2329  # invoked indirectly via 'trap cleanup EXIT'
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
  "$GOSTACK_BIN" --port "$port" --base-url "$url" \
    --pid-file "$WORKDIR/gostack-${port}.pid" \
    >"$WORKDIR/gostack-${name}.log" 2>&1 &
  pids+=("$!")
  for _ in $(seq 1 50); do
    if curl -sf "$url/v3" >/dev/null 2>&1; then
      echo "gostack $name ready on $url"
      return 0
    fi
    sleep 0.2
  done
  echo "ERROR: gostack $name did not become ready on $url" >&2
  cat "$WORKDIR/gostack-${name}.log" >&2
  return 1
}

start_instance "$SRC_PORT" "$SRC_URL" src
start_instance "$DST_PORT" "$DST_URL" dst

cat >"$WORKDIR/clouds.yaml" <<EOF
clouds:
  src:
    auth:
      auth_url: ${SRC_URL}/v3
      username: admin
      password: password
      project_name: admin
      user_domain_name: Default
      project_domain_name: Default
    region_name: RegionOne
    identity_api_version: 3
  dst:
    auth:
      auth_url: ${DST_URL}/v3
      username: admin
      password: password
      project_name: admin
      user_domain_name: Default
      project_domain_name: Default
    region_name: RegionOne
    identity_api_version: 3
EOF

cat >"$WORKDIR/func-vars.yml" <<EOF
os_migrate_data_dir: ${WORKDIR}/data
os_migrate_tests_tmp_dir: ${WORKDIR}/tmp
os_migrate_src_region_name: RegionOne
os_migrate_dst_region_name: RegionOne
os_migrate_src_filters: {}
os_migrate_dst_filters: {}
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

export OS_CLIENT_CONFIG_FILE="$WORKDIR/clouds.yaml"

rc=0
for pb in $PLAYBOOKS; do
  echo "=============================================================="
  echo "Running tests/func/$pb against gostack"
  echo "=============================================================="
  rm -rf "$WORKDIR/data" "$WORKDIR/tmp"
  if ! ansible-playbook \
      -i "$REPO_ROOT/inventory/localhost.yml" \
      -e @"$WORKDIR/func-vars.yml" \
      "$HERE/$pb"; then
    echo "FAILED: $pb" >&2
    rc=1
  fi
done

exit "$rc"
