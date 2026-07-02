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
module: update_workload_nbdkit_uris

short_description: Update workload file with multiple nbdkit URIs for multi-disk support

version_added: "1.0.0"

author: "OpenStack tenant migration tools (@os-migrate)"

description:
  - "Update a workload in the workloads.yml file with a list of nbdkit disk information"
  - "Supports multiple disks per instance (boot + ephemeral disks)"

options:
  path:
    description:
      - Path to workloads YAML file
    required: true
    type: str
  instance_id:
    description:
      - Instance ID to update
    required: true
    type: str
  nbdkit_disks:
    description:
      - List of disk information dictionaries
      - Each dict contains device, uri, port, size, bootable
    required: true
    type: list
    elements: dict
"""

EXAMPLES = r"""
- name: Update workload with multiple nbdkit URIs
  os_migrate.os_migrate.update_workload_nbdkit_uris:
    path: /data/workloads.yml
    instance_id: abc-123-def-456
    nbdkit_disks:
      - device: "/dev/vda"
        uri: "nbd://hypervisor-01:10809"
        port: 10809
        size: 10
        bootable: true
      - device: "/dev/vdb"
        uri: "nbd://hypervisor-01:10810"
        port: 10810
        size: 10
        bootable: false
"""

RETURN = r"""
"""

from ansible.module_utils.basic import AnsibleModule
try:
    import yaml
    HAS_YAML = True
except ImportError:
    HAS_YAML = False


def run_module():
    argument_spec = dict(
        path=dict(type="str", required=True),
        instance_id=dict(type="str", required=True),
        nbdkit_disks=dict(type="list", elements="dict", required=True),
    )

    result = dict(
        changed=False,
    )

    module = AnsibleModule(
        argument_spec=argument_spec,
    )

    path = module.params["path"]
    instance_id = module.params["instance_id"]
    nbdkit_disks = module.params["nbdkit_disks"]

    # Read the workloads file
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f)
    except Exception as e:
        module.fail_json(msg=f"Failed to read workloads file: {str(e)}")

    # Find and update the workload
    found = False
    for resource in data.get("resources", []):
        if resource.get("_info", {}).get("id") == instance_id:
            # Update migration_params with list of disks
            if "_migration_params" not in resource:
                resource["_migration_params"] = {}

            resource["_migration_params"]["nbdkit_disks"] = nbdkit_disks
            found = True
            result["changed"] = True
            break

    if not found:
        module.fail_json(msg=f"Workload with instance_id {instance_id} not found in {path}")

    # Write back the file
    try:
        with open(path, "w", encoding="utf-8") as f:
            yaml.dump(data, f, default_flow_style=False, sort_keys=False)
    except Exception as e:
        module.fail_json(msg=f"Failed to write workloads file: {str(e)}")

    module.exit_json(**result)


def main():
    run_module()


if __name__ == "__main__":
    main()
