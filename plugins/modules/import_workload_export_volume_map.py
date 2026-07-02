#!/usr/bin/python

from __future__ import absolute_import, division, print_function

__metaclass__ = type

ANSIBLE_METADATA = {
    "metadata_version": "1.1",
    "status": ["preview"],
    "supported_by": "community",
}

DOCUMENTATION = r"""
---
module: import_workload_export_volume_map

short_description: Create volume map from workload data for nbdkit direct mode

extends_documentation_fragment:
  - os_migrate.os_migrate.openstack

version_added: "1.0.0"

author: "OpenStack tenant migration tools (@os-migrate)"

description:
  - "Create a volume_map structure from workload data without using source conversion host"
  - "Handles both volume-backed and ephemeral-backed instances"

options:
  auth:
    description:
      - Required if 'cloud' param not used.
    required: false
    type: dict
  auth_type:
    description:
      - Auth type plugin for OpenStack cloud.
    required: false
    type: str
  cloud:
    description:
      - Cloud resource from clouds.yml
    required: false
    type: raw
  validate_certs:
    description:
      - Validate HTTPS certificates when logging in to OpenStack.
    required: false
    type: bool
  data:
    description:
      - Data structure with server parameters as loaded from OS-Migrate workloads YAML file.
    required: true
    type: dict
"""

EXAMPLES = r"""
- name: Create volume map for nbdkit direct mode
  os_migrate.os_migrate.import_workload_export_volume_map:
    cloud: src
    data: "{{ workload_item }}"
  register: volume_info
"""

RETURN = r"""
transfer_uuid:
  description: UUID to identify this transfer
  returned: Always
  type: str
  sample: 9b8a64b3-c976-4103-b34e-995e4ab9f57b
volume_map:
  description:
    - Mapping of source volume devices to volume information
  returned: Always
  type: dict
  sample:
    "/dev/vda":
      bootable: true
      dest_dev: null
      dest_id: null
      image_id: null
      name: "my-vm-boot"
      port: null
      progress: 0.0
      size: 10
      snap_id: null
      source_dev: null
      source_id: "volume-uuid-123"
      url: null
"""

from ansible.module_utils.basic import AnsibleModule
from ansible_collections.os_migrate.os_migrate.plugins.module_utils import os_auth
from ansible_collections.os_migrate.os_migrate.plugins.module_utils import server
import uuid


def build_volume_map_from_volumes(ser_server):
    """Build volume map from attached volumes."""
    volume_map = {}
    volumes = ser_server.params().get("volumes", [])

    for vol_data in volumes:
        vol_info = vol_data.get("_info", {})
        volume_id = vol_info.get("id")

        # Get device path from attachments
        attachments = vol_info.get("attachments", [])
        if attachments:
            device = attachments[0].get("device", "/dev/vda")
        else:
            device = "/dev/vda" if vol_info.get("bootable") else "/dev/vdb"

        volume_map[device] = {
            "bootable": vol_info.get("bootable", False),
            "dest_dev": None,
            "dest_id": None,
            "image_id": None,
            "name": vol_data.get("params", {}).get("name", f"volume-{volume_id}"),
            "port": None,
            "progress": 0.0,
            "size": vol_info.get("size", 0),
            "snap_id": None,
            "source_dev": None,
            "source_id": volume_id,
            "url": None,
        }

    return volume_map


