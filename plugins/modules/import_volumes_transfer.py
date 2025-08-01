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
module: import_volumes_transfer_volumes

short_description: Create destination volumes and transfer source data.

extends_documentation_fragment:
  - os_migrate.os_migrate.openstack

version_added: "2.9.0"

author: "OpenStack tenant migration tools (@os-migrate)"

description:
  - "Connect to the destination cloud to create new volumes, and copy data from the source cloud."

options:
  auth:
    description:
      - Required if 'cloud' param not used
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
  validate_certs:
    description:
      - Validate HTTPS certificates when logging in to OpenStack.
    required: false
    type: bool
  conversion_host:
    description:
      - Dictionary with information about the destination conversion host (address, status, name, id)
    required: true
    type: dict
  log_file:
    description:
      - Path to store a log file for this conversion process.
    required: false
    type: str
  src_conversion_host_address:
    description:
      - Require IP address of the source conversion host.
      - This is used by the destination conversion host to initiate data transfer.
    required: true
    type: str
  ssh_key_path:
    description:
      - Path to an SSH private key authorized on the destination cloud.
    required: true
    type: str
  ssh_user:
    description:
      - The SSH user to connect to the conversion hosts.
      - Provided by the import_volumes_export_volumes module.
    required: true
    type: str
  state_file:
    description:
      - Path to store a transfer progress file for this conversion process.
    required: false
    type: str
  dst_conversion_host_address:
    description:
      - Optional IP address of the destination conversion host. Without this, the
        plugin will use the 'access_ipv4' property of the conversion host instance.
    required: false
    type: str
  transfer_uuid:
    description:
      - A UUID used to keep track of this tranfer's resources on the conversion hosts.
      - Provided by the import_volumes_export_volumes module.
    required: true
    type: str
  volume_map:
    description:
      - Dictionary providing information about the volumes to transfer.
      - Provided by the import_volumes_export_volumes module.
    required: true
    type: dict
  timeout:
    description:
      - Timeout for long running operations, in seconds.
    required: false
    default: 1800
    type: int
"""

EXAMPLES = r"""
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

- name: transfer volumes to destination
  os_migrate.os_migrate.import_volumes_transfer:
    cloud: dst
    validate_certs: "{{ os_migrate_dst_validate_certs|default(omit) }}"
    ca_cert: "{{ os_migrate_dst_ca_cert|default(omit) }}"
    client_cert: "{{ os_migrate_dst_client_cert|default(omit) }}"
    client_key: "{{ os_migrate_dst_client_key|default(omit) }}"
    conversion_host:
      "{{ os_dst_conversion_host_info.openstack_conversion_host }}"
    ssh_key_path: "{{ import_detached_volumes_keypair_private_path }}"
    ssh_user: "{{ conversion_host_ssh_user }}"
    transfer_uuid: "{{ exports.transfer_uuid }}"
    src_conversion_host_address:
      "{{ os_src_conversion_host_info.openstack_conversion_host.address }}"
    volume_map: "{{ exports.volume_map }}"
    log_file: "{{ exports.log_file }}"
    state_file: "{{ exports.state_file }}"
    timeout: "{{ import_detached_volumes_timeout }}"
  register: transfer
"""

RETURN = r"""
volume_map:
  description:
    - Updated mapping of source volume devices to NBD export URLs.
    - Takes the input volume_map and fills out the destination-specific fields.
  returned: Only after successfully transferring volumes from the source cloud.
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
    OpenstackVolumeTransfer,
    DEFAULT_TIMEOUT,
)

import re


class OpenStackDestinationVolume(OpenstackVolumeTransfer):
    def __init__(
        self,
        openstack_connection,
        destination_conversion_host_id,
        ssh_key_path,
        ssh_user,
        transfer_uuid,
        source_conversion_host_address,
        volume_map,
        destination_conversion_host_address=None,
        state_file=None,
        log_file=None,
        timeout=DEFAULT_TIMEOUT,
    ):

        super().__init__(
            openstack_connection,
            destination_conversion_host_id,
            ssh_key_path,
            ssh_user,
            transfer_uuid,
            conversion_host_address=destination_conversion_host_address,
            state_file=state_file,
            log_file=log_file,
            timeout=timeout,
        )

        # Required unique parameters:
        # source_conversion_host_address: Source conversion host IP address for
        #                                 direct connection from destination.
        # volume_map: Volume map returned by export_volumes module
        self.source_conversion_host_address = source_conversion_host_address
        self.volume_map = volume_map

        # Match for qemu_img progress percentage
        self.qemu_progress_re = re.compile(r"\((\d+\.\d+)/100%\)")

        # SSH tunnel process
        self.forwarding_process = None
        self.forwarding_process_command = None

    def transfer_exports(self):
        try:
            self._create_forwarding_process()
            self._create_destination_volumes()
            self._attach_destination_volumes()
            self._convert_destination_volumes()
            self._detach_destination_volumes()
        finally:
            self._stop_forwarding_process()
            self._release_ports()
            self._converter_close_exports()


def run_module():
    argument_spec = openstack_full_argument_spec(
        conversion_host=dict(type="dict", required=True),
        ssh_key_path=dict(type="str", required=True),
        ssh_user=dict(type="str", required=True),
        transfer_uuid=dict(type="str", required=True),
        src_conversion_host_address=dict(type="str", required=True),
        volume_map=dict(type="dict", required=True),
        dst_conversion_host_address=dict(type="str", default=None),
        state_file=dict(type="str", default=None),
        log_file=dict(type="str", default=None),
        timeout=dict(type="int", default=DEFAULT_TIMEOUT),
    )

    result = dict(
        changed=False,
    )

    module = AnsibleModule(
        argument_spec=argument_spec,
    )

    sdk, conn = openstack_cloud_from_module(module)

    # Required parameters
    destination_conversion_host_id = module.params["conversion_host"]["id"]
    ssh_key_path = module.params["ssh_key_path"]
    ssh_user = module.params["ssh_user"]
    transfer_uuid = module.params["transfer_uuid"]
    source_conversion_host_address = module.params["src_conversion_host_address"]
    volume_map = module.params["volume_map"]

    # Optional parameters
    destination_conversion_host_address = module.params.get(
        "dst_conversion_host_address", None
    )
    state_file = module.params.get("state_file", None)
    log_file = module.params.get("log_file", None)
    timeout = module.params["timeout"]

    destination_host = OpenStackDestinationVolume(
        conn,
        destination_conversion_host_id,
        ssh_key_path,
        ssh_user,
        transfer_uuid,
        source_conversion_host_address,
        volume_map,
        destination_conversion_host_address=destination_conversion_host_address,
        state_file=state_file,
        log_file=log_file,
        timeout=timeout,
    )
    destination_host.transfer_exports()
    result["volume_map"] = destination_host.volume_map

    module.exit_json(**result)


def main():
    run_module()


if __name__ == "__main__":
    main()
