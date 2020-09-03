OS Migrate Walkthrough
======================

OS Migrate is a framework for OpenStack parallel cloud migration
(migrating content between OpenStack tenants which are not necessarily
in the same cloud). It’s a collection of Ansible playbooks that provide
the basic functionality, but may not fit each use case out of the box.
You can craft custom playbooks using the OS-Migrate collection pieces
(roles and modules) as building blocks.

Parallel cloud migration is a way to modernize an OpenStack deployment.
Instead of upgrading an OpenStack cluster in place, a second OpenStack
cluster is deployed alongside, and tenant content is migrated from the
original cluster to the new one. Parallel cloud migration is best suited
for environments which are due for a hardware refresh cycle. It may also
be performed without a hardware refresh, but extra hardware resources
are needed to bootstrap the new cluster. As hardware resources free up
in the original cluster, they can be gradually added to the new cluster.

OS-Migrate strictly uses the official OpenStack API and does not utilize
direct database access or other methods to export or import data. The
Ansible playbooks contained in OS-Migrate are idempotent. If a command
fails, you can retry with the same command.

.. figure:: https://raw.githubusercontent.com/os-migrate/os-migrate/main/media/walkthrough/2020-06-24-osp-migrate-fig1.png?sanitize=true
   :alt: OSP-OSP Migration Overview

   OSP-OSP Migration Overview

The migration is generally performed in this sequence:

-  prerequisites: authentication, parameter files,

-  pre-workload migration, which copies applicable resources into the
   destination cloud (e.g. networks, security groups, images) while
   workloads keep running in the source cloud,

-  workload migration, which stops usage of applicable resources in the
   source cloud and moves them into the destination cloud (VMs,
   volumes).

Prerequisites
-------------

Authentication
~~~~~~~~~~~~~~

Users are encouraged to use os-migrate using specific credentials for
each project/tenant, this means not using the admin user to execute the
resources migration. In the case that a user is required to use the
admin credentials this ``admin`` user needs to have access to the tenant
resources, otherwise you will hit an error similar to the following:

::

   keystoneauth1.exceptions.http.Unauthorized: The request you have made requires authentication. (HTTP 401)

To pass this error there are some options.

-  Add the ``admin`` user as a ``_member_`` of each project.

Depending on how many projects need to be migrated this approach seems
to be suboptimal as there are involved several configuration updates in
the projects that will need to be reverted after the migration
completes.

-  Create a group including the admin user and add the group to each
   project as member.

The difference with this approach is that once the migration is
completed, by removing the group, all the references in all the projects
will be removed automatically.

Parameter file
~~~~~~~~~~~~~~

Let’s create an ``os-migrate-vars.yml`` file with Ansible variables:

.. code:: yaml

   os_migrate_src_auth:
     auth_url: http://192.168.0.13.199/v3
     password: srcpassword
     project_domain_name: Default
     project_name: src
     user_domain_name: Default
     username: src
   os_migrate_src_region_name: regionOne
   os_migrate_dst_auth:
     auth_url: http://192.167.0.16:5000/v3
     password: dstpassword
     project_domain_name: Default
     project_name: dst
     user_domain_name: Default
     username: dst
   os_migrate_dst_region_name: regionOne

   os_migrate_data_dir: /home/migrator/os-migrate-data

The file contains the source and destination tenant credentials, a
directory on the migrator host (typically localhost) and a directory
where the exported data will be saved. There can also

A note about Keystone v2
^^^^^^^^^^^^^^^^^^^^^^^^

As depicted in content of the previously defined ``os-migrate-vars.yml``
file, the parameters ``os_migrate_src_auth`` and ``os_migrate_dst_auth``
refer to the usage of Keystone v3. In the case of a user needing to
execute a migration between tenants not supporting Keystone v3 the
following error will be raised:

::

   keystoneauth1.exceptions.discovery.DiscoveryFailure: Cannot use v2 authentication with domain scope

To fix this issue, the user must adjust their auth parameters in this
way:

.. code:: yaml

   os_migrate_src_auth:
     auth_url: http://192.168.0.13.199/v2.0
     password: srcpassword
     project_name: src
     username: src
   os_migrate_src_region_name: regionOne

Notice that the parameters ``project_domain_id`` and ``user_domain_id``
do not exist and the ``auth_url`` parameter points to the Keystone v2
endpoint.

Shortcuts
~~~~~~~~~

We will use the OS Migrate collection path and an ansible-playbook
command with the following arguments routinely, so let’s save them as
variables in the shell:

.. code:: bash

   export OSM_DIR=/home/migrator/.ansible/collections/ansible_collections/os_migrate/os_migrate
   export OSM_CMD="ansible-playbook -v -i $OSM_DIR/localhost_inventory.yml -e @os-migrate-vars.yml"

Pre-workload migration
----------------------

