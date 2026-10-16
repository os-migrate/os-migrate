# Functional tests (tests/func)

These Ansible playbooks exercise the os-migrate export/import roles and modules
end to end (seed → export → import → idempotence → update → clean) for tenant
and admin resources. They run against **two [gostack](https://github.com/os-migrate/gostack)
fake-OpenStack instances** — a source cloud and a destination cloud — so no real
OpenStack is needed. CI runs them on every PR (`.github/workflows/func-test.yml`).

- `test_as_tenant.yml` — networks, subnets, security groups + rules, routers +
  interfaces, images, keypairs, plus the `validate_data_dir` checks.
- `test_as_admin.yml` — projects, users, domains, flavors, user keypairs and
  user/project/role assignments.

## Running locally

You need Go (to build gostack), Python 3.12, and the pinned Python deps.

```bash
# 1. Build gostack (sibling checkout of os-migrate/gostack)
git clone https://github.com/os-migrate/gostack ../gostack
( cd ../gostack && go build -o bin/fake-openstack ./cmd/fake-openstack )

# 2. Python deps (a venv is recommended)
pip install -r requirements.txt -r requirements-tests.txt ansible-core

# 3. Make the collection importable and link the vendored openstack.cloud modules
#    (run from the collection root, i.e. this repo)
make vendor-links
COLLECTIONS=$(mktemp -d)
mkdir -p "$COLLECTIONS/ansible_collections/os_migrate"
ln -s "$PWD" "$COLLECTIONS/ansible_collections/os_migrate/os_migrate"
ansible-galaxy collection install plugins/modules/_vendor/openstack.cloud -p "$COLLECTIONS"
export ANSIBLE_COLLECTIONS_PATH="$COLLECTIONS"

# 4. Run the suite (starts/stops the two gostack instances automatically)
export GOSTACK_BIN="$PWD/../gostack/bin/fake-openstack"
bash tests/func/run-gostack.sh
```

`run-gostack.sh` starts a source instance (port 15001) and a destination
instance (port 15002), writes a `clouds.yaml` and an auth vars file pointing at
them, and runs both playbooks. Override `OSM_FUNC_SRC_PORT`, `OSM_FUNC_DST_PORT`,
`OSM_FUNC_WORKDIR` or `OSM_FUNC_PLAYBOOKS` as needed.

## Notes

- The image test uses a small locally-generated blob by default. Set
  `os_migrate_func_image_url` to download a real image instead (e.g. for a run
  against real clouds).
- gostack keeps a single in-memory state per process, so a source→destination
  migration needs the two separate instances the runner starts.
