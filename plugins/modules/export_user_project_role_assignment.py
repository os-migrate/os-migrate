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
module: export_user_project_role_assignment
short_description: Export OpenStack Identity Role Assignment
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
  path:
    description:
      - Resources YAML file to where project will be serialized.
      - In case the resource file already exists, it must match the
        os-migrate version.
      - In case the resource of same type and name exists in the file,
        it will be replaced.
    required: true
    type: str
  user_id:
    description:
      - ID of a user to export the role assignment for.
    required: true
    type: str
  project_id:
    description:
      - ID of a project to export the role assignment for.
    required: true
    type: str
  role_id:
    description:
      - ID of a role to export the role assignment for.
    required: true
    type: str
  availability_zone:
    description:
      - Availability zone.
    required: false
    type: str
  cloud:
    description:
      - Cloud resource from clouds.yml
      - Required if 'auth' param not used.
    required: false
    type: raw
"""

EXAMPLES = r"""
- name: Export my_project into /opt/os-migrate/user_project_role_assignment.yml
  os_migrate.os_migrate.export_user_project_role_assignment:
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

from ansible_collections.os_migrate.os_migrate.plugins.module_utils import filesystem
from ansible_collections.os_migrate.os_migrate.plugins.module_utils import (
    user_project_role_assignment,
)


def run_module():
    argument_spec = openstack_full_argument_spec(
        path=dict(type="str", required=True),
        user_id=dict(type="str", required=True),
        project_id=dict(type="str", required=True),
        role_id=dict(type="str", required=True),
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

    user_id = module.params["user_id"]
    project_id = module.params["project_id"]
    role_id = module.params["role_id"]

    sdk, conn = openstack_cloud_from_module(module)
    sdk_assignments = list(
        conn.identity.role_assignments(
            user_id=user_id, scope_project_id=project_id, role_id=role_id
        )
    )
    if len(sdk_assignments) == 0:
        module.fail_json(
            msg=f"No role assignment found for user {user_id}, project {project_id}, role {role_id}."
        )
    elif len(sdk_assignments) > 1:
        module.fail_json(
            msg=f"Multiple role assignments found for user {user_id}, project {project_id}, role {role_id}."
        )
    else:
        sdk_assignment = sdk_assignments[0]

        data = user_project_role_assignment.UserProjectRoleAssignment.from_sdk(
            conn, sdk_assignment
        )

        result["changed"] = filesystem.write_or_replace_resource(
            module.params["path"], data
        )

    module.exit_json(**result)


def main():
    run_module()


if __name__ == "__main__":
    main()
