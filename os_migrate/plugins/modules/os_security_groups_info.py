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
module: os_migrate.os_migrate.os_security_groups_info

short_description: Get security groups info

version_added: "2.9"

description:
  - "List security groups information"

options:
  cloud:
    description:
      - Named cloud to operate against.
    required: true
  path:
    description:
      - Resources YAML file to where security groups will be serialized.
      - In case the resource file already exists, it must match the
        os-migrate version.
      - In case the resource of same type and name exists in the file,
        it will be replaced.
    required: true
'''

EXAMPLES = '''
- name: Export security groups into /opt/os-migrate/security_groups.yml
  os_security_groups_info:
    auth:
      auth_url: https://identity.example.com
      username: user
      password: password
      project_name: someproject
    name:  secgroup
'''

RETURN = '''
openstack_security_groups:
    description: has all the openstack information about the securty groups
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
    module = AnsibleModule(argument_spec)
    sdk, cloud = openstack_cloud_from_module(module)
    try:
        security_groups = cloud.list_security_groups(module.params['name'])
        module.exit_json(changed=False, openstack_security_groups=security_groups)

    except sdk.exceptions.OpenStackCloudException as e:
        module.fail_json(msg=str(e))


if __name__ == '__main__':
    main()
