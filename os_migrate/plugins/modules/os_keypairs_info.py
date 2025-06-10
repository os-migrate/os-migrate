#!/usr/bin/python


from __future__ import absolute_import, division, print_function

__metaclass__ = type

ANSIBLE_METADATA = {
    "metadata_version": "1.1",
    "status": ["preview"],
    "supported_by": "community",
}

DOCUMENTATION = """
---
module: os_keypairs_info

short_description: Get keypairs info

extends_documentation_fragment: openstack

version_added: "2.9.0"

author: "OpenStack tenant migration tools (@os-migrate)"

description:
  - "List keypairs information"

options:
  filters:
    description:
      - Options for filtering the Keypairs info.
    required: false
    type: dict
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
  availability_zone:
    description:
      - Availability zone.
    required: false
    type: str
  cloud:
    description:
      - Cloud from clouds.yaml to use.
      - Required if 'auth' parameter is not used.
    required: false
    type: raw
"""

EXAMPLES = """
- os_keypairs_info:
    cloud: srccloud
"""

RETURN = """
openstack_keypairs:
    description: information about the keypairs
    returned: always, but can be empty
    type: complex
    contains:
        id:
            description: Unique UUID.
            returned: success
            type: str
        name:
            description: Keypair name.
            returned: success
            type: str
"""

from ansible.module_utils.basic import AnsibleModule

# Import openstack module utils from ansible_collections.openstack.cloud.plugins as per ansible 3+
try:
    from ansible_collections.openstack.cloud.plugins.module_utils.openstack import (
        openstack_full_argument_spec,
        openstack_cloud_from_module,
    )
except ImportError:
    # If this fails fall back to ansible < 3 imports
    from ansible.module_utils.openstack import (
        openstack_full_argument_spec,
        openstack_cloud_from_module,
    )


def main():
    argument_spec = openstack_full_argument_spec(
        filters=dict(required=False, type="dict", default={}),
    )

    module = AnsibleModule(
        argument_spec=argument_spec,
        supports_check_mode=True,
    )

    try:
        sdk, conn = openstack_cloud_from_module(module)
        keypairs = list(
            map(
                lambda r: r.to_dict(), conn.compute.keypairs(**module.params["filters"])
            )
        )
        module.exit_json(changed=False, openstack_keypairs=keypairs)

    except sdk.exceptions.OpenStackCloudException as e:
        module.fail_json(msg=str(e))


if __name__ == "__main__":
    main()
