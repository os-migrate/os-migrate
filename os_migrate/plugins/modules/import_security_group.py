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
module: os_migrate.os_migrate.import_security_group
short_description: Import OpenStack security group
version_added: "2.9"
description:
  - "Import OpenStack security group from an OS-Migrate YAML structure"
options:
  cloud:
    description:
      - Named cloud to operate against.
    required: true
  data:
    description:
      - Data structure with security group parameters as loaded from OS-Migrate YAML file.
    required: true
'''

EXAMPLES = '''
- name: Import mysecgroup into /opt/os-migrate/security_groups.yml
  os_migrate.os_migrate.import_security_group:
    cloud: source_cloud
    data:
      - type: openstack.security_group
        params:
          name: my_secgroup
'''

RETURN = '''
'''

import openstack
from ansible.module_utils.basic import AnsibleModule

from ansible_collections.os_migrate.os_migrate.plugins.module_utils import network


def run_module():
    module_args = dict(
        cloud=dict(type='str', required=True),
        data=dict(type='dict', required=True),
    )

    result = dict(
        changed=False,
    )

    module = AnsibleModule(
        argument_spec=module_args,
        # TODO: Consider check mode. We'd fetch the resource and check
        # if the file representation matches it.
        # supports_check_mode=True,
    )

    conn = openstack.connect(cloud=module.params['cloud'])
    ser_sec = module.params['data']
    sec_params = network.security_group_sdk_params(ser_sec)
    existing_secgroup = conn.network.find_security_group(sec_params['name'])
    if existing_secgroup:
        if network.security_group_needs_update(existing_secgroup, ser_sec):
            conn.network.update_security_group(sec_params['name'], **sec_params)
            result['changed'] = True
        # else: pass -- nothing to update
    else:
        conn.network.create_security_group(**sec_params)
        result['changed'] = True

    module.exit_json(**result)


def main():
    run_module()


if __name__ == '__main__':
    main()
