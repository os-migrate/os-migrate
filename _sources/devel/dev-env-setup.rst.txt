Development Environment Setup
=============================

Prerequisites
-------------

-  Local clone of the os-migrate git repo from
   https://github.com/os-migrate/os-migrate
-  `Podman <https://podman.io/>`_ and `Buildah <https://buildah.io/>`_
   for running rootless development environment containers.

Development environment
-----------------------

Build a container image with tools to be used for building and testing
the project:

::

   make toolbox-build

All further ``make`` commands etc. should be run from a container
using this image. You can start a bash shell within the development
container like so:

::

   ./toolbox/run

Alternatively, you can run each development-related command in an
ephemeral container using the provided wrapper, if you provide the
command as parameter(s) to the `./toolbox/run` script:

::

   ./toolbox/run echo "Hello from os-migrate toolbox."

Sanity and unit tests
---------------------

You can run sanity tests this way:

::

   ./toolbox/run make test-sanity

And unit tests this way:

::

   ./toolbox/run make test-unit

To run sanity tests and then unit tests together, a shorthand target
“test-fast” can be used:

::

   ./toolbox/run make test-fast

Vagrant for functional tests
----------------------------

To run functional tests, you’ll need to connect to OpenStack cloud(s)
where tenant resources can be managed. As a developer, the easiest way
is to run a local virtualized all-in-one OpenStack cloud. OS Migrate has
Vagrant+Devstack setup for this purpose.

If you have Vagrant-libvirt installed on your machine, you can use it
directly, but OS Migrate tooling does not assume that, the customary
way is to run it via the OS Migrate toolbox container. Special
``vagrant-run`` wrapper scripts are provided for this purpose.

Note that the Vagrant container cannot run in rootless mode since it
controls libvirt. When the wrapper script is first run, it will copy
the rootless `os-migrate-toolbox` image into the system's (`root`
user's) container images automatically.

Launch the Vagrant-capable containerized shell:

::

   ./toolbox/vagrant-run

Within that shell, run the script which brings up Vagrant+Devstack:

::

   # we are already in toolbox/vagrant dir when we launch vagrant-run
   ./vagrant-up

Assuming the creation succeeded, it is now recommended to take a
snapshot of the environment so you can revert it back into a known-good
state later:

::

   ./vagrant-snapshot-create

**Important:** the life of the Vagrant VM is tied to the life of the
container started by ``./toolbox/vagrant-run``. That means you should
keep the shell open, and run functional tests via ``./toolbox/run make
test-func`` from a different terminal. If you close the
``vagrant-run``, the Vagrant VM will get killed. If that happens, you
can start it again and use ``./vagrant-snapshot-revert`` to revive
the VM.

If you need to revert the VM at any time, run:

::

   ./vagrant-snapshot-revert

When you’re done developing, halt Vagrant and close ``vagrant-run``
shell:

::

   ./vagrant-halt
   exit

When you want to develop again, you will be able to reuse the
snapshotted Vagrant environment:

::

   ./toolbox/vagrant-run
   ./vagrant-snapshot-revert

To destroy the Vagrant VM, e.g. when you want to recreate it from
scratch later, run:

::

   ./vagrant-destroy

Running functional tests
------------------------

Functional tests expect ``tests/func/auth_tenant.yml`` and
``tests/func/auth_admin.yml`` files to exist and contain
``os_migrate_src_auth`` and ``os_migrate_dst_auth`` variables
with credentials for connecting to OpenStack cloud(s). The tests
will connect to wherever these auth parameters point and
create/delete resources there.

Run a make target which will set up the aforementioned
``tests/func/auth_tenant.yml`` file to connect to your
Vagrant+Devstack instance:

::

   ./toolbox/run make test-setup-vagrant-devstack

Run a make target which will set up the aforementioned
``tests/func/auth_admin.yml`` file to connect to your
Vagrant+Devstack instance:

::

   ./toolbox/run make test-setup-vagrant-devstack-admin

Finally, run the functional tests:

::

   ./toolbox/run make test-func

To run functional tests for just the resource you’re working on, run
e.g.:

