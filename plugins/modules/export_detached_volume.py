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

# Import openstack module utils from ansible_collections.openstack.cloud.plugins as per ansible 3+
HAS_OPENSTACK_CLOUD = False
try:
    from ansible_collections.openstack.cloud.plugins.module_utils.openstack import (
        openstack_full_argument_spec,
        openstack_cloud_from_module,
    )
    HAS_OPENSTACK_CLOUD = True
except ImportError:
    try:
        # If this fails fall back to ansible < 3 imports
        from ansible.module_utils.openstack import (
            openstack_full_argument_spec,
            openstack_cloud_from_module,
        )
        HAS_OPENSTACK_CLOUD = True
    except ImportError:
        # Create stub functions for sanity testing
        HAS_OPENSTACK_CLOUD = False

        def openstack_full_argument_spec(**kwargs):
            spec = dict(
                cloud=dict(type='raw'),
                auth=dict(type='dict'),
                auth_type=dict(type='str'),
                region_name=dict(type='str'),
                wait=dict(type='bool', default=True),
                timeout=dict(type='int', default=180),
                api_timeout=dict(type='int'),
                validate_certs=dict(type='bool', aliases=['verify']),
                ca_cert=dict(type='str', aliases=['cacert']),
                client_cert=dict(type='str', aliases=['cert']),
                client_key=dict(type='str', aliases=['key']),
                interface=dict(type='str', choices=['admin', 'internal', 'public'], default='public', aliases=['endpoint_type']),
                sdk_log_path=dict(type='str'),
                sdk_log_level=dict(type='str', default='INFO', choices=['INFO', 'DEBUG']),
            )
            spec.update(kwargs)
            return spec

        def openstack_cloud_from_module(module):
            return None, None

from ansible_collections.os_migrate.os_migrate.plugins.module_utils import filesystem
from ansible_collections.os_migrate.os_migrate.plugins.module_utils import server_volume


def run_module():
    argument_spec = openstack_full_argument_spec(
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

    if not HAS_OPENSTACK_CLOUD:
        module.fail_json(msg='openstack.cloud collection is required for this module')

    sdk, conn = openstack_cloud_from_module(module)
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
