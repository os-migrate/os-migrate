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
module: os_security_group_rules_info

short_description: Get security group rules info

extends_documentation_fragment: openstack

version_added: "2.9"

author: "OpenStack tenant migration tools (@os-migrate)"

description:
  - "List security group rules information"

options:
  name:
    description:
      - The name of the Security Group rule to get the info.
    required: true
    type: str
  filters:
    description:
      - Options for filtering the Security Group rules info.
    required: true
    type: dict
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
- name: Export security group rules into /opt/os-migrate/security_group_rules.yml
  os_security_group_rules_info:
    auth:
      auth_url: https://identity.example.com
      username: user
      password: password
      project_name: someproject
    name:  secgroup
'''

RETURN = '''
openstack_security_group_rules:
    description: has all the openstack information about the securty group rules
    returned: always, but can be null
    type: complex
    contains:
        id:
            description: Unique UUID.
            returned: success
            type: str
'''

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.openstack import openstack_full_argument_spec, openstack_cloud_from_module


def main():

    argument_spec = openstack_full_argument_spec(
        name=dict(required=False, default=None),
        filters=dict(required=False, type='dict', default=None)
    )
    # TODO: check the del
    # del argument_spec['cloud']

    module = AnsibleModule(argument_spec)
    sdk, cloud = openstack_cloud_from_module(module)
    try:
        security_group = cloud.list_security_groups(module.params['name'])

        # We need to get the security rules from the security group we queried
        security_group_rules = security_group['']
        module.exit_json(changed=False, openstack_security_group_rules=security_group_rules)

    except sdk.exceptions.OpenStackCloudException as e:
        module.fail_json(msg=str(e))


if __name__ == '__main__':
    main()
