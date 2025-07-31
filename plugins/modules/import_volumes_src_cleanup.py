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
module: import_volumes_src_cleanup

short_description: Clean up temporary volumes after a volume migration

extends_documentation_fragment:
  - os_migrate.os_migrate.openstack

version_added: "2.9.0"

author: "OpenStack tenant migration tools (@os-migrate)"

description:
  - Remove any temporary snapshots or volumes associated with this volume migration.

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
      - Dictionary with information about the source conversion host (address, status, name, id)
    required: true
    type: dict
  data:
    description:
      - Data structure with server parameters as loaded from OS-Migrate volumes YAML file.
    required: true
    type: dict
  log_file:
    description:
      - Path to store a log file for this conversion process.
    required: false
    type: str
  state_file:
    description:
      - Path to store a transfer progress file for this conversion process.
    required: false
    type: str
  src_conversion_host_address:
    description:
      - Optional IP address of the source conversion host. Without this, the
        plugin will use the 'access_ipv4' property of the conversion host instance.
    required: false
    type: str
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
    ssh_key_path: "{{ conversion_host_keypair_private_path }}"
    ssh_user: "{{ conversion_host_ssh_user }}"
    log_dir: "{{ os_migrate_data_dir }}/volume_logs"
    timeout: "{{ os_migrate_timeout }}"
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
    ssh_key_path: "{{ conversion_host_keypair_private_path }}"
    ssh_user: "{{ conversion_host_ssh_user }}"
    transfer_uuid: "{{ exports.transfer_uuid }}"
    src_conversion_host_address:
      "{{ os_src_conversion_host_info.openstack_conversion_host.address }}"
    volume_map: "{{ exports.volume_map }}"
    log_file: "{{ exports.log_file }}"
    state_file: "{{ exports.state_file }}"
    timeout: "{{ os_migrate_timeout }}"
  register: transfer

- name: clean up in the source cloud after migration
  os_migrate.os_migrate.import_volumes_src_cleanup:
    cloud: src
    validate_certs: "{{ os_migrate_src_validate_certs|default(omit) }}"
    ca_cert: "{{ os_migrate_src_ca_cert|default(omit) }}"
    client_cert: "{{ os_migrate_src_client_cert|default(omit) }}"
    client_key: "{{ os_migrate_src_client_key|default(omit) }}"
    conversion_host: "{{ os_src_conversion_host_info.openstack_conversion_host }}"
    ssh_key_path: "{{ conversion_host_keypair_private_path }}"
    ssh_user: "{{ conversion_host_ssh_user }}"
    transfer_uuid: "{{ exports.transfer_uuid }}"
    volume_map: "{{ exports.volume_map }}"
    log_file: "{{ exports.log_file }}"
    state_file: "{{ exports.state_file }}"
    timeout: "{{ os_migrate_timeout }}"
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

from ansible_collections.os_migrate.os_migrate.plugins.module_utils.volume_common import (
    DEFAULT_TIMEOUT,
    OpenstackVolumeClean,
)


class OpenStackSourceCleanup(OpenstackVolumeClean):
    """Removes temporary migration volumes and snapshots from source cloud."""

    def __init__(
        self,
        openstack_connection,
        source_conversion_host_id,
        ssh_key_path,
        ssh_user,
        transfer_uuid,
        volume_map,
        source_conversion_host_address=None,
        state_file=None,
        log_file=None,
        timeout=DEFAULT_TIMEOUT,
    ):

        super().__init__(
            openstack_connection,
            source_conversion_host_id,
            ssh_key_path,
            ssh_user,
            transfer_uuid,
            conversion_host_address=source_conversion_host_address,
            state_file=state_file,
            log_file=log_file,
            timeout=timeout,
        )

        # Required unique parameters:
        # volume_map: Volume map returned by export_volumes module
        self.volume_map = volume_map

        # This will make _release_ports clean up ports from the export module
        for path, mapping in volume_map.items():
            port = mapping["port"]
            self.claimed_ports.append(port)

    def close_exports(self):
        self._converter_close_exports()
        self._detach_volumes_from_source_converter()


def run_module():
    argument_spec = openstack_full_argument_spec(
        conversion_host=dict(type="dict", required=True),
        ssh_key_path=dict(type="str", required=True),
        ssh_user=dict(type="str", required=True),
        transfer_uuid=dict(type="str", required=True),
        volume_map=dict(type="dict", required=True),
        src_conversion_host_address=dict(type="str", default=None),
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
    source_conversion_host_id = module.params["conversion_host"]["id"]
    ssh_key_path = module.params["ssh_key_path"]
    ssh_user = module.params["ssh_user"]
    transfer_uuid = module.params["transfer_uuid"]
    volume_map = module.params["volume_map"]

    # Optional parameters
    source_conversion_host_address = module.params.get(
        "src_conversion_host_address", None
    )
    state_file = module.params.get("state_file", None)
    log_file = module.params.get("log_file", None)
    timeout = module.params["timeout"]

    host_cleanup = OpenStackSourceCleanup(
        conn,
        source_conversion_host_id,
        ssh_key_path,
        ssh_user,
        transfer_uuid,
        volume_map,
        source_conversion_host_address=source_conversion_host_address,
        state_file=state_file,
        log_file=log_file,
        timeout=timeout,
    )
    host_cleanup.close_exports()

    module.exit_json(**result)


def main():
    run_module()


if __name__ == "__main__":
    main()
