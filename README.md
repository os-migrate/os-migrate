# OpenStack to Openstack/Openshift migration tooling
OS Migrate is an open source toolbox for parallel cloud migration
between OpenStack/Openshift clouds.

[![consistency-functional](https://github.com/os-migrate/os-migrate/actions/workflows/consistency-functional.yml/badge.svg?branch=main)](https://github.com/os-migrate/os-migrate/actions/workflows/consistency-functional.yml)
[![container-image-build](https://github.com/os-migrate/os-migrate/actions/workflows/container-image-build.yml/badge.svg?branch=main)](https://github.com/os-migrate/os-migrate/actions/workflows/container-image-build.yml)
[![docs-build](https://github.com/os-migrate/os-migrate/actions/workflows/docs-build.yml/badge.svg?branch=main)](https://github.com/os-migrate/os-migrate/actions/workflows/docs-build.yml)
<img src="https://img.shields.io/badge/Python-v3.7+-blue.svg">
<img src="https://img.shields.io/badge/Ansible-v2.9-blue.svg">
<a href="https://opensource.org/licenses/Apache-2.0">
  <img src="https://img.shields.io/badge/License-Apache2.0-blue.svg">
</a>

## Description

Parallel cloud migration is a way to
modernize an OpenStack/Openshift deployment. Instead of upgrading an OpenStack
cluster in place, a second OpenStack cluster is deployed alongside,
and tenant content is migrated from the original cluster to the new
one. As hardware resources free up in the original cluster, they can
be gradually added to the new cluster.

OS Migrate provides a framework for exporting and importing resources
between two clouds. It's a collection of Ansible playbooks that
provide the basic functionality, but may not fit each use case out of
the box. You can craft custom playbooks using the OS Migrate
collection pieces (roles and modules) as building blocks.

OS Migrate strictly uses the official OpenStack API and does not
utilize direct database access or other methods to export or import
data. The Ansible playbooks contained in OS Migrate are idempotent. If
a command fails, you can retry with the same command.


## Requirements

This section must list the required minimum versions of Ansible and Python, and any Python or external collection dependencies. Include additional information on other prerequisite tasks needed, if applicable.


## Installation

Before using this collection, you need to install it with the Ansible Galaxy command-line tool:

```
ansible-galaxy collection install os_migrate.os_migrate
```

You can also include it in a requirements.yml file and install it with ansible-galaxy collection install -r requirements.yml, using the format:


```yaml
collections:
  - name: os_migrate.os_migrate
```

Note that if you install any collections from Ansible Galaxy, they will not be upgraded automatically when you upgrade the Ansible package.
To upgrade the collection to the latest available version, run the following command:

```
ansible-galaxy collection install os_migrate.os_migrate --upgrade
```

You can also install a specific version of the collection, for example, if you need to downgrade when something is broken in the latest version (please report an issue in this repository). Use the following syntax to install version 1.0.0:

```
ansible-galaxy collection install os_migrate.os_migrate:==1.0.0
```

See [using Ansible collections](https://docs.ansible.com/ansible/devel/user_guide/collections_using.html) for more details.


In addition to the above boilerplate, this section should include any additional details specific to your collection, and what to expect at each step and after installation. Be sure to include any information that supports the installation process, such as information about authentication and credentialing.

## Overview

With OS Migrate you can test a migration from one existing openstack deployment to another existing openstack deployment. You can also test with a single existing openstack deployment migrating from one project to another. These docs cover the testing of a single existing openstack deployment migrating from one project to another scenario.

The concepts and prerequisites are the same for other deployments.

### Prerequisites for Migration

- Source environment credentials
- Destination environment credentials
- Existing images in both source and destination environments
- Flavors
- Public network
- Space requirements
    - 2 images totalling 1.25 GB
    - 1 volume totalling 1 GB in source environment
    - 2 volumes totalling 6 GB in destination environment
    - 2 VMs totalling 35 GB disk usage in each environment


## Workflow

Below are the steps required to satisfy the above requirements and run a migration end-to-end in a test environment, migrating resources from one project to another.


### Create source environment and destination environment projects and users
```yaml
# Create the src user in the default domain with password 'redhat'
openstack user create --domain default --password redhat src

# Create the src project
openstack project create --domain default src

# Assign src user a 'member' role in the src project
openstack role add \
--user src --user-domain default \
--project src --project-domain default member

# Confirm role assignment was successful
openstack role assignment list --project src

# Create the dst user in the default domain with password 'redhat'
openstack user create --domain default --password redhat dst

# Create the dst project
openstack project create --domain default dst

# Assign dst user a 'member' role in the src project
openstack role add \
--user dst --user-domain default \
--project dst --project-domain default member

# Confirm role assignment was successful
openstack role assignment list --project dst
```


### Create images
```yaml
# Download images
wget https://cloud.centos.org/centos/9-stream/x86_64/images/CentOS-Stream-GenericCloud-9-20230704.1.x86_64.qcow2
wget http://download.cirros-cloud.net/0.4.0/cirros-0.4.0-x86_64-disk.img

# Create images in glance from these downloads
openstack image create --public --disk-format qcow2 --file \
    CentOS-Stream-GenericCloud-9-20230704.1.x86_64.qcow2 CentOS-Stream-GenericCloud-9-20230704.1.x86_64.qcow2
openstack image create --public --disk-format raw --file cirros-0.4.0-x86_64-disk.img cirros-0.4.0-x86_64-disk.img
```


### Create flavors
```yaml
openstack flavor create --public \
--ram 256 --disk 5 --vcpus 1 --rxtx-factor 1 m1.xtiny

openstack flavor create --public \
--ram 2048 --disk 30 --vcpus 2 --rxtx-factor 1 m1.large
```


### Create public network
If your OpenStack environment doesn’t have a public network created yet, you’ll need to create one. The parameters below should work if you’re deploying your OpenStack environment with Infrared Virsh plugin. If you deployed using something else, you may need to adjust the parameters.

```yaml
openstack network create \
     --mtu 1500 \
     --external \
     --provider-network-type flat \
     --provider-physical-network datacentre \
     public

openstack subnet create \
    --network public \
    --gateway 10.0.0.1 \
    --subnet-range 10.0.0.0/24 \
    --allocation-pool start=10.0.0.150,end=10.0.0.190 \
    public
```


## Running a migration
Copy the above config to file custom-config.yaml in the local directory of your local os-migrate source.

```yaml
os_migrate_src_auth:
  auth_url: http://10.0.0.131:5000/v3
  password: redhat
  project_domain_name: Default
  project_name: src
  user_domain_name: Default
  username: src
os_migrate_src_region_name: regionOne
os_migrate_dst_auth:
  auth_url: http://10.0.0.131:5000/v3
  password: redhat
  project_domain_name: Default
  project_name: dst
  user_domain_name: Default
  username: dst
os_migrate_dst_region_name: regionOne

os_migrate_data_dir: /root/os_migrate/local/migrate-data

os_migrate_conversion_host_ssh_user: cloud-user
os_migrate_src_conversion_external_network_name: nova
os_migrate_dst_conversion_external_network_name: nova
os_migrate_conversion_flavor_name: m1.large
os_migrate_conversion_image_name: CentOS-Stream-GenericCloud-8-20220913.0.x86_64.qcow2

os_migrate_src_osm_server_flavor: m1.xtiny
os_migrate_src_osm_server_image: cirros-0.4.0-x86_64-disk.img
os_migrate_src_osm_router_external_network: nova

os_migrate_src_validate_certs: False
os_migrate_dst_validate_certs: False

os_migrate_src_release: 16
os_migrate_dst_release: 16

os_migrate_src_conversion_net_mtu: 1400
os_migrate_dst_conversion_net_mtu: 1400
```

Run the migration suite using the above steps.
```yaml
OS_MIGRATE_E2E_TEST_ARGS='-e @/root/os_migrate/local/custom-config.yaml' ./toolbox/run make test-e2e-tenant
```


## Related Information

For more useful information see; optional tags/variables to add to run a migration [end-to-end](https://os-migrate.github.io/os-migrate/devel/dev-env-setup.html#optional-tags-to-pass-to-e2e-tests), demo on using os-migrate [here](https://www.youtube.com/watch?v=1AQKTcZi85A) and streamlining [VM Migrations](https://www.redhat.com/en/events/webinar/stream-os-migrate) on Red Hat OpenStack.


## Contributing
As an open source project, OS Migrate welcomes contributions from the community at large. The following guide provides information on how to add a new role to the project and where additional testing or documentation artifacts should be added. This isn’t an exhaustive reference and is a living document subject to change as needed when the project formalizes any practice or pattern. See the
[OS Migrate developer documentation](https://os-migrate.github.io/os-migrate/devel/README.html).


## Support

Please report any issues into the
[GitHub issue tracker](https://github.com/os-migrate/os-migrate/issues).


## Release Notes and Roadmap

See the [Official Changelog](https://os-migrate.github.io/os-migrate/changelog.html).
