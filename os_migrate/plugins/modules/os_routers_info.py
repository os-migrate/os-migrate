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
module: os_migrate.os_migrate.os_routers_info

short_description: Get routers info

version_added: "2.9"

description:
  - "List routers information"

options:
  cloud:
    description:
      - Named cloud to operate against.
    required: true
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

import openstack
from ansible.module_utils.basic import AnsibleModule


def main():
    module_args = dict(
        cloud=dict(type='str', required=True),
    )

    module = AnsibleModule(
        argument_spec=module_args,
        supports_check_mode=True,
    )

    try:
        conn = openstack.connect(cloud=module.params['cloud'])
        routers = list(map(lambda r: r.to_dict(), conn.network.routers()))
        module.exit_json(changed=False, openstack_routers=routers)

    except openstack.exceptions.OpenStackCloudException as e:
        module.fail_json(msg=str(e))


if __name__ == '__main__':
    main()
