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
module: os_security_groups_info

short_description: Get security groups info

extends_documentation_fragment:
  - os_migrate.os_migrate.openstack

version_added: "2.9.0"

author: "OpenStack tenant migration tools (@os-migrate)"

description:
  - "List security groups information"

options:
  filters:
    description:
      - Options for filtering the Security Group info.
    required: false
    type: dict
    default: {}
  cloud:
    description:
      - Cloud resource from clouds.yml file
    required: false
    type: raw
"""

EXAMPLES = r"""
- name: Export security groups into /opt/os-migrate/security_groups.yml
  os_security_groups_info:
    auth:
      auth_url: https://identity.example.com
      username: user
      password: password
      project_name: someproject
    name: secgroup
"""

RETURN = r"""
openstack_security_groups:
    description: has all the openstack information about the securty groups
    returned: always, but can be null
    type: complex
    contains:
        id:
            description: Unique UUID.
            returned: success
            type: str
"""

from ansible.module_utils.basic import AnsibleModule

from ansible_collections.os_migrate.os_migrate.plugins.module_utils import os_auth


def main():

    argument_spec = os_auth.openstack_full_argument_spec(
        filters=dict(required=False, type="dict", default={}),
    )
    # TODO: check the del
    # del argument_spec['cloud']

    module = AnsibleModule(argument_spec, supports_check_mode=True)
    cloud = os_auth.get_connection(module)
    try:
        security_groups = list(
            map(
                lambda r: r.to_dict(),
                cloud.network.security_groups(**module.params["filters"]),
            )
        )
        module.exit_json(changed=False, openstack_security_groups=security_groups)

    except sdk.exceptions.OpenStackCloudException as e:
        module.fail_json(msg=str(e))


if __name__ == "__main__":
    main()
