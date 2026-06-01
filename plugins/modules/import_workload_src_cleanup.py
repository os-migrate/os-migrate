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
module: import_workload_src_cleanup

short_description: Clean up temporary volumes after a workload migration

extends_documentation_fragment:
  - os_migrate.os_migrate.openstack

version_added: "2.9.0"

author: "OpenStack tenant migration tools (@os-migrate)"

description:
  - Remove any temporary snapshots or volumes associated with this workload migration.

options:
  conversion_host:
    description:
      - Information about the source conversion host.
    required: true
    type: dict
  data:
    description:
      - Server data loaded from OS-Migrate workloads YAML.
    required: true
    type: dict
  ssh_key_path:
    description:
      - Path to an SSH private key authorized on the source cloud.
    required: true
    type: str
  ssh_user:
    description:
      - SSH user for conversion host access.
    required: true
    type: str
  transfer_uuid:
    description:
      - Transfer UUID created by export/transfer modules.
    required: true
    type: str
  volume_map:
    description:
      - Mapping structure returned by previous workload transfer steps.
    required: true
    type: dict
  src_conversion_host_address:
    description:
      - Optional explicit source conversion host address.
    required: false
    type: str
  state_file:
    description:
      - Optional state file path.
    required: false
    type: str
  log_file:
    description:
      - Optional log file path.
    required: false
    type: str
  timeout:
    description:
      - Timeout for long running operations, in seconds.
    required: false
    default: 1800
    type: int
"""

EXAMPLES = r"""
- name: Clean up source-side temporary migration resources
  os_migrate.os_migrate.import_workload_src_cleanup:
    auth: "{{ os_migrate_src_auth }}"
    auth_type: "{{ os_migrate_src_auth_type | default(omit) }}"
    region_name: "{{ os_migrate_src_region_name | default(omit) }}"
    validate_certs: "{{ os_migrate_src_validate_certs | default(omit) }}"
    ca_cert: "{{ os_migrate_src_ca_cert | default(omit) }}"
    client_cert: "{{ os_migrate_src_client_cert | default(omit) }}"
    client_key: "{{ os_migrate_src_client_key | default(omit) }}"
    data: "{{ item }}"
    conversion_host: "{{ os_src_conversion_host_info.openstack_conversion_host }}"
    ssh_key_path: "{{ os_migrate_conversion_keypair_private_path }}"
    ssh_user: "{{ os_migrate_conversion_host_ssh_user }}"
    transfer_uuid: "{{ exports.transfer_uuid }}"
    volume_map: "{{ exports.volume_map }}"
    state_file: "{{ os_migrate_data_dir }}/{{ item.params.name }}.state"
    log_file: "{{ os_migrate_data_dir }}/{{ item.params.name }}.log"
"""

RETURN = r"""
"""

from ansible.module_utils.basic import AnsibleModule

from ansible_collections.os_migrate.os_migrate.plugins.module_utils import os_auth
from ansible_collections.os_migrate.os_migrate.plugins.module_utils import server

from ansible_collections.os_migrate.os_migrate.plugins.module_utils.volume_common import (
    DEFAULT_TIMEOUT,
    OpenstackVolumeClean,
)


class OpenStackSourceHostCleanup(OpenstackVolumeClean):
    """Removes temporary migration volumes and snapshots from source cloud."""

    def __init__(
        self,
        openstack_connection,
        source_conversion_host_id,
        ssh_key_path,
        ssh_user,
        source_instance_id,
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
        # source_instance_id: ID of VM that was migrated from the source
        # volume_map: Volume map returned by export_volumes module
        self.source_instance_id = source_instance_id
        self.volume_map = volume_map

        # This will make _release_ports clean up ports from the export module
        for path, mapping in volume_map.items():
            port = mapping["port"]
            self.claimed_ports.append(port)


def run_module():
    argument_spec = os_auth.openstack_full_argument_spec(
        data=dict(type="dict", required=True),
        conversion_host=dict(type="dict", required=True),
        ssh_key_path=dict(type="str", required=True, no_log=True),
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

    conn = os_auth.get_connection(module)
    src = server.Server.from_data(module.params["data"])
    params, info = src.params_and_info()

    # Required parameters
    source_conversion_host_id = module.params["conversion_host"]["id"]
    ssh_key_path = module.params["ssh_key_path"]
    ssh_user = module.params["ssh_user"]
    source_instance_id = info["id"]
    transfer_uuid = module.params["transfer_uuid"]
    volume_map = module.params["volume_map"]

    # Optional parameters
    source_conversion_host_address = module.params.get(
        "src_conversion_host_address", None
    )
    state_file = module.params.get("state_file", None)
    log_file = module.params.get("log_file", None)
    timeout = module.params["timeout"]

    host_cleanup = OpenStackSourceHostCleanup(
        conn,
        source_conversion_host_id,
        ssh_key_path,
        ssh_user,
        source_instance_id,
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
