#!/usr/bin/python


from __future__ import absolute_import, division, print_function

__metaclass__ = type

ANSIBLE_METADATA = {
    "metadata_version": "1.1",
    "status": ["preview"],
    "supported_by": "community",
}

DOCUMENTATION = """
---
module: read_resources

short_description: Import OpenStack network

version_added: "2.9.0"

author: "OpenStack tenant migration tools (@os-migrate)"

description:
  - "Read an OS-Migrate YAML resources file structure"

options:
  path:
    description:
      - Resources YAML file to read.
    required: true
    type: str
"""

EXAMPLES = """
- name: Read resources from /opt/os-migrate/networks.yml
  os_migrate.os_migrate.read_resources:
    path: /opt/os-migrate/networks.yml
  register: read_networks

- name: Debug-print resources
  debug:
    msg: "{{ read_networks.resources }}"
"""

RETURN = """
resources:
    description: List of resources deserialized from YAML file
    returned: success
    type: complex
    contains:
        type:
            description: Type of the resource.
            returned: success
            type: str
        params:
            description: Resource parameters important for import.
            returned: success
            type: dict
        info:
            description: Additional resource information, not needed for import.
            returned: success
            type: dict
"""

from ansible.module_utils.basic import AnsibleModule

from ansible_collections.os_migrate.os_migrate.plugins.module_utils import filesystem


def run_module():
    module_args = dict(
        path=dict(type="str", required=True),
    )

    result = dict(
        # This module doesn't change anything.
        changed=False,
    )

    module = AnsibleModule(
        argument_spec=module_args,
        # Module doesn't change anything, we can let it run as-is in
        # check mode.
        supports_check_mode=True,
    )

    struct = filesystem.load_resources_file(module.params["path"])
    result["resources"] = struct["resources"]

    module.exit_json(**result)


def main():
    run_module()


if __name__ == "__main__":
    main()
