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
module: update_workload_nbdkit_uri

short_description: Update workload file with nbdkit URI

version_added: "1.0.0"

author: "OpenStack tenant migration tools (@os-migrate)"

description:
  - "Update a workload in the workloads.yml file with nbdkit socket URI and port"

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
  nbdkit_socket_uri:
    description:
      - NBDkit socket URI (e.g. nbd://host:port)
    required: true
    type: str
  nbdkit_port:
    description:
      - NBDkit port number
    required: true
    type: int
"""

EXAMPLES = r"""
- name: Update workload with nbdkit URI
  os_migrate.os_migrate.update_workload_nbdkit_uri:
    path: /data/workloads.yml
    instance_id: abc-123-def-456
    nbdkit_socket_uri: "nbd://hypervisor-01:10809"
    nbdkit_port: 10809
"""

RETURN = r"""
"""

from ansible.module_utils.basic import AnsibleModule
import yaml


def run_module():
    argument_spec = dict(
        path=dict(type="str", required=True),
        instance_id=dict(type="str", required=True),
        nbdkit_socket_uri=dict(type="str", required=True),
        nbdkit_port=dict(type="int", required=True),
    )

    result = dict(
        changed=False,
    )

    module = AnsibleModule(
        argument_spec=argument_spec,
    )

    path = module.params["path"]
    instance_id = module.params["instance_id"]
    nbdkit_socket_uri = module.params["nbdkit_socket_uri"]
    nbdkit_port = module.params["nbdkit_port"]

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
            # Update migration_params
            if "_migration_params" not in resource:
                resource["_migration_params"] = {}

            resource["_migration_params"]["nbdkit_socket_uri"] = nbdkit_socket_uri
            resource["_migration_params"]["nbdkit_port"] = nbdkit_port
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
