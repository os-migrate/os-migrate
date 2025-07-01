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
module: export_workload

short_description: Export OpenStack instance information

extends_documentation_fragment:
  - os_migrate.os_migrate.openstack

version_added: "2.9.0"

author: "OpenStack tenant migration tools (@os-migrate)"

description:
  - "Export OpenStack workload definition into an OS-Migrate YAML"

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
  validate_certs:
    description:
      - Validate HTTPS certificates when logging in to OpenStack.
    required: false
    type: bool
  region_name:
    description:
      - OpenStack region name. Can be omitted if using default region.
    required: false
    type: str
  path:
    description:
      - Resources YAML file to where workloads will be serialized.
      - In case the resource file already exists, it must match the
        os-migrate version.
      - In case the resource of same type and name exists in the file,
        it will be replaced.
    required: true
    type: str
  name:
    description:
      - Name (or ID) of an instance to export.
    required: true
    type: str
  migration_params:
    description:
      - Dictionary with parameters for the migration procedure.
    required: false
    type: dict
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
- name: Export migration-vm into /opt/os-migrate/workloads.yml
  os_migrate.os_migrate.export_workload:
    path: /opt/os-migrate/workloads.yml
    name: migration-vm
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
from ansible_collections.os_migrate.os_migrate.plugins.module_utils import server


def run_module():
    argument_spec = openstack_full_argument_spec(
        path=dict(type="str", required=True),
        name=dict(type="str", required=True),
        migration_params=dict(type="dict", required=False, default={}),
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
    sdk_server_nodetails = conn.compute.find_server(
        module.params["name"], ignore_missing=False
    )
    sdk_server = conn.compute.get_server(sdk_server_nodetails["id"])
    srv = server.Server.from_sdk(conn, sdk_server)
    srv.update_migration_params(module.params["migration_params"])

    result["changed"] = filesystem.write_or_replace_resource(module.params["path"], srv)

    module.exit_json(**result)


def main():
    run_module()


if __name__ == "__main__":
    main()