def build_volume_map_from_ephemeral(conn, ser_server):
    """Build volume map for ephemeral disk instances."""
    volume_map = {}
    params = ser_server.params()
    info = ser_server.info()

    # Get flavor to determine ephemeral disk size
    flavor_ref = params.get("flavor_ref", {})
    flavor_name = flavor_ref.get("name")

    if not flavor_name:
        return volume_map

    # Fetch flavor details
    try:
        flavor = conn.compute.find_flavor(flavor_name, ignore_missing=False)
    except Exception:
        # If flavor not found, try using flavor_id from info
        flavor_id = info.get("flavor_id")
        if flavor_id:
            flavor = conn.compute.get_flavor(flavor_id)
        else:
            return volume_map

    # Calculate ephemeral disks (ESTIMATION - actual sizes come from qemu-img info)
    # Nova typically creates ephemeral disks in 10GB chunks
    # This is a fallback when nbdkit_disks is not available
    ephemeral_gb = getattr(flavor, "ephemeral", 0)
    num_ephemeral_disks = ephemeral_gb // 10 if ephemeral_gb > 0 else 0

    if ephemeral_gb > 0:
        # Create boot volume entry
        boot_size = getattr(flavor, "disk", 10)  # Root disk size

        volume_map["/dev/vda"] = {
            "bootable": True,
            "dest_dev": None,
            "dest_id": None,
            "image_id": None,
            "name": f"{params.get('name', 'vm')}-boot",
            "port": None,
            "progress": 0.0,
            "size": boot_size,
            "snap_id": None,
            "source_dev": None,
            "source_id": None,  # Ephemeral, no source volume ID
            "url": None,
        }

        # Create separate ephemeral volume entries (DO NOT merge sizes!)
        # ESTIMATION: Assumes 10GB per disk (actual sizes from qemu-img via nbdkit_disks)
        for i in range(num_ephemeral_disks):
            # Device names: /dev/vdb, /dev/vdc, /dev/vdd, etc.
            device = f"/dev/vd{chr(ord('b') + i)}"
            volume_map[device] = {
                "bootable": False,
                "dest_dev": None,
                "dest_id": None,
                "image_id": None,
                "name": f"{params.get('name', 'vm')}-ephemeral{i}",
                "port": None,
                "progress": 0.0,
                "size": 10,  # ESTIMATE: 10GB per disk (overridden by nbdkit_disks)
                "snap_id": None,
                "source_dev": None,
                "source_id": None,
                "url": None,
            }
    else:
        # Just boot disk, no ephemeral
        boot_size = getattr(flavor, "disk", 10)

        volume_map["/dev/vda"] = {
            "bootable": True,
            "dest_dev": None,
            "dest_id": None,
            "image_id": None,
            "name": f"{params.get('name', 'vm')}-boot",
            "port": None,
            "progress": 0.0,
            "size": boot_size,
            "snap_id": None,
            "source_dev": None,
            "source_id": None,
            "url": None,
        }

    return volume_map


def build_volume_map_from_nbdkit_disks(ser_server):
    """Build volume map from nbdkit_disks (uses actual sizes from qemu-img info)."""
    volume_map = {}
    migration_params = ser_server.migration_params()
    nbdkit_disks = migration_params.get("nbdkit_disks", [])
    params = ser_server.params()

    for disk in nbdkit_disks:
        device = disk["device"]
        size = disk["size"]  # Actual size from qemu-img info
        bootable = disk.get("bootable", False)

        volume_map[device] = {
            "bootable": bootable,
            "dest_dev": None,
            "dest_id": None,
            "image_id": None,
            "name": f"{params.get('name', 'vm')}-{device.split('/')[-1]}",
            "port": disk.get("port"),
            "progress": 0.0,
            "size": size,  # Real size from hypervisor
            "snap_id": None,
            "source_dev": None,
            "source_id": None,
            "url": disk.get("uri"),
        }

    return volume_map


def run_module():
    argument_spec = os_auth.openstack_full_argument_spec(
        data=dict(type="dict", required=True),
    )

    result = dict(
        changed=False,
    )

    module = AnsibleModule(
        argument_spec=argument_spec,
    )

    conn = os_auth.get_connection(module)
    ser_server = server.Server.from_data(module.params["data"])
    params = ser_server.params()
    migration_params = ser_server.migration_params()

    # Generate transfer UUID
    transfer_uuid = str(uuid.uuid4())

    # Build volume map
    # Priority: nbdkit_disks (actual sizes) > volumes > ephemeral (flavor-based)
    nbdkit_disks = migration_params.get("nbdkit_disks")
    volumes = params.get("volumes", [])

    if nbdkit_disks:
        # Use actual disk sizes from nbdkit_disks (populated by import_from_hypervisor)
        volume_map = build_volume_map_from_nbdkit_disks(ser_server)
    elif volumes:
        # Instance has attached volumes
        volume_map = build_volume_map_from_volumes(ser_server)
    else:
        # Instance uses ephemeral disks - estimate from flavor
        volume_map = build_volume_map_from_ephemeral(conn, ser_server)

    result["transfer_uuid"] = transfer_uuid
    result["volume_map"] = volume_map

    module.exit_json(**result)


def main():
    run_module()


if __name__ == "__main__":
    main()
