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
module: validate_resource_files

short_description: Import OpenStack network

version_added: "2.9.0"

author: "OpenStack tenant migration tools (@os-migrate)"

description:
  - "Validate OS-Migrate YAML resource files."
  - "Unique resource naming is validated across all files provided."

options:
  paths:
    description:
      - Resources YAML files to read.
    required: true
    type: list
    elements: str
"""

EXAMPLES = """
- name: Read resources from /opt/os-migrate/networks.yml
  os_migrate.os_migrate.validate_resource_files:
    paths:
      - /opt/os-migrate/networks.yml
      - /opt/os-migrate/security_groups.yml
      - /opt/os-migrate/security_group_rules.yml
      - /opt/os-migrate/subnets.yml
  register: validation_results

- name: Debug-print validation results
  debug:
    var: validation_results
"""

RETURN = """
ok:
    description: Whether validation passed without errors
    returned: always
    type: str
errors:
    description: Errors found
    returned: always but can be empty
    type: dict
"""

from ansible.module_utils.basic import AnsibleModule

from ansible_collections.os_migrate.os_migrate.plugins.module_utils import filesystem
from ansible_collections.os_migrate.os_migrate.plugins.module_utils import validation


def run_module():
    module_args = dict(
        paths=dict(type="list", required=True, elements="str"),
    )

    result = dict(
        # This module doesn't change anything.
        changed=False,
        ok="True",
        errors=[],
    )

    module = AnsibleModule(
        argument_spec=module_args,
        # Module doesn't change anything, we can let it run as-is in
        # check mode.
        supports_check_mode=True,
    )

    file_structs = []
    for path in module.params["paths"]:
        file_structs.append(filesystem.load_resources_file(path))
    errors = validation.get_errors_in_file_structs(file_structs)

    if len(errors) == 0:
        result["ok"] = "True"
    else:
        result["ok"] = "False"
    result["errors"] = errors

    module.exit_json(**result)


def main():
    run_module()


if __name__ == "__main__":
    main()
