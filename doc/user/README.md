OS-Migrate User Documentation
=============================

General notes:

* Run against testing/staging clouds first, verify that you are
  getting the expected results.

* OS-Migrate may not fit each use case out of the box. You can craft
  custom playbooks using the OS-Migrate collection pieces (roles and
  modules) as building blocks.

* Use the same version of OS-Migrate for export and import. We
  currently do not guarantee that data files are compatible across
  versions.


Prerequisites
-------------

* Ansible >= 2.9


Installation
------------

It is recommended to install releases from Ansible Galaxy.

```bash
ansible-galaxy collection install os_migrate.os_migrate
```

Alternatively, you can [install from source](install-from-source.md).



Usage example
-------------

Export the collection path to shorten commands:

```bash
export OS_MIGRATE="$HOME/.ansible/collections/ansible_collections/os_migrate/os_migrate"
```

In the out-of-the-box usage pattern, resources are exported into a
common directory, one file per resource type. (More advanced patterns
can be achieved by building custom playbooks using OS-Migrate
modules.) Create a directory where the migration files will be stored:

```
export OS_MIGRATE_DATA="$HOME/os-migrate-data"
mkdir -p "$OS_MIGRATE_DATA"
```

Put basic variables into `$HOME/os-migrate-vars.yml`:

```yaml
# authentication for source and destination clouds
os_migrate_src_auth:
  auth_url: http://192.168.122.85/identity
  password: password
  project_domain_id: default
  project_name: demo
  user_domain_id: default
  username: demo
os_migrate_src_region_name: RegionOne
os_migrate_dst_auth:
  auth_url: http://192.168.122.85/identity
  password: password
  project_domain_id: default
  project_name: alt_demo
  user_domain_id: default
  username: alt_demo
os_migrate_dst_region_name: RegionOne

# where to put exported resources
os_migrate_data_dir: /home/myuser/os-migrate-data
```

Now you should be ready to run OS-Migrate playbooks. To see the ones
available:

```bash
ls $OS_MIGRATE/playbooks
```

Now we can, for example, export networks:

```bash
ansible-playbook \
    -i $OS_MIGRATE/localhost_inventory.yml \
    -e @$HOME/os-migrate-vars.yml \
    $OS_MIGRATE/playbooks/export_networks.yml
```

Now you should have a `networks.yml` file with serialized data about
the networks visible using the `os_migrate_src_auth` credentials. To view the
file:

```bash
cat $OS_MIGRATE_DATA/networks.yml
```

You can edit the YAML file, for example keep only a subset of networks
that you want to import into cloud identified by `os_migrate_dst_auth`, and
remove others. When the contents are in desired state, import the networks:

```bash
ansible-playbook \
    -i $OS_MIGRATE/localhost_inventory.yml \
    -e @$HOME/os-migrate-vars.yml \
    $OS_MIGRATE/playbooks/import_networks.yml
```

This should create the desired networks in the cloud identified by
`os_migrate_dst_auth`.
