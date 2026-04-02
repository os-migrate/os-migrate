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
module: export_detached_volume
short_description: Export OpenStack detached volume
extends_documentation_fragment:
  - os_migrate.os_migrate.openstack
version_added: "2.9.0"
author: "OpenStack tenant migration tools (@os-migrate)"
description:
  - "Export OpenStack detached volume definition into an OS-Migrate YAML"
options:
  auth:
    description:
      - Dictionary with parameters for chosen auth type.
      - Required if 'cloud' parameter is not used.
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
      - Resources YAML file to where detached volume will be serialized.
      - In case the resource file already exists, it must match the
        os-migrate version.
      - In case the resource of same type and name exists in the file,
        it will be replaced.
    required: true
    type: str
  volume_id:
    description:
      - Volume ID of the detached volume to export.
    required: true
    type: str
  cloud:
    description:
      - Cloud from clouds.yaml to use.
      - Required if 'auth' parameter is not used.
    required: false
    type: raw
"""

EXAMPLES = r"""
- name: Export mydetachedvolume into /opt/os-migrate/detached_volumes.yml
  os_migrate.os_migrate.export_detached_volume:
    path: /opt/os-migrate/detached_volumes.yml
    volume_id: <some-volume-uuid>
"""

RETURN = r"""
"""

from ansible.module_utils.basic import AnsibleModule

from ansible_collections.os_migrate.os_migrate.plugins.module_utils import filesystem
from ansible_collections.os_migrate.os_migrate.plugins.module_utils import os_auth
from ansible_collections.os_migrate.os_migrate.plugins.module_utils import server_volume


def run_module():
    argument_spec = os_auth.openstack_full_argument_spec(
        path=dict(type="str", required=True),
        volume_id=dict(type="str", required=True),
    )

    result = dict(
        changed=False,
        errors=[],
    )

    module = AnsibleModule(
        argument_spec=argument_spec,
        # TODO: Consider check mode. We'd fetch the resource and check
        # if the file representation matches it.
        # supports_check_mode=True,
    )

    conn = os_auth.get_connection(module)
    sdk_volume = conn.block_storage.get_volume(module.params["volume_id"])
    data = server_volume.ServerVolume.from_sdk(conn, sdk_volume)

    if not sdk_volume["attachments"]:
        result["changed"] = filesystem.write_or_replace_resource(
            module.params["path"], data
        )
    else:
        result["failed"] = True
        result["errors"] = "Volume " + module.params["volume_id"] + " is not detached"

    module.exit_json(**result)


def main():
    run_module()


if __name__ == "__main__":
    main()