::

   OS_MIGRATE_FUNC_TEST_ARGS='--tags test_network,test_subnet' ./toolbox/run make test-func

To explore imported resources, skip the after-test cleanup of resources,
e.g.:

::

   OS_MIGRATE_FUNC_TEST_ARGS='--tags test_network,test_subnet --skip-tags test_clean_after' ./toolbox/run make test-func

Running e2e tests
-----------------

OS Migrate also has a suite of end to end, e2e, tests which tests a migration from one existing openstack deployment
to another existing openstack deployment.

You can also test with a single existing openstack deployment migrating from one project to another.

These docs cover the testing of a single existing openstack deployment migrating from one project to another scenario.

The concepts and prerequisites are the same for other deployments.

Prerequisites for e2e test
^^^^^^^^^^^^^^^^^^^^^^^^^^

-  Source environment credentials

-  Destination environment credentials

-  Existing images in both source and destination environments

-  Flavors

-  Public network

-  Space requirements

   -  2 images totalling 1.25 GB

   -  1 volume totalling 1 GB in source environment

   -  2 volumes totalling 6 GB in destination environment

   -  2 VMs totalling 35 GB disk usage in each environment

Below are the steps required to satisfy the above requirements and run e2e tests in a test environment, migrating
resources from one project to another.

Create source environment and destination environment projects and users
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. code-block::

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

Create images
^^^^^^^^^^^^^

.. code-block::

    # Download images
    wget https://cloud.centos.org/centos/8-stream/x86_64/images/CentOS-Stream-GenericCloud-8-20210603.0.x86_64.qcow2
    wget http://download.cirros-cloud.net/0.4.0/cirros-0.4.0-x86_64-disk.img

    # Create images in glance from these downloads
    openstack image create --public --disk-format qcow2 --file \
        CentOS-Stream-GenericCloud-8-20210603.0.x86_64.qcow2 CentOS-Stream-GenericCloud-8-20210603.0.x86_64.qcow2
    openstack image create --public --disk-format raw --file cirros-0.4.0-x86_64-disk.img cirros-0.4.0-x86_64-disk.img

Create flavors
^^^^^^^^^^^^^^

.. code-block::

    openstack flavor create --public \
    --ram 256 --disk 5 --vcpus 1 --rxtx-factor 1 m1.xtiny

    openstack flavor create --public \
    --ram 2048 --disk 30 --vcpus 2 --rxtx-factor 1 m1.large

Create public network
^^^^^^^^^^^^^^^^^^^^^

If your OpenStack environment doesn't have a public network created
yet, you'll need to create one. The parameters below should work if
you're deploying your OpenStack environment with Infrared Virsh
plugin. If you deployed using something else, you may need to adjust
the parameters.

.. code-block::

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

Sample e2e config yaml using the above prerequisites
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Also see https://github.com/os-migrate/os-migrate/blob/main/tests/e2e/tenant/scenario_variables.yml

Auth URLs and network names will change based on your environment.

.. code-block::

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

    os_migrate_conversion_host_ssh_user: centos
    os_migrate_src_conversion_external_network_name: nova
    os_migrate_dst_conversion_external_network_name: nova
    os_migrate_conversion_flavor_name: m1.large
    os_migrate_conversion_image_name: CentOS-Stream-GenericCloud-8-20210603.0.x86_64.qcow2

    os_migrate_src_osm_server_flavor: m1.xtiny
    os_migrate_src_osm_server_image: cirros-0.4.0-x86_64-disk.img
    os_migrate_src_osm_router_external_network: nova

    os_migrate_src_validate_certs: False
    os_migrate_dst_validate_certs: False

    os_migrate_src_release: 16
    os_migrate_dst_release: 16

    os_migrate_src_conversion_net_mtu: 1400
    os_migrate_dst_conversion_net_mtu: 1400

Run e2e test using the OS Migrate toolbox and the above config
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Copy the above config to file `custom-config.yaml` in the `local` directory of your local `os-migrate` source.

Run the full test suite using the above config.

.. code-block::

   OS_MIGRATE_E2E_TEST_ARGS='-e @/root/os_migrate/local/custom-config.yaml' ./toolbox/run make test-e2e-tenant


