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
module: auth_info
short_description: Fetch information about authenticated user/project
description:
  - "Fetch information about authenticated user/project"
version_added: "2.9.0"
extends_documentation_fragment:
  - os_migrate.os_migrate.openstack
author: "OpenStack tenant migration tools (@os-migrate)"
options:
  auth:
    description:
      - Required if 'cloud' param not used.
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
      - Cloud config from clouds.yml resource
      - Required if 'auth' param not used
    required: false
    type: raw
requirements:
  - openstacksdk
seealso: []
notes: []
"""

EXAMPLES = r"""
- name: Fetch info about currently authenticated user/project
  os_migrate.os_migrate.auth_info:
  register: _auth_info
"""

RETURN = r"""
auth_info:
    description: information about current authenticated user/project
    returned: always
    type: complex
    contains:
        project_id:
            description: Currently authenticated project ID.
            returned: success
            type: str
        user_id:
            description: Currently authenticated user ID.
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


def run_module():
    argument_spec = openstack_full_argument_spec()
    # TODO: check the del
    # del argument_spec['cloud']

    result = dict(
        changed=False,
    )

    module = AnsibleModule(
        argument_spec=argument_spec,
        supports_check_mode=True,
    )

    sdk, conn = openstack_cloud_from_module(module)
    result["auth_info"] = {
        "project_id": conn.current_project_id,
        "user_id": conn.current_user_id,
    }

    module.exit_json(**result)


def main():
    run_module()


if __name__ == "__main__":
    main()
