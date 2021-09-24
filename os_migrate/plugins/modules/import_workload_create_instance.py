#!/usr/bin/python


from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

ANSIBLE_METADATA = {
    'metadata_version': '1.1',
    'status': ['preview'],
    'supported_by': 'community'
}

DOCUMENTATION = '''
---
module: import_workload_create_instance

short_description: Create NBD exports of OpenStack volumes

extends_documentation_fragment: openstack

version_added: "2.9.0"

author: "OpenStack tenant migration tools (@os-migrate)"

description:
  - "Take an instance from an OS-Migrate YAML structure, and export its volumes over NBD."

options:
  auth:
    description:
      - Dictionary with parameters for chosen auth type on the destination cloud.
    required: true
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
      - Ignored. Present for backwards compatibility.
    required: false
    type: raw
  validate_certs:
    description:
      - Validate HTTPS certificates when logging in to OpenStack.
    required: false
    type: bool
  data:
    description:
      - Data structure with server parameters as loaded from OS-Migrate workloads YAML file.
    required: true
    type: dict
  block_device_mapping:
    description:
      - A block_device_mapping_v2 structure from the transfer_volumes module.
      - Used to attach destination volumes to the new instance in the right order.
    required: true
    type: list
    elements: dict
'''

EXAMPLES = '''
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
      validate_certs: False
      src_conversion_host: "{{ os_src_conversion_host_info.openstack_conversion_host }}"
      src_auth:
          auth_url: https://src-osp:13000/v3
          username: migrate
          password: migrate
          project_domain_id: default
          project_name: migration-source
          user_domain_id: default
      src_validate_certs: False
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
      ssh_key_path: "{{ os_migrate_conversion_keypair_private_path }}"
    register: exports
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
      ssh_key_path: "{{ os_migrate_conversion_keypair_private_path }}"
      transfer_uuid: "{{ exports.transfer_uuid }}"
      src_conversion_host_address:
        "{{ os_src_conversion_host_info.openstack_conversion_host.address }}"
      volume_map: "{{ exports.volume_map }}"
      state_file: "{{ os_migrate_data_dir }}/{{ prelim.server_name }}.state"
      log_file: "{{ os_migrate_data_dir }}/{{ prelim.server_name }}.log"
    register: transfer
    when: prelim.changed

  - name: create destination instance
    os_migrate.os_migrate.import_workload_create_instance:
      auth: "{{ os_migrate_dst_auth }}"
      auth_type: "{{ os_migrate_dst_auth_type|default(omit) }}"
      region_name: "{{ os_migrate_dst_region_name|default(omit) }}"
      validate_certs: "{{ os_migrate_dst_validate_certs|default(omit) }}"
      ca_cert: "{{ os_migrate_dst_ca_cert|default(omit) }}"
      client_cert: "{{ os_migrate_dst_client_cert|default(omit) }}"
      client_key: "{{ os_migrate_dst_client_key|default(omit) }}"
      data: "{{ item }}"
      block_device_mapping: "{{ transfer.block_device_mapping }}"
    register: os_migrate_destination_instance
    when: prelim.changed

  rescue:
    - fail:
        msg: "Failed to import {{ item.params.name }}!"
'''

RETURN = '''
server_id:
  description: The ID of the newly created server.
  returned: On successful creation of migrated server on destination cloud.
  type: str
  sample: 059635b7-451f-4a64-978a-7c2e9e4c15ff
'''

from ansible.module_utils.basic import AnsibleModule
# Import openstack module utils from ansible_collections.openstack.cloud.plugins as per ansible 3+
try:
    from ansible_collections.openstack.cloud.plugins.module_utils.openstack \
        import openstack_full_argument_spec, openstack_cloud_from_module
except ImportError:
    # If this fails fall back to ansible < 3 imports
    from ansible.module_utils.openstack \
        import openstack_full_argument_spec, openstack_cloud_from_module

from ansible_collections.os_migrate.os_migrate.plugins.module_utils import server


def run_module():
    argument_spec = openstack_full_argument_spec(
        auth=dict(type='dict', no_log=True, required=True),
        data=dict(type='dict', required=True),
        block_device_mapping=dict(type='list', required=True, elements='dict'),
    )

    result = dict(
        changed=False,
    )

    module = AnsibleModule(
        argument_spec=argument_spec,
    )

    sdk, conn = openstack_cloud_from_module(module)
    block_device_mapping = module.params['block_device_mapping']

    ser_server = server.Server.from_data(module.params['data'])
    sdk_server = ser_server.create(conn, block_device_mapping)
    # Some info (e.g. flavor ID) will only become available after the
    # server is in ACTIVE state, we need to wait for it.
    sdk_server = conn.compute.wait_for_server(sdk_server, failures=['ERROR'], wait=600)
    dst_ser_server = server.Server.from_sdk(conn, sdk_server)

    if sdk_server:
        result['changed'] = True
        result['server'] = dst_ser_server.data
        result['server_id'] = sdk_server.id

    module.exit_json(**result)


def main():
    run_module()


if __name__ == '__main__':
    main()