Workloads require the support of several resources in a given cloud to
operate properly. Some of these resources include networks, subnets,
routers, router interfaces, security groups, and security group rules.
The pre-workload migration process includes exporting these resources
from the source cloud onto the migrator machine, the option to edit the
resources if desired, and importing them into the destination cloud.

Exporting or importing resources is enabled by running the corresponding
playbook from OS Migrate. Let’s look at a concrete example. To export
the networks, run the “export_networks” playbook.

Export and import
~~~~~~~~~~~~~~~~~

To export the networks:

.. code:: bash

   $OSM_CMD $OSM_DIR/playbooks/export_networks.yml

This will create networks.yml file in the data directory, similar to
this:

.. code:: yaml

   os_migrate_version: 0.4.0
   resources:
     - _info:
         availability_zones:
           - nova
         created_at: '2020-04-07T14:08:30Z'
         id: a1eb31f6-2cdc-4896-b582-8950dafa34aa
         project_id: 2f444c71265048f7a9d21f81db6f21a4
         qos_policy_id: null
         revision_number: 3
         status: ACTIVE
         subnet_ids:
           - a5052e10-5e00-432b-a826-29695677aca0
           - d450ffd0-972e-4398-ab49-6ba9e29e2499
         updated_at: '2020-04-07T14:08:34Z'
       params:
         availability_zone_hints: []
         description: ''
         dns_domain: null
         is_admin_state_up: true
         is_default: null
         is_port_security_enabled: true
         is_router_external: false
         is_shared: false
         is_vlan_transparent: null
         mtu: 1450
         name: osm_net
         provider_network_type: null
         provider_physical_network: null
         provider_segmentation_id: null
         qos_policy_name: null
         segments: null
       type: openstack.network.Network

You may edit the file as needed and then run the “import_networks”
playbook to import the networks from this file into the destination
cloud:

.. code:: bash

   $OSM_CMD $OSM_DIR/playbooks/import_networks.yml

You can repeat this process for other resources like subnets, security
groups, security group rules, routers, router interfaces, images and
keypairs.

For a full list of available playbooks, run:

.. code:: bash

   ls $OSM_DIR/playbooks

.. figure:: https://raw.githubusercontent.com/os-migrate/os-migrate/main/media/walkthrough/2020-06-24-osp-migrate-fig2.png?raw=true
   :alt: Pre-workload Migration (data flow)

   Pre-workload Migration (data flow)

.. figure:: https://raw.githubusercontent.com/os-migrate/os-migrate/main/media/walkthrough/2020-06-24-osp-migrate-fig3.png?raw=true
   :alt: Pre-workload Migration (workflow)

   Pre-workload Migration (workflow)

Pre-workload migration recorded demo:

|Watch the video1|

Workload migration
------------------

Workload information is exported in a similar method to networks,
security groups, etc. as in the previous sections. Run the
“export_workloads” playbook, and edit the resulting workloads.yml as
desired:

.. code:: yaml

   os_migrate_version: 0.4.0
   resources:
   - _info:
       addresses:
         external_network:
         - OS-EXT-IPS-MAC:mac_addr: fa:16:3e:98:19:a0
           OS-EXT-IPS:type: fixed
           addr: 10.19.2.41
           version: 4
       flavor_id: a96b2815-3525-4eea-9ab4-14ba58e17835
       id: 0025f062-f684-4e02-9da2-3219e011ec74
       status: SHUTOFF
     params:
       flavor_name: m1.small
       name: migration-vm
       security_group_names:
       - testing123
       - default
     type: openstack.compute.Server

Note that this playbook only extracts metadata about instances in the
specified tenant - it does not download OpenStack volumes directly to
the migration data directory. Data transfer is handled by the
import_workloads playbook, and it is a fairly involved process to create
an environment where this playbook will run successfully. The next few
sections detail the process and some of the rationale for various design
choices.

Process summary
~~~~~~~~~~~~~~~

This flowchart illustrates the high-level migration workflow, from a
user’s point of view:

.. figure:: https://raw.githubusercontent.com/os-migrate/os-migrate/main/media/walkthrough/2020-06-24-osp-migrate-fig4.png?raw=true
   :alt: alt text

   alt text

The process involves the deployment of a “conversion host” on source and
destination clouds. A conversion host is an OpenStack instance which
will be used to transfer binary volume data from the source to the
destination cloud. Currently, CentOS 8 is expected to be the image from
which conversion hosts are created.

The following diagram helps explain the need for a conversion host VM:

.. figure:: https://raw.githubusercontent.com/os-migrate/os-migrate/main/media/walkthrough/2020-06-24-osp-migrate-fig5.png?raw=true
   :alt: Workload migration (data flow)

   Workload migration (data flow)

This shows that volumes on the source and destination clouds are removed
from their original VMs and attached to their respective UCH, and then
transferred over the network from the source UCH to the destination. The
tooling inside the UCH migrates one instance by automating these actions
on the source and destination clouds:

Source Cloud:

-  Detach volumes from the target instance to migrate

-  Attach the volumes to the source conversion host

-  Export the volumes as block devices and wait for destination
   conversion host to connect

Destination Cloud:

-  Create new volumes on the destination conversion host, one for each
   source volume

-  Attach the new volumes to the destination conversion host

-  Connect to the block devices exported by source conversion host, and
   copy the data to the new attached volumes

-  Detach the volumes from the destination conversion host

-  Create a new instance using the new volumes

This method keeps broad compatibility with the various flavors and
configurations of OpenStack using as much of an API-only approach as
possible, while allowing the use of libguestfs-based tooling to minimize
total data transfer.

Preparation
~~~~~~~~~~~

We’ll put additional parameters into ``os-migrate-vars.yml``:

.. code:: yaml

   os_migrate_conversion_external_network_name: public
   os_migrate_conversion_flavor_name: m1.large

These define the flavor and external network we want to use for our
conversion hosts.

By default the migration will use an image named ``os_migrate_conv`` for
conversion hosts. Make sure this image exists in Glance on both clouds.
Currently it should be a `CentOS 8 cloud
image <https://cloud.centos.org/centos/8/x86_64/images/CentOS-8-GenericCloud-8.2.2004-20200611.2.x86_64.qcow2>`__.

Conversion host deployment
~~~~~~~~~~~~~~~~~~~~~~~~~~

The conversion host deployment playbook creates the instances, installs
additional required packages, and authorizes the destination conversion
host to connect to the source conversion host for the actual data
transfer.

.. code:: bash

   $OSM_CMD $OSM_DIR/deploy_conversion_hosts.yml

Migration
~~~~~~~~~

Before migrating workloads, the destination cloud must have imported all
other resources (networks, security groups, etc.) or the migration will
fail. Matching named resources (including flavor names) must exist on
the destination before the instances are created.

If not already exported, export workload information with the
export_workloads playbook. Each instance listed in the resulting
workloads.yml will be migrated, except for the one matching the name
given to the source conversion host instance.

.. code:: bash

   $OSM_CMD $OSM_DIR/playbooks/export_workloads.yml

Then run the import_workloads playbook:

.. code:: bash

   $OSM_CMD $OSM_DIR/playbooks/import_workloads.yml

After a few minutes, results should start showing up looking something
like this:

::

   PLAY [migrator] ********************************************************************************************************************

   TASK [Gathering Facts] ********************************************************************************************************************
   [DEPRECATION WARNING]: Distribution fedora 31 on host localhost should use /usr/bin/python3, but is using /usr/bin/python for backward compatibility with prior Ansible releases. A future Ansible release will default to using the 
   discovered platform python for this host. See https://docs.ansible.com/ansible/2.9/reference_appendices/interpreter_discovery.html for more information. This feature will be removed in version 2.12. Deprecation warnings can be disabled by setting deprecation_warnings=False in ansible.cfg.
   ok: [localhost]

   TASK [import_workloads : validate loaded resources] ********************************************************************************************************************
   ok: [localhost]

   TASK [import_workloads : stop when errors found] ********************************************************************************************************************
   skipping: [localhost]

   TASK [import_workloads : read workloads resource file] ********************************************************************************************************************
   ok: [localhost]

   TASK [import_workloads : get source conversion host address] ********************************************************************************************************************
   ok: [localhost]

   TASK [import_workloads : check source conversion host status] ********************************************************************************************************************
   skipping: [localhost]

   TASK [import_workloads : get destination conversion host address] ********************************************************************************************************************
   ok: [localhost]

   TASK [import_workloads : check destination conversion host status] ********************************************************************************************************************
   skipping: [localhost]

   TASK [import_workloads : import workloads] ********************************************************************************************************************
   changed: [localhost] => (item={'_info': {'addresses': {'external_network': [{'OS-EXT-IPS-MAC:mac_addr': 'fa:16:3e:98:19:a0', 'OS-EXT-IPS:type': 'fixed', 'addr': '10.19.2.41', 'version': 4}]}, 'flavor_id': 'a96b2815-3525-4eea-9ab4-14ba58e17835', 'id': '0025f062-f684-4e02-9da2-3219e011ec74', 'status': 'SHUTOFF'}, 'params': {'flavor_name': 'm1.small', 'name': 'migration-vm', 'security_group_names': ['testing123', 'default']}, 'type': 'openstack.compute.Server'})
   changed: [localhost] => (item={'_info': {'addresses': {'external_network': [{'OS-EXT-IPS-MAC:mac_addr': 'fa:16:3e:d7:ae:16', 'OS-EXT-IPS:type': 'fixed', 'addr': '10.19.2.50', 'version': 4}]}, 'flavor_id': 'a96b2815-3525-4eea-9ab4-14ba58e17835', 'id': '0ca7b7d6-6679-4d46-99e5-866672d3e869', 'status': 'SHUTOFF'}, 'params': {'flavor_name': 'm1.small', 'name': 'second-migration-vm', 'security_group_names': ['default']}, 'type': 'openstack.compute.Server'})
   skipping: [localhost] => (item={'_info': {'addresses': {'external_network': [{'OS-EXT-IPS-MAC:mac_addr': 'fa:16:3e:14:12:46', 'OS-EXT-IPS:type': 'fixed', 'addr': '10.19.2.39', 'version': 4}]}, 'flavor_id': 'd0c1507e-92ce-48c5-9287-59c7b4e57467', 'id': '240d0194-ee2a-4708-b2c1-bde082887c59', 'status': 'ACTIVE'}, 'params': {'flavor_name': 'ims.conversion-host', 'name': 'source-conversion-host-2', 'security_group_names': ['default']}, 'type': 'openstack.compute.Server'}) 
   changed: [localhost] => (item={'_info': {'addresses': {'external_network': [{'OS-EXT-IPS-MAC:mac_addr': 'fa:16:3e:06:3e:c2', 'OS-EXT-IPS:type': 'fixed', 'addr': '10.19.2.44', 'version': 4}]}, 'flavor_id': 'a96b2815-3525-4eea-9ab4-14ba58e17835', 'id': '980e76f6-9143-475d-89f8-e708342b90e2', 'status': 'SHUTOFF'}, 'params': {'flavor_name': 'm1.small', 'name': 'fourth-migration-vm', 'security_group_names': ['default']}, 'type': 'openstack.compute.Server'})
   skipping: [localhost] => (item={'_info': {'addresses': {'external_network': [{'OS-EXT-IPS-MAC:mac_addr': 'fa:16:3e:3a:9b:72', 'OS-EXT-IPS:type': 'fixed', 'addr': '10.19.2.40', 'version': 4}]}, 'flavor_id': 'd0c1507e-92ce-48c5-9287-59c7b4e57467', 'id': 'ce4dda96-5d8e-4b67-aee2-9845cdc943fe', 'status': 'ACTIVE'}, 'params': {'flavor_name': 'ims.conversion-host', 'name': 'latestuci', 'security_group_names': ['default']}, 'type': 'openstack.compute.Server'})
   skipping: [localhost] => (item={'_info': {'addresses': {'external_network': [{'OS-EXT-IPS-MAC:mac_addr': 'fa:16:3e:3d:d1:25', 'OS-EXT-IPS:type': 'fixed', 'addr': '10.19.2.37', 'version': 4}]}, 'flavor_id': 'd0c1507e-92ce-48c5-9287-59c7b4e57467', 'id': 'a4e688e4-8d22-4469-9535-a8c867797c61', 'status': 'ACTIVE'}, 'params': {'flavor_name': 'ims.conversion-host', 'name': 'source-conversion-host-', 'security_group_names': ['default']}, 'type': 'openstack.compute.Server'}) 

   PLAY RECAP ********************************************************************************************************************
   localhost                  : ok=6    changed=1    unreachable=0    failed=0    skipped=3    rescued=0    ignored=0 

Any instance marked “changed” should be successfully migrated to the
destination cloud. Instances are “skipped” if they are still running, or
if they match the name or ID of the specified conversion host. If there
is already an instance on the destination matching the name of the
current instance, it will be marked “ok” and no extra work will be
performed:

::

   TASK [import_workloads : import workloads] ******************************************************************************************************************
   ok: [localhost] => (item={'_info': {'addresses': {'external_network': [{'OS-EXT-IPS-MAC:mac_addr': 'fa:16:3e:98:19:a0', 'OS-EXT-IPS:type': 'fixed', 'addr': '10.19.2.41', 'version': 4}]}, 'flavor_id': 'a96b2815-3525-4eea-9ab4-14ba58e17835', 'id': '0025f062-f684-4e02-9da2-3219e011ec74', 'status': 'SHUTOFF'}, 'params': {'flavor_name': 'm1.small', 'name': 'migration-vm', 'security_group_names': ['testing123', 'default']}, 'type': 'openstack.compute.Server'})

Workload migration recorded demo:

|Watch the video1|

|Watch the video2|

.. |Watch the video1| image:: https://img.youtube.com/vi/e7KXy5Hq4CM/maxresdefault.jpg
   :target: https://youtu.be/e7KXy5Hq4CMA
.. |Watch the video2| image:: https://img.youtube.com/vi/gEKvgIZqrQY/maxresdefault.jpg
   :target: https://youtu.be/gEKvgIZqrQY
