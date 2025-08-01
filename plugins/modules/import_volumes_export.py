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
module: import_volumes_export_volumes

short_description: Create NBD exports of OpenStack volumes

extends_documentation_fragment:
  - os_migrate.os_migrate.openstack

version_added: "2.9.0"

author: "OpenStack tenant migration tools (@os-migrate)"

description:
  - "Take a volume from an OS-Migrate YAML structure, and export its volumes over NBD."

options:
  auth:
    description:
      - Required if 'cloud' param not used.
    required: false
    type: dict
  auth_type:
    description:
      - Auth type plugin for destination OpenStack cloud. Can be omitted if using password authentication.
    required: false
    type: str
  cloud:
    description:
      - Cloud resource from clouds.yml
      - Required if 'auth' param not used
    required: false
    type: raw
  conversion_host:
    description:
      - Dictionary with information about the source conversion host (address, status, name, id)
    required: true
    type: dict
  data:
    description:
      - Data structure with server parameters as loaded from OS-Migrate volumes YAML file.
    required: true
    type: dict
  ssh_key_path:
    description:
      - Path to an SSH private key authorized on the source cloud.
    required: true
    type: str
  ssh_user:
    description:
      - The SSH user to connect to the conversion hosts.
    required: true
    type: str
  log_dir:
    description:
      - Complete path for log folder.
    required: true
    type: str
  timeout:
    description:
      - Timeout for long running operations, in seconds.
    required: false
    default: 1800
    type: int
"""

EXAMPLES = r"""
import_volumes.yml:

  - name: expose source volume
    os_migrate.os_migrate.import_volumes_export:
      cloud: "{{ cloud_vars_src }}"
      conversion_host:
        "{{ os_src_conversion_host_info.openstack_conversion_host }}"
      data: "{{ detached_volumes }}"
      ssh_key_path: "{{ import_detached_volumes_keypair_private_path }}"
      ssh_user: "{{ conversion_host_ssh_user }}"
      log_dir: "{{ os_migrate_data_dir }}/volume_logs"
      timeout: "{{ import_detached_volumes_timeout }}"
    register: exports
"""

RETURN = r"""
data:
  description: volumes imported
  returned: Only on success.
  type: list
  sample:
    - _info:
        attachments: []
        id: 0e9ff1ab-fb8d-4c12-81c4-29d519d09cb9
        is_bootable: false
        size: 5
      _migration_params:
        params:
        availability_zone: nova
        description: null
        name: test-detached
        volume_type: tripleo
      type: openstack.network.ServerVolume

log_file:
  description: log file path
  returned: Only on success.
  type: str
  sample: /root/os_migrate/tests/e2e/tmp/data/volume_logs/detached_volumes.log

state_file:
  description: transfer progress file for this conversion process.
  returned: Only on success.
  type: str
  sample: /root/os_migrate/tests/e2e/tmp/data/volume_logs/detached_volumes.state

transfer_uuid:
  description: UUID to identify this transfer when needed
  returned: Only on success.
  type: str
  sample: 9b8a64b3-c976-4103-b34e-995e4ab9f57b

volume_map:
  description:
    - Mapping of source volume devices to NBD export URLs.
    - This structure only has source-related fields filled out.
  returned: Only after successfully moving volumes on source cloud.
  type: dict
  sample:
    volume_map:
      0e9ff1ab-fb8d-4c12-81c4-29d519d09cb9:
      bootable: false
      dest_dev: null
      dest_id: null
      image_id: null
      name: test-detached3
      port: 49166
      progress: 0.0
      size: 5
      snap_id: null
      source_dev: /dev/vdb
      source_id: 0e9ff1ab-fb8d-4c12-81c4-29d519d09cb9
      url: null
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

from ansible_collections.os_migrate.os_migrate.plugins.module_utils.volume_common import (
    DEFAULT_TIMEOUT,
    OpenstackVolumeExport,
)

import uuid
import os


