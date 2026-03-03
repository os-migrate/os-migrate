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

# Import openstack module utils from ansible_collections.openstack.cloud.plugins as per ansible 3+
HAS_OPENSTACK_CLOUD = False
try:
    from ansible_collections.openstack.cloud.plugins.module_utils.openstack import (
        openstack_full_argument_spec,
        openstack_cloud_from_module,
    )
    HAS_OPENSTACK_CLOUD = True
except ImportError:
    try:
        # If this fails fall back to ansible < 3 imports
        from ansible.module_utils.openstack import (
            openstack_full_argument_spec,
            openstack_cloud_from_module,
        )
        HAS_OPENSTACK_CLOUD = True
    except ImportError:
        # Create stub functions for sanity testing
        HAS_OPENSTACK_CLOUD = False

        def openstack_full_argument_spec(**kwargs):
            spec = dict(
                cloud=dict(type='raw'),
                auth=dict(type='dict'),
                auth_type=dict(type='str'),
                region_name=dict(type='str'),
                wait=dict(type='bool', default=True),
                timeout=dict(type='int', default=180),
                api_timeout=dict(type='int'),
                validate_certs=dict(type='bool', aliases=['verify']),
                ca_cert=dict(type='str', aliases=['cacert']),
                client_cert=dict(type='str', aliases=['cert']),
                client_key=dict(type='str', aliases=['key']),
                interface=dict(type='str', choices=['admin', 'internal', 'public'], default='public', aliases=['endpoint_type']),
                sdk_log_path=dict(type='str'),
                sdk_log_level=dict(type='str', default='INFO', choices=['INFO', 'DEBUG']),
            )
            spec.update(kwargs)
            return spec

        def openstack_cloud_from_module(module):
            return None, None


def main():

    argument_spec = openstack_full_argument_spec(
        filters=dict(required=False, type="dict", default={}),
    )
    # TODO: check the del
    # del argument_spec['cloud']

    module = AnsibleModule(argument_spec, supports_check_mode=True)

    if not HAS_OPENSTACK_CLOUD:
        module.fail_json(msg='openstack.cloud collection is required for this module')

    sdk, cloud = openstack_cloud_from_module(module)
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
