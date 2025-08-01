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
module: os_conversion_host_info

short_description: Get information about an OpenStack conversion host instance

extends_documentation_fragment:
  - os_migrate.os_migrate.openstack

version_added: "2.9.0"

author: "OpenStack tenant migration tools (@os-migrate)"

description:
  - "Get information about a migration conversion host instance from OpenStack, in the format expected by the import_workload module."

options:
  server:
    description:
      - Name or ID of server to inspect
    required: true
    type: str
  filters:
    description:
      - Options for filtering the host, e.g. by project.
    required: false
    type: dict
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
      - Cloud config from clouds.yml resource
      - Required if 'auth' param not used.
    required: false
    type: raw
"""

EXAMPLES = r"""
- os_migrate.os_migrate.os_conversion_host_info:
    server: source-migration-conversion-host
    auth:
      auth_url: https://dest-osp:13000/v3
      username: migrate
      password: migrate
      project_domain_id: default
      project_name: migration-destination
      user_domain_id: default
  register: os_dst_conversion_host_info
"""

RETURN = r"""
openstack_conversion_host:
    description: Useful information about a conversion host
    returned: only when information gathering was successful
    type: complex
    contains:
        address:
            description: IP (v4) address of the specified instance
            type: str
        name:
            description: Name of the specified instance
            type: str
        id:
            description: ID of the specified instance
            type: str
        status:
            description: Current status of the specified instance (ACTIVE, SHUTOFF, etc.)
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
        server=dict(type="str", required=True),
        filters=dict(required=False, type="dict", default={}),
    )

    module = AnsibleModule(
        argument_spec=argument_spec,
    )

    srv = module.params["server"]
    filters = module.params["filters"]
    conversion_host = {}

    try:
        sdk, conn = openstack_cloud_from_module(module)
        server = conn.get_server(name_or_id=srv, filters=filters)
        if not server:
            module.fail_json(msg="Conversion host " + srv + " not found!")

        # There are two possible attributes for the server's IPv4 floating IP
        # value, access_ipv4 and public_v4 which might not be consistent across
        # vendors, so we check both.
        if hasattr(server, "access_ipv4") and server.access_ipv4 != "":
            conversion_host["address"] = server.access_ipv4
        elif hasattr(server, "public_v4") and server.public_v4 != "":
            conversion_host["address"] = server.public_v4
        else:
            module.fail_json(
                msg="Conversion host address cant be empty \n" + str(server)
            )
        conversion_host["status"] = server.status
        conversion_host["name"] = server.name
        conversion_host["id"] = server.id

    except sdk.exceptions.OpenStackCloudException as e:
        module.fail_json(msg=str(e))

    module.exit_json(changed=False, openstack_conversion_host=conversion_host)


if __name__ == "__main__":
    main()