Expected output from successful e2e test run
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. code-block::

    PLAY RECAP ********************************************************************************************************
    localhost                  : ok=318  changed=110  unreachable=0    failed=0    skipped=27   rescued=0    ignored=0
    os_migrate_conv_dst        : ok=12   changed=5    unreachable=0    failed=0    skipped=3    rescued=0    ignored=0
    os_migrate_conv_src        : ok=12   changed=5    unreachable=0    failed=0    skipped=3    rescued=0    ignored=0

    Wednesday 21 July 2021  09:59:17 +0000 (0:00:03.419)       0:29:17.016 ********
    ===============================================================================
    os_migrate.os_migrate.conversion_host_content : update all packages --------------------------------------- 435.56s
    os_migrate.os_migrate.import_workloads : transfer volumes to destination ---------------------------------- 101.72s
    os_migrate.os_migrate.import_workloads : expose source volumes --------------------------------------------- 66.67s
    os_migrate.os_migrate.conversion_host_content : install content -------------------------------------------- 62.35s
    os_migrate.os_migrate.import_workloads : transfer volumes to destination ----------------------------------- 58.75s
    os_migrate.os_migrate.import_workloads : clean up in the source cloud after migration ---------------------- 27.40s
    os_migrate.os_migrate.import_workloads : expose source volumes --------------------------------------------- 27.30s
    Create osm_server ------------------------------------------------------------------------------------------ 24.71s
    create osm_image ------------------------------------------------------------------------------------------- 23.86s
    os_migrate.os_migrate.export_images : export image blobs --------------------------------------------------- 23.80s
    os_migrate.os_migrate.import_images : import images -------------------------------------------------------- 23.69s
    os_migrate.os_migrate.import_workloads : create destination instance --------------------------------------- 23.30s
    os_migrate.os_migrate.import_workloads : create destination instance --------------------------------------- 21.93s
    Create osm_server ------------------------------------------------------------------------------------------ 21.61s
    os_migrate.os_migrate.import_workloads : clean up in the source cloud after migration ---------------------- 21.16s
    os_migrate.os_migrate.conversion_host : create os_migrate conversion host ---------------------------------- 20.03s
    Remove osm_server ------------------------------------------------------------------------------------------ 19.01s
    os_migrate.os_migrate.conversion_host : create os_migrate conversion host ---------------------------------- 18.23s
    Shutdown osm_server ---------------------------------------------------------------------------------------- 18.14s
    Shutdown osm_server ---------------------------------------------------------------------------------------- 17.88s

Optional tags to pass to e2e tests
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
There are a set of tags that can be used to filter which tasks to run during test.

- test_clean_before
- test_workload
- test_image_workload_boot_copy
- test_image_workload_boot_nocopy
- test_image_workload_boot_copy_clean
- test_clean_before
- test_pre_workload

Optional playbook variable
^^^^^^^^^^^^^^^^^^^^^^^^^^
There is also an optional variable `test_clean_conversion_hosts_after` which can be set to `false` if you do not wish
to clean up conversion hosts after test is complete.

Environment variables
^^^^^^^^^^^^^^^^^^^^^
The following environment variables can be used when running e2e tests.

- `OS_MIGRATE_E2E_TEST_ARGS`: All of the above tags and playbook variables can be set using the
  `OS_MIGRATE_E2E_TEST_ARGS` environment variable. This variable is also used to pass in the playbook custom config
  file. eg:

      `OS_MIGRATE_E2E_TEST_ARGS='-e @/root/os_migrate/local/custom-config.yaml \
      --tags test_clean_before,test_workload --skip-tags test_clean_after -e test_clean_conversion_hosts_after=false'`

- `ROOT_DIR`: Absolute directory path to OS Migrate source. When not set the default when run using OS Migrate developer
  toolbox this is set to `/root/os_migrate`.
- `OS_MIGRATE`: Absolute directory path to the OS Migrate ansible collection. When not set the default when run using
  os-migrate developer toolbox this is set to `/root/.ansible/collections/ansible_collections/os_migrate/os_migrate`.



