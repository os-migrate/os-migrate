NBD Source Migration
====================

Introduction
------------

The NBD source migration feature allows workload migration to consume volume data directly from the source hypervisor using the NBD protocol and qemu-nbd. Instead of routing data through a source conversion host, the migration connects directly to the compute node where the instance lives, reducing network hops and improving transfer performance.

This approach is useful when you have direct network access to your hypervisors and want to bypass the traditional conversion host architecture. The feature supports multiple disks per instance, including boot volumes and ephemeral disks.

How it works
------------

Traditional migration path::

    Source VM -> Source Conv Host (SSH) -> Destination Conv Host -> Destination Volumes

NBD direct path::

    Source VM (on Hypervisor) -> qemu-nbd on Hypervisor -> Destination Conv Host -> Destination Volumes

The data flows directly from the hypervisor to the destination conversion host using nbdcopy, eliminating the intermediate source conversion host step.

Enabling the feature
--------------------

To enable NBD direct mode for a workload, add the ``use_nbdkit_direct`` flag to the workload definition in your ``workloads.yml`` file:

.. code-block:: yaml

    - _info:
        id: abc-123-def-456
        hypervisor_hostname: compute-01.example.com
        status: SHUTOFF
      params:
        name: my-instance
      _migration_params:
        use_nbdkit_direct: true

You can enable this flag manually after running export_workloads, or set it in your workload definitions before export.

The import_from_hypervisor role
--------------------------------

The import_from_hypervisor role spawns qemu-nbd processes on the source hypervisors. This role should be run after exporting workloads and before importing them.

Running the role
~~~~~~~~~~~~~~~~

.. code-block:: bash

    ansible-playbook -i inventory.yml \
      os_migrate.os_migrate.playbooks.import_from_hypervisor.yml

Or from the playbooks directory:

.. code-block:: bash

    ansible-playbook -i inventory.yml playbooks/import_from_hypervisor.yml

What the role does
~~~~~~~~~~~~~~~~~~

For each workload marked with ``use_nbdkit_direct: true``, the role:

1. Verifies the instance is in SHUTOFF state
2. Connects to the hypervisor via SSH
3. Discovers all disk files in ``/var/lib/nova/instances/<uuid>/`` (disk, disk.eph0, disk.eph1, etc.)
4. Inspects each disk with qemu-img info to detect format and size
5. Spawns one qemu-nbd process per disk on sequential ports starting from 10809
6. Updates the workloads.yml file with the nbdkit_disks list

The nbdkit_disks field
~~~~~~~~~~~~~~~~~~~~~~

After running import_from_hypervisor, your workload definition will be updated with a ``nbdkit_disks`` list:

.. code-block:: yaml

    - _info:
        id: abc-123-def-456
        hypervisor_hostname: compute-01.example.com
      params:
        name: my-instance
      _migration_params:
        use_nbdkit_direct: true
        nbdkit_disks:
          - device: "/dev/vda"
            uri: "nbd://compute-01.example.com:10809"
            port: 10809
            size: 10
            bootable: true
          - device: "/dev/vdb"
            uri: "nbd://compute-01.example.com:10810"
            port: 10810
            size: 10
            bootable: false

Each entry in the list represents one disk with:

* ``device``: The device name on the destination instance
* ``uri``: The NBD URI to connect to
* ``port``: The qemu-nbd port number
* ``size``: Disk size in GB (detected from qemu-img info)
* ``bootable``: Whether this is the boot disk

Role configuration
~~~~~~~~~~~~~~~~~~

You can customize the role behavior using these variables in your playbook or inventory:

.. code-block:: yaml

    # Base port for qemu-nbd (increments for each disk)
    os_migrate_nbdkit_port: 10809

    # Protocol: 'tcp' or 'ssh'
    os_migrate_nbdkit_protocol: tcp

    # SSH user (only for ssh protocol)
    os_migrate_nbdkit_ssh_user: stack

    # Read-only mode (recommended to keep true)
    os_migrate_nbdkit_readonly: true

    # Nova instances directory on hypervisor
    os_migrate_nbdkit_nova_instances_dir: /var/lib/nova/instances

Manual hypervisor preparation
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

If you want to skip the import_from_hypervisor role and prepare the hypervisor manually, follow these steps:

1. Find the instance UUID and locate its directory on the hypervisor::

    /var/lib/nova/instances/<uuid>/
    ├── disk          # Boot disk
    ├── disk.eph0     # Ephemeral disk 0 (if present)
    ├── disk.eph1     # Ephemeral disk 1 (if present)
    └── disk.info     # Metadata file (not used)

2. Inspect the disk format:

.. code-block:: bash

    qemu-img info /var/lib/nova/instances/<uuid>/disk

