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
module: import_user_project_role_assignment
short_description: Import OpenStack Identity Role Assignment
extends_documentation_fragment:
  - os_migrate.os_migrate.openstack
version_added: "2.9"
author: "OpenStack tenant migration tools (@os-migrate)"
description:
  - "Export OpenStack Identity Role Assignment definition into an OS-Migrate YAML"
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
  filters:
    description:
      - Options for filtering existing resources to be looked up, e.g. by role assignment.
    required: false
    type: dict
  availability_zone:
    description:
      - Availability zone.
    required: false
    type: str
  cloud:
    description:
      - Cloud resource from clouds.yml.
      - Required if 'auth' param not used.
    required: false
    type: raw
"""

EXAMPLES = r"""
- name: Import my_project into /opt/os-migrate/user_project_role_assignment.yml
  os_migrate.os_migrate.import_user_project_role_assignment:
    cloud: source_cloud
    path: /opt/os-migrate/user_project_role_assignment.yml
    name: my_project
"""

RETURN = r"""
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

from ansible_collections.os_migrate.os_migrate.plugins.module_utils import (
    user_project_role_assignment,
)


def run_module():
    argument_spec = openstack_full_argument_spec(
        data=dict(type="dict", required=True),
        filters=dict(type="dict", required=False, default={}),
    )
    # TODO: check the del
    # del argument_spec['cloud']

    result = dict(
        changed=False,
    )

    module = AnsibleModule(
        argument_spec=argument_spec,
        # TODO: Consider check mode. We'd fetch the resource and check
        # if the file representation matches it.
        # supports_check_mode=True,
    )

    sdk, conn = openstack_cloud_from_module(module)
    ser_assignment = user_project_role_assignment.UserProjectRoleAssignment.from_data(
        module.params["data"]
    )

    result["changed"] = ser_assignment.create_or_update(conn, module.params["filters"])

    module.exit_json(**result)


def main():
    run_module()


if __name__ == "__main__":
    main()
