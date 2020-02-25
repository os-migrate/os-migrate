#!/usr/bin/python

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

ANSIBLE_METADATA = {
    'metadata_version': '1.1',
    'status': ['preview'],
    'supported_by': 'community'
}

DOCUMENTATION = '''
---
module: os_migrate.os_migrate.validate_resource_files

short_description: Import OpenStack network

version_added: "2.9"

description:
  - "Validate OS-Migrate YAML resource files."
  - "Unique resource naming is validated across all files provided."

options:
  paths:
    description:
      - Resources YAML files to read.
    required: true
'''

EXAMPLES = '''
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
'''

RETURN = '''
ok:
    description: Whether validation passed without errors
    returned: always
    type: boolean
resources:
    description: Errors found
    returned: always but can be empty
    type: list of str
'''

import openstack
from ansible.module_utils.basic import AnsibleModule

from ansible_collections.os_migrate.os_migrate.plugins.module_utils import filesystem
from ansible_collections.os_migrate.os_migrate.plugins.module_utils import validation


def run_module():
    module_args = dict(
        paths=dict(type='list', required=True),
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

    file_structs = []
    for path in module.params['paths']:
        file_structs.append(filesystem.load_resources_file(path))
    errors = validation.get_errors_in_file_structs(file_structs)

    result['ok'] = len(errors) == 0
    result['errors'] = errors

    module.exit_json(**result)


def main():
    run_module()


if __name__ == '__main__':
    main()
