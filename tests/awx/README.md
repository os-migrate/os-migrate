# AWX functional tests

These tests run os-migrate **through AWX**, the way users run it in AWX /
Ansible Automation Platform, against two [gostack](https://github.com/os-migrate/gostack)
fake-OpenStack clouds. They complement `tests/func` (which runs the roles
directly with `ansible-playbook`) by also covering:

- the os-migrate execution environment (`aee/`) built from the commit under test,
- running the collection's playbooks (`os_migrate.os_migrate.export_*` /
  `import_*`) from an AWX project and job template,
- passing source/destination cloud credentials with a custom AWX credential type.

CI: `.github/workflows/awx-test.yml`. It runs on pushes to `main`, nightly,
on manual dispatch, and on pull requests labelled **`test-awx`** (bringing AWX
up takes ~10 minutes, so it does not run on every PR push).

## How it works

```
GitHub runner (ubuntu-24.04)
├── gostack src :15001, dst :15002   bound to 0.0.0.0, catalog URLs use the kind gateway IP
└── kind cluster "osm-awx"
    └── AWX (AWX Operator 2.19.1, AWX 24.6.1), UI/API on localhost:8080
        └── job pod = os-migrate EE image built from this commit (side-loaded, pull: never)
              └── reaches gostack through the kind network gateway
```

1. `deploy-awx.sh install` creates the kind cluster, installs the pinned AWX
   Operator (`awx-operator/`) and creates the AWX instance (`awx.yml`).
2. CI builds the collection and the EE (`ansible-builder`) and loads the image
   into kind, while the operator brings AWX up. `deploy-awx.sh wait` then waits
   for the AWX API.
3. `run-awx.sh` starts the two gostack clouds and runs, on the runner:
   - `seed.yml`: creates `osm_net`, `osm_subnet`, `osm_security_group` (+ a tcp/80 rule) in the source cloud,
   - `configure_awx.yml`: creates the EE, the `os-migrate clouds` credential type and a
     credential, a project (this repository at the commit under test), an inventory
     (`migrator` group with `localhost`) and the job template, using `awx.awx`,
   - `run_awx_jobs.yml`: launches the job template twice and saves each job's output,
   - `verify.yml`: checks the destination cloud has each resource exactly once
     (so the second run also checks the migration is idempotent).
4. On failure, `collect-logs.sh` gathers pod logs, the AWX CR, recent AWX jobs and
   project updates. Everything ends up in the `awx-test-artifacts` workflow artifact.

The job template runs `project/migrate_tenant.yml`, which imports the
collection's playbooks from the EE.

## Things worth knowing

- **One job = one pod.** Every AWX job starts with an empty filesystem, so the
  os-migrate data dir does not survive from one job to the next. That is why
  export and import run in the same job here. Splitting them into separate jobs
  (for example in a workflow job template) needs a persistent volume mounted at
  `os_migrate_data_dir`, via a container group with a custom pod spec.
- **Credentials.** AWX's built-in OpenStack credential covers a single cloud, and a
  job template can only take one credential per type, so os-migrate needs a custom
  credential type holding both clouds. Injectors can only inject strings, so the
  credential injects flat `osm_awx_{src,dst}_*` extra vars and the first play of
  `migrate_tenant.yml` assembles `os_migrate_src_auth` / `os_migrate_dst_auth`
  from them. The os-migrate prelude then writes the `clouds.yaml`.
- **Project source.** AWX syncs the project from Git, so the commit under test
  must be pushed. CI uses `${{ github.sha }}`. The project's refspec also fetches
  `refs/pull/*`, so PR merge commits work, including for PRs from forks.
- **Pinned versions.** AWX Operator 2.19.1 (`awx-operator/kustomization.yml`) and
  `awx.awx` 24.6.1 (`requirements.yml`) should be bumped together. The operator's
  default `kube-rbac-proxy` image (`gcr.io/kubebuilder`) no longer exists and is
  remapped to `quay.io/brancz/kube-rbac-proxy`.

## Running locally (Linux, docker)

You need `docker`, `kind`, `kubectl`, `jq`, Go, and a Python env with
`requirements.txt`, `ansible-core` and `ansible-builder`. The collection must be
importable as `os_migrate.os_migrate`, as in CI:

```bash
# from a checkout at <dir>/ansible_collections/os_migrate/os_migrate
export ANSIBLE_COLLECTIONS_PATH=<dir>
make vendor-links
ansible-galaxy collection install plugins/modules/_vendor/openstack.cloud -p "$ANSIBLE_COLLECTIONS_PATH" --force
ansible-galaxy collection install -r tests/awx/requirements.yml -p "$ANSIBLE_COLLECTIONS_PATH"

tests/awx/deploy-awx.sh install
ansible-galaxy collection build --force
(cd aee && ansible-builder build --container-runtime docker --tag os-migrate-aee:ci)
kind load docker-image os-migrate-aee:ci --name osm-awx
tests/awx/deploy-awx.sh wait

# AWX syncs the project from Git: push your branch first.
GOSTACK_BIN=/path/to/fake-openstack \
OSM_AWX_SCM_URL=https://github.com/<you>/os-migrate \
OSM_AWX_SCM_BRANCH=<your-branch> \
  tests/awx/run-awx.sh
```

AWX is at <http://localhost:8080>. The user is `admin`, and
`tests/awx/deploy-awx.sh password` prints the password. Clean up with
`kind delete cluster --name osm-awx`.

On macOS (Docker Desktop) the kind network gateway is not reachable from the
host, so the default gostack setup does not work as is. Use a Linux machine or VM.
