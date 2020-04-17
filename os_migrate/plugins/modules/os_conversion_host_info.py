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
module: os_server_address

short_description: Get IP address of OpenStack conversion host instance

extends_documentation_fragment: openstack

version_added: "2.9"

author: "OpenStack tenant migration tools (@os-migrate)"

description:
  - "Get OpenStack instance IP address, intended for migration conversion host instances only. Verifies that the instance is up."

options:
  server_id:
    description:
      - ID of server to inspect
    required: true
    type: str
  auth:
    description:
      - Dictionary with parameters for chosen auth type.
    required: true
    type: dict
  auth_type:
    description:
      - Auth type plugin for OpenStack. Can be omitted if using password authentication.
    required: false
    type: str
  region_name:
    description:
      - OpenStack region name. Can be omitted if using default region.
    required: false
    type: str
  availability_zone:
    description:
      - Availability zone.
    required: false
    type: str
  cloud:
    description:
      - Ignored. Present for backwards compatibility.
    required: false
    type: raw
'''

EXAMPLES = '''
- os_migrate.os_migrate.os_server_address:
    auth:
        auth_url: https://dest-osp:13000/v3
        username: migrate
        password: migrate
        project_domain_id: default
        project_name: migration-destination
        user_domain_id: default
    server_id: 2d2afe57-ace5-4187-8fca-5f10f9059ba1
  register: os_dst_conversion_host_address
'''

RETURN = '''
openstack_server_address:
    description: IP address of an instance
    returned: only when instance is in ACTIVE state
    type: complex
    contains:
        address:
            description: IP (v4) address of the specified instance
'''

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.openstack \
    import openstack_full_argument_spec, openstack_cloud_from_module


def main():
    argument_spec = openstack_full_argument_spec(
        server_id=dict(type='str', required=True)
    )

    module = AnsibleModule(
        argument_spec=argument_spec,
        supports_check_mode=True,
    )

    srv_id = module.params['server_id']

    try:
        sdk, conn = openstack_cloud_from_module(module)
        server = conn.get_server_by_id(srv_id)
        if server.status != 'ACTIVE':
            msg = 'Conversion host ' + server.name + ' is not in state ACTIVE!'
            module.fail_json(msg=msg)
        module.exit_json(changed=False, address=server.accessIPv4)

    except sdk.exceptions.OpenStackCloudException as e:
        module.fail_json(msg=str(e))


if __name__ == '__main__':
    main()
