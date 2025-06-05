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
module: os_role_assignments_info

short_description: Get role assignments info

extends_documentation_fragment: openstack

version_added: "2.9.0"

author: "OpenStack tenant migration tools (@os-migrate)"

description:
  - "List role assignments information"

options:
  assignee_types:
    description:
      - List of assignee types to filter the assignments. Supported
         types 'user', 'group'. None means don't filter anything.
    required: false
    type: str
  scope_types:
    description:
      - List of scope types to filter the assignments. Supported
         types 'project', 'system', 'domain'. None means don't filter anything.
    required: false
    type: str
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

EXAMPLES = """
- os_role_assignments_info:
    cloud: srccloud
"""

RETURN = """
openstack_role_assignments:
    description: information about the role assignments
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
        assignee_types=dict(required=False, type="list", default=None),
        scope_types=dict(required=False, type="list", default=None),
    )

    module = AnsibleModule(
        argument_spec=argument_spec,
        supports_check_mode=True,
    )

    assignee_types = module.params["assignee_types"]
    scope_types = module.params["scope_types"]
    try:
        sdk, conn = openstack_cloud_from_module(module)
        role_assignment_dicts = map(
            lambda r: r.to_dict(), conn.identity.role_assignments(include_names=True)
        )

        def assignee_filter(role_assignment_dict):
            if assignee_types is None:
                return True
            for assignee_type in assignee_types:
                if role_assignment_dict.get(assignee_type) is not None:
                    return True
            return False

        def scope_filter(role_assignment_dict):
            if scope_types is None:
                return True
            for scope_type in scope_types:
                if role_assignment_dict["scope"].get(scope_type) is not None:
                    return True
            return False

        filtered_role_assignments = filter(assignee_filter, role_assignment_dicts)
        filtered_role_assignments = filter(scope_filter, filtered_role_assignments)
        module.exit_json(
            changed=False, openstack_role_assignments=list(filtered_role_assignments)
        )

    except sdk.exceptions.OpenStackCloudException as e:
        module.fail_json(msg=str(e))


if __name__ == "__main__":
    main()