3. Start qemu-nbd for each disk:

.. code-block:: bash

    # Boot disk on port 10809
    sudo qemu-nbd -f qcow2 -p 10809 --read-only \
      /var/lib/nova/instances/<uuid>/disk

    # First ephemeral disk on port 10810 (if present)
    sudo qemu-nbd -f qcow2 -p 10810 --read-only \
      /var/lib/nova/instances/<uuid>/disk.eph0

4. Manually update your workloads.yml with the nbdkit_disks structure shown above.

The import_workloads role with NBD direct mode
-----------------------------------------------

When import_workloads detects ``use_nbdkit_direct: true`` in a workload definition, it changes the migration workflow.

Standard workflow (use_nbdkit_direct: false)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

1. Attach source volumes to source conversion host
2. Spawn nbdkit on source conversion host
3. Create SSH tunnel from destination to source conversion host
4. Transfer data using qemu-img convert
5. Detach source volumes

NBD direct workflow (use_nbdkit_direct: true)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

1. Skip source conversion host operations entirely
2. Read nbdkit_disks from workload definition
3. Create destination volumes (one per disk in nbdkit_disks)
4. Attach destination volumes to destination conversion host
5. Use nbdcopy to transfer each disk from the NBD URI to its destination volume
6. Detach destination volumes
7. Create instance with the new volumes

The key differences:

* No source conversion host needed
* Direct connection from hypervisor to destination
* Uses nbdcopy instead of qemu-img convert
* Handles multiple disks independently

Transfer process
~~~~~~~~~~~~~~~~

Each disk is transferred in parallel using nbdcopy:

.. code-block:: bash

    # Boot disk transfer
    nbdcopy nbd://compute-01:10809 /dev/vde --progress

    # Ephemeral disk transfer
    nbdcopy nbd://compute-01:10810 /dev/vdf --progress

Progress is tracked in the state file for each workload, allowing you to monitor the transfer.

Security considerations
-----------------------

When using NBD direct mode:

1. Ensure the instance is SHUTOFF before starting qemu-nbd. The role enforces this check.

2. Always use read-only mode for qemu-nbd to prevent accidental writes to source disks:

   .. code-block:: yaml

       os_migrate_nbdkit_readonly: true

3. Consider using SSH protocol for encrypted transfers over untrusted networks:

   .. code-block:: yaml

       os_migrate_nbdkit_protocol: ssh
       os_migrate_nbdkit_ssh_user: stack

4. Ensure firewall rules allow the destination conversion host to connect to ports 10809+ on your hypervisors.

5. qemu-nbd binds to all interfaces by default. Use firewall rules to restrict access to only the destination conversion host.

Complete workflow example
-------------------------

Here's a complete migration using NBD direct mode:

.. code-block:: bash

    # 1. Export workloads from source (standard)
    ansible-playbook -i inventory.yml \
      os_migrate.os_migrate.export_workloads.yml

    # 2. Edit workloads.yml to enable NBD direct mode
    # Add use_nbdkit_direct: true to _migration_params

    # 3. Spawn qemu-nbd on hypervisors
    ansible-playbook -i inventory.yml \
      playbooks/import_from_hypervisor.yml

    # 4. Verify the nbdkit_disks were added to workloads.yml
    cat os-migrate-data/workloads.yml

    # 5. Import workloads (uses NBD URIs)
    ansible-playbook -i inventory.yml \
      os_migrate.os_migrate.import_workloads.yml

Troubleshooting
---------------

qemu-nbd process not starting
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Check if the port is already in use:

.. code-block:: bash

    sudo netstat -tlnp | grep 10809

The role automatically stops existing qemu-nbd processes on the same port before starting new ones.

Cannot connect to NBD from destination
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Test connectivity:

.. code-block:: bash

    # From destination conversion host
    qemu-img info nbd://hypervisor-hostname:10809

Check firewall rules on the hypervisor and verify qemu-nbd is listening:

.. code-block:: bash

    # On hypervisor
    sudo netstat -tlnp | grep qemu-nbd

Instance not in SHUTOFF state
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The role requires instances to be SHUTOFF before spawning qemu-nbd. Either manually shut down the instance or use:

.. code-block:: yaml

    os_migrate_workload_stop_before_migration: true

Missing hypervisor_hostname
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The hypervisor_hostname field is populated by export_workloads. Make sure you've run the export step and that the source cloud API provides this information.

Limitations
-----------

* Only works with instances in SHUTOFF state
* Requires direct network connectivity from destination conversion host to source hypervisors
* qemu-nbd processes remain running after migration (you may want to clean them up manually)
* Currently uses variable names with "nbdkit" prefix for backward compatibility, even though the implementation uses qemu-nbd
