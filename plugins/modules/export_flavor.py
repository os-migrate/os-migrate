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
module: export_flavor

short_description: Export OpenStack Nova Flavor

version_added: "2.9.0"

description:
  - Export an OpenStack Nova Flavor definition into an OS-Migrate YAML file.

author:
  - OpenStack tenant migration tools (@os-migrate)

options:
  cloud:
    description:
      - Cloud name from clouds.yaml
    required: false
    type: str

  auth:
    description:
      - OpenStack authentication dictionary
    required: false
    type: dict

  region_name:
    description:
      - OpenStack region
    required: false
    type: str

  path:
    description:
      - Path to YAML resource file
    required: true
    type: str

  name:
    description:
      - Flavor name or ID
    required: true
    type: str
"""

EXAMPLES = r"""
- name: Export flavor
  export_flavor:
    cloud: source_cloud
    path: /opt/os-migrate/flavors.yml
    name: m1.small
"""

RETURN = r"""
changed:
  description: Whether the file changed
  type: bool
"""

from ansible.module_utils.basic import AnsibleModule

from ansible_collections.os_migrate.os_migrate.plugins.module_utils import filesystem
from ansible_collections.os_migrate.os_migrate.plugins.module_utils import flavor
from ansible_collections.os_migrate.os_migrate.plugins.module_utils import os_auth


def run_module():

    argument_spec = os_auth.openstack_full_argument_spec(
        path=dict(type="str", required=True),
        name=dict(type="str", required=True),
    )

    module = AnsibleModule(argument_spec=argument_spec)

    result = dict(
        changed=False,
    )

    conn = os_auth.get_connection(module)

    try:
        sdk_flavor = conn.compute.find_flavor(
            module.params["name"], ignore_missing=False
        )
    except Exception as e:
        module.fail_json(msg=f"Failed to fetch flavor: {str(e)}")

    data = flavor.Flavor.from_sdk(conn, sdk_flavor)

    result["changed"] = filesystem.write_or_replace_resource(
        module.params["path"], data
    )

    module.exit_json(**result)


def main():
    run_module()


if __name__ == "__main__":
    main()