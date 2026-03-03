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
module: os_routers_info

short_description: Get routers info

extends_documentation_fragment:
  - os_migrate.os_migrate.openstack

version_added: "2.9.0"

author: "OpenStack tenant migration tools (@os-migrate)"

description:
  - "List routers information"

options:
  filters:
    description:
      - Options for filtering the Routers info.
    required: false
    type: dict
    default: {}
  auth:
    description:
      - Required if 'cloud' parameter not used.
    required: false
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
  cloud:
    description:
      - Cloud configuration from clouds.yml
      - Required if 'auth' param not used.
    required: false
    type: raw
"""

EXAMPLES = r"""
- os_routers_info:
    cloud: srccloud
"""

RETURN = r"""
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

    module = AnsibleModule(
        argument_spec=argument_spec,
        supports_check_mode=True,
    )

    if not HAS_OPENSTACK_CLOUD:
        module.fail_json(msg='openstack.cloud collection is required for this module')

    try:
        sdk, conn = openstack_cloud_from_module(module)
        routers = list(
            map(lambda r: r.to_dict(), conn.network.routers(**module.params["filters"]))
        )
        module.exit_json(changed=False, openstack_routers=routers)

    except sdk.exceptions.OpenStackCloudException as e:
        module.fail_json(msg=str(e))


if __name__ == "__main__":
    main()
