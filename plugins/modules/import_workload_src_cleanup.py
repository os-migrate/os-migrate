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
  region_name:
    description:
      - Destination OpenStack region name. Can be omitted if using default region.
    required: false
    type: str
  availability_zone:
    description:
      - Availability zone.
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
      - Data structure with server parameters as loaded from OS-Migrate workloads YAML file.
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
      - Provided by the import_workloads_export_volumes module.
    required: true
    type: str
  volume_map:
    description:
      - Dictionary providing information about the volumes to transfer.
      - Provided by the import_workloads_export_volumes module.
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
main.yml:

  - name: validate loaded resources
    os_migrate.os_migrate.validate_resource_files:
      paths:
        - "{{ os_migrate_data_dir }}/workloads.yml"
    register: workloads_file_validation
    when: import_workloads_validate_file

  - name: read workloads resource file
    os_migrate.os_migrate.read_resources:
      path: "{{ os_migrate_data_dir }}/workloads.yml"
    register: read_workloads

  - name: get source conversion host address
    os_migrate.os_migrate.os_conversion_host_info:
      auth:
        auth_url: https://src-osp:13000/v3
        username: migrate
        password: migrate
        project_domain_id: default
        project_name: migration-source
        user_domain_id: default
      server_id: ce4dda96-5d8e-4b67-aee2-9845cdc943fe
    register: os_src_conversion_host_info

  - name: get destination conversion host address
    os_migrate.os_migrate.os_conversion_host_info:
      auth:
        auth_url: https://dest-osp:13000/v3
        username: migrate
        password: migrate
        project_domain_id: default
        project_name: migration-destination
        user_domain_id: default
      server_id: 2d2afe57-ace5-4187-8fca-5f10f9059ba1
    register: os_dst_conversion_host_info

  - name: import workloads
    include_tasks: workload.yml
    loop: "{{ read_workloads.resources }}"


workload.yml:

  - block:
      - name: preliminary setup for workload import
        os_migrate.os_migrate.import_workload_prelim:
          auth:
            auth_url: https://dest-osp:13000/v3
            username: migrate
            password: migrate
            project_domain_id: default
            project_name: migration-destination
            user_domain_id: default
          validate_certs: false
          src_conversion_host: "{{ os_src_conversion_host_info.openstack_conversion_host }}"
          src_auth:
            auth_url: https://src-osp:13000/v3
            username: migrate
            password: migrate
            project_domain_id: default
            project_name: migration-source
            user_domain_id: default
          src_validate_certs: false
          data: "{{ item }}"
          data_dir: "{{ os_migrate_data_dir }}"
        register: prelim

      - debug:
          msg:
            - "{{ prelim.server_name }} log file: {{ prelim.log_file }}"
            - "{{ prelim.server_name }} progress file: {{ prelim.state_file }}"
        when: prelim.changed

      - name: expose source volumes
        os_migrate.os_migrate.import_workload_export_volumes:
          auth: "{{ os_migrate_src_auth }}"
          auth_type: "{{ os_migrate_src_auth_type|default(omit) }}"
          region_name: "{{ os_migrate_src_region_name|default(omit) }}"
          validate_certs: "{{ os_migrate_src_validate_certs|default(omit) }}"
          ca_cert: "{{ os_migrate_src_ca_cert|default(omit) }}"
          client_cert: "{{ os_migrate_src_client_cert|default(omit) }}"
          client_key: "{{ os_migrate_src_client_key|default(omit) }}"
          conversion_host:
            "{{ os_src_conversion_host_info.openstack_conversion_host }}"
          data: "{{ item }}"
          log_file: "{{ os_migrate_data_dir }}/{{ prelim.server_name }}.log"
          state_file: "{{ os_migrate_data_dir }}/{{ prelim.server_name }}.state"
          ssh_key_path: "{{ import_workloads_keypair_private_path }}"
        register: volume_map
        when: prelim.changed

      - name: transfer volumes to destination
        os_migrate.os_migrate.import_workload_transfer_volumes:
          auth: "{{ os_migrate_dst_auth }}"
          auth_type: "{{ os_migrate_dst_auth_type|default(omit) }}"
          region_name: "{{ os_migrate_dst_region_name|default(omit) }}"
          validate_certs: "{{ os_migrate_dst_validate_certs|default(omit) }}"
          ca_cert: "{{ os_migrate_dst_ca_cert|default(omit) }}"
          client_cert: "{{ os_migrate_dst_client_cert|default(omit) }}"
          client_key: "{{ os_migrate_dst_client_key|default(omit) }}"
          data: "{{ item }}"
          conversion_host:
            "{{ os_dst_conversion_host_info.openstack_conversion_host }}"
          ssh_key_path: "{{ import_workloads_keypair_private_path }}"
          transfer_uuid: "{{ exports.transfer_uuid }}"
          src_conversion_host_address:
            "{{ os_src_conversion_host_info.openstack_conversion_host.address }}"
          volume_map: "{{ exports.volume_map }}"
          state_file: "{{ os_migrate_data_dir }}/{{ prelim.server_name }}.state"
          log_file: "{{ os_migrate_data_dir }}/{{ prelim.server_name }}.log"
        register: transfer
        when: prelim.changed

      - name: clean up after migration
        os_migrate.os_migrate.import_workload_src_cleanup:
          auth: "{{ os_migrate_src_auth }}"
          auth_type: "{{ os_migrate_src_auth_type|default(omit) }}"
          region_name: "{{ os_migrate_src_region_name|default(omit) }}"
          validate_certs: "{{ os_migrate_src_validate_certs|default(omit) }}"
          ca_cert: "{{ os_migrate_src_ca_cert|default(omit) }}"
          client_cert: "{{ os_migrate_src_client_cert|default(omit) }}"
          client_key: "{{ os_migrate_src_client_key|default(omit) }}"
          data: "{{ item }}"
          conversion_host:
            "{{ os_src_conversion_host_info.openstack_conversion_host }}"
          ssh_key_path: "{{ import_workloads_keypair_private_path }}"
          ssh_user: "{{ conversion_host_ssh_user }}"
          transfer_uuid: "{{ exports.transfer_uuid }}"
          volume_map: "{{ exports.volume_map }}"
          state_file: "{{ os_migrate_data_dir }}/{{ prelim.server_name }}.state"
          log_file: "{{ os_migrate_data_dir }}/{{ prelim.server_name }}.log"
        when: prelim.changed

    rescue:
      - fail:
          msg: "Failed to import {{ item.params.name }}!"
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
    argument_spec = openstack_full_argument_spec(
        data=dict(type="dict", required=True),
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
