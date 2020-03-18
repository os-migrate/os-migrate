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
module: os_routers_info

short_description: Get routers info

extends_documentation_fragment: openstack

version_added: "2.9"

author: "OpenStack tenant migration tools (@os-migrate)"

description:
  - "List routers information"

options:
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
- os_routers_info:
    cloud: srccloud
'''

RETURN = '''
openstack_routers:
    description: information about the routers
    returned: always, but can be empty
    type: complex
    contains:
        id:
            description: Unique UUID.
            returned: success
            type: str
        name:
            description: Router name.
            returned: success
            type: str
'''

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.openstack \
    import openstack_full_argument_spec, openstack_cloud_from_module


def main():
    argument_spec = openstack_full_argument_spec()

    module = AnsibleModule(
        argument_spec=argument_spec,
        supports_check_mode=True,
    )

    try:
        sdk, conn = openstack_cloud_from_module(module)
        routers = list(map(lambda r: r.to_dict(), conn.network.routers()))
        module.exit_json(changed=False, openstack_routers=routers)

    except sdk.exceptions.OpenStackCloudException as e:
        module.fail_json(msg=str(e))


if __name__ == '__main__':
    main()
