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
module: export_router

short_description: Export OpenStack router

extends_documentation_fragment:
  - os_migrate.os_migrate.openstack

version_added: "2.9.0"

author: "OpenStack tenant migration tools (@os-migrate)"

description:
  - "Export OpenStack router definition into an OS-Migrate YAML"

options:
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
  path:
    description:
      - Resources YAML file to where router will be serialized.
      - In case the resource file already exists, it must match the
        os-migrate version.
      - In case the resource of same type and name exists in the file,
        it will be replaced.
    required: true
    type: str
  name:
    description:
      - Name (or ID) of a Router to export.
    required: true
    type: str
  availability_zone:
    description:
      - Availability zone.
    required: false
    type: str
  cloud:
    description:
      - Cloud configuration from clouds.yml
      - Required if 'auth' parameter not used.
    required: false
    type: raw
"""

EXAMPLES = r"""
- name: Export myrouter into /opt/os-migrate/routers.yml
  os_migrate.os_migrate.export_router:
    path: /opt/os-migrate/routers.yml
    name: myrouter
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
    filesystem,
    router,
)


def run_module():
    argument_spec = openstack_full_argument_spec(
        path=dict(type="str", required=True),
        name=dict(type="str", required=True),
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
    sdk_rtr = conn.network.find_router(module.params["name"], ignore_missing=False)
    rtr = router.Router.from_sdk(conn, sdk_rtr)

    result["changed"] = filesystem.write_or_replace_resource(module.params["path"], rtr)

    module.exit_json(**result)


def main():
    run_module()


if __name__ == "__main__":
    main()
