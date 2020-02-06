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

**Note: We haven't released to Ansible Galaxy yet. Until we do, the
above command will not work.**

Alternatively, you can [install from source](install-from-source.md).


Clouds.yaml
-----------

OS-Migrate uses "named clouds" from `clouds.yml` file as the source of
OpenStack authentication credentials. The file should be created at
`$HOME/.config/openstack/clouds.yml`. Assuming we'll be migrating
content from a named cloud (tenant) we call `src` to one we call
`dst`, the `clouds.yml` file may look similar to:

```yaml
clouds:
  src:
    auth:
      auth_url: http://192.168.122.11/identity
      password: srcpassword
      project_domain_id: default
      project_name: src_project
      user_domain_id: default
      username: src_user
    identity_api_version: '3'
    region_name: RegionOne
    volume_api_version: '3'
  dst:
    auth:
      auth_url: http://192.168.122.11/identity
      password: dstpassword
      project_domain_id: default
      project_name: dst_project
      user_domain_id: default
      username: dst_user
    identity_api_version: '3'
    region_name: RegionOne
    volume_api_version: '3'
```

*Note: Due to a possible bug in some versions of Ansible or OpenStack
SDK, it seemed that the cloud names ("src", "dst" in the above
example) had to be alphanumeric only, and could not contain special
characters like hyphens or underscores. If Ansible reports that it
cannot find a named cloud in your clouds.yml file, try removing any
special characters from the names.*


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
# source and destination clouds, referring to names chosen in clouds.yml
os_migrate_src_cloud: src
os_migrate_dst_cloud: dst

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
the networks visible by the `src` named cloud (tenant). To view the
file:

```bash
cat $OS_MIGRATE_DATA/networks.yml
```

You can edit the YAML file, for example keep only a subset of networks
that you want to import into `dst` named cloud, and remove
others. When the contents are in desired state, import the networks:

```bash
ansible-playbook \
    -i $OS_MIGRATE/localhost_inventory.yml \
    -e @$HOME/os-migrate-vars.yml \
    $OS_MIGRATE/playbooks/import_networks.yml
```

This should create the desired networks in `dst` named cloud.