class OpenStackSourceVolume(OpenstackVolumeExport):
    """Export volumes from an OpenStack instance over NBD."""

    def __init__(
        self,
        openstack_connection,
        source_conversion_host_id,
        ssh_key_path,
        ssh_user,
        volume_list=None,
        state_file=None,
        log_file=None,
        source_conversion_host_address=None,
        transfer_uuid=None,
        timeout=DEFAULT_TIMEOUT,
    ):
        # UUID marker for child processes on conversion hosts.
        transfer_uuid = str(uuid.uuid4())

        super().__init__(
            openstack_connection,
            source_conversion_host_id,
            ssh_key_path,
            ssh_user,
            transfer_uuid=transfer_uuid,
            conversion_host_address=source_conversion_host_address,
            state_file=state_file,
            log_file=log_file,
            timeout=timeout,
        )
        # Build up a list of VolumeMappings keyed by the original device path
        # provided by the OpenStack API. Details:
        #   source_dev:  Device path (like /dev/vdb) on source conversion host
        #   source_id:   Volume ID on source cloud
        #   dest_dev:    Device path on destination conversion host
        #   dest_id:     Volume ID on destination cloud
        #   snap_id:     Root volumes need snapshot+new volume
        #   image_id:    Direct-from-image VMs create temporary snapshot image
        #   name:        Save volume name to set on destination
        #   size:        Volume size reported by OpenStack, in GB
        #   port:        Port used to listen for NBD connections to this volume
        #   url:         Final NBD export on destination conversion host
        #   progress:    Transfer progress percentage
        #   bootable:    Boolean flag for boot disks
        self.volume_map = {}
        self.volume_list = volume_list

    def prepare_exports(self):
        """
        Attach the source volume to the source conversion host, and start
        waiting for NBD connections.
        """
        self._get_root_and_data_volumes()
        self.log.info("Data in the volume: %s", self.volume_list)
        self._attach_volumes_to_converter()
        self._export_volumes_from_converter()

    def _get_root_and_data_volumes(self):
        """
        Volume mapping step one: get the IDs and sizes of all volumes on the
        source VM. Key off the original device path to eventually preserve this
        order on the destination.
        """
        for s_volume in self.volume_list:
            volume = self.conn.get_volume_by_id(s_volume["_info"]["id"])
            self.log.info("Inspecting volume: %s", volume["id"])
            dev_path = volume["id"]
            self.volume_map[dev_path] = dict(
                source_dev=None,
                source_id=volume["id"],
                dest_dev=None,
                dest_id=None,
                snap_id=None,
                image_id=None,
                name=volume["name"],
                size=volume["size"],
                port=None,
                url=None,
                progress=None,
                bootable=volume["bootable"],
            )
            self._update_progress(dev_path, 0.0)


def run_module():
    argument_spec = openstack_full_argument_spec(
        data=dict(type="list", required=True),
        conversion_host=dict(type="dict", required=True),
        ssh_key_path=dict(type="str", required=True),
        ssh_user=dict(type="str", required=True),
        src_conversion_host_address=dict(type="str", default=None),
        log_dir=dict(type="str", default=None),
        timeout=dict(type="int", default=DEFAULT_TIMEOUT),
    )

    result = dict(
        changed=False,
    )

    module = AnsibleModule(
        argument_spec=argument_spec,
    )

    sdk, conn = openstack_cloud_from_module(module)
    volume_list = module.params["data"]

    # Required parameters
    source_conversion_host_id = module.params["conversion_host"]["id"]
    ssh_key_path = module.params["ssh_key_path"]
    ssh_user = module.params["ssh_user"]

    # Optional parameters
    source_conversion_host_address = module.params.get(
        "src_conversion_host_address", None
    )
    log_dir = module.params["log_dir"]
    timeout = module.params["timeout"]

    # TODO implement the names of the files in the volume_common.py
    log_file = os.path.join(log_dir, "detached_volumes") + ".log"
    state_file = os.path.join(log_dir, "detached_volumes") + ".state"

    source_volume = OpenStackSourceVolume(
        conn,
        source_conversion_host_id,
        ssh_key_path,
        ssh_user,
        volume_list=volume_list,
        source_conversion_host_address=source_conversion_host_address,
        state_file=state_file,
        log_file=log_file,
        timeout=timeout,
    )
    source_volume.prepare_exports()
    result["log_file"] = source_volume.log_file
    result["state_file"] = source_volume.state_file
    result["transfer_uuid"] = source_volume.transfer_uuid
    result["volume_map"] = source_volume.volume_map
    result["data"] = module.params["data"]
    module.exit_json(**result)


def main():
    run_module()


if __name__ == "__main__":
    main()
