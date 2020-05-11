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
module: import_workload_prelim

short_description: Preliminary actions required to import an OpenStack instance

extends_documentation_fragment: openstack

version_added: "2.9"

author: "OpenStack tenant migration tools (@os-migrate)"

description:
  - "Import OpenStack instance from an OS-Migrate YAML structure."
  - "This module communicates with the OpenStack API and sets up variables for the import_workload module."

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
  validate_certs:
    description:
      - Validate HTTPS certificates when logging in to OpenStack.
    required: false
    type: bool
  dst_conversion_host:
    description:
      - Dictionary with information about the destination conversion host (address, status, name, id)
    required: true
    type: dict
  src_conversion_host:
    description:
      - Dictionary with information about the source conversion host (address, status, name, id)
    required: true
    type: dict
  src_auth:
    description:
      - Dictionary with parameters for chosen auth type on the source cloud.
    required: true
    type: dict
  src_auth_type:
    description:
      - Auth type plugin for source OpenStack cloud. Can be omitted if using password authentication.
    required: false
    type: str
  src_region_name:
    description:
      - Source OpenStack region name. Can be omitted if using default region.
    required: false
    type: str
  src_validate_certs:
    description:
      - Validate HTTPS certificates when logging in to source OpenStack cloud.
    required: false
    type: bool
  ssh_key_path:
    description:
      - Path to an SSH private key authorized on both source and destination clouds.
    required: true
    type: str
  data:
    description:
      - Data structure with server parameters as loaded from OS-Migrate workloads YAML file.
    required: true
    type: dict
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
      dst_conversion_host: "{{ os_dst_conversion_host_info.openstack_conversion_host }}"
      src_conversion_host: "{{ os_src_conversion_host_info.openstack_conversion_host }}"
      src_auth:
          auth_url: https://src-osp:13000/v3
          username: migrate
          password: migrate
          project_domain_id: default
          project_name: migration-source
          user_domain_id: default
      src_validate_certs: False
      ssh_key_path: "/path/to/migration.key"
      data: "{{ item }}"
    register: prelim

  - debug:
      msg:
        - "{{ prelim.server_name }} remote log directory: {{ prelim.v2v_dir }}"
        - "{{ prelim.server_name }} log file: {{ prelim.v2v_log }}"
        - "{{ prelim.server_name }} progress state file: {{ prelim.v2v_state }}"
    when: prelim.changed

  - name: import one workload
    os_migrate.os_migrate.import_workload:
      dst_addr: "{{ prelim.dst_addr }}"
      server_name: "{{ prelim.server_name }}"
      ssh_key_path: "/path/to/migration.key"
      v2v_dir: "{{ prelim.v2v_dir }}"
    when: prelim.changed

  rescue:
    - debug:
        msg: "Failed to import {{ prelim.server_name }}!"
'''

RETURN = '''
dst_addr:
  description: External IP address of destination conversion host, as a convenience.
  returned: Only after successful connection to destination cloud.
  type: str
  sample: 10.2.34.137
server_name:
  description: The name of the target instance from params, as a convenience.
  returned: Only after successful connection to destination cloud.
  type: str
  sample: migration-vm
v2v_dir:
  description: Temporary working directory for this migration, on the destination conversion host.
  returned: Only after successful creation.
  type: str
  sample: /tmp/v2v-dT5Hzz
v2v_log:
  description: Direct link to remote virt-v2v-wrapper log file, formatted for SCP.
  returned: Only on success.
  type: str
  sample: cloud-user@10.2.34.137:/tmp/v2v-dT5Hzz/log/uci/virt-v2v-wrapper.log
v2v_state:
  description: Direct link to remote virt-v2v-wrapper transfer progress file, formatted for SCP.
  returned: Only on success.
  type: str
  sample: cloud-user@10.2.34.137:/tmp/v2v-dT5Hzz/lib/uci/state.json
'''

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.openstack \
    import openstack_full_argument_spec, openstack_cloud_from_module

from ansible_collections.os_migrate.os_migrate.plugins.module_utils import server

from ansible_collections.os_migrate.os_migrate.plugins.module_utils.workload_common \
    import dst_ssh, ssh_preamble

import json
import subprocess


def run_module():
    argument_spec = openstack_full_argument_spec(
        dst_conversion_host=dict(type='dict', required=True),
        src_conversion_host=dict(type='dict', required=True),
        src_auth=dict(type='dict', required=True),
        src_auth_type=dict(default=None),
        src_region_name=dict(default=None),
        src_validate_certs=dict(default=None, type='bool'),
        data=dict(type='dict', required=True),
        ssh_key_path=dict(type='str', default=None),
    )

    result = dict(
        changed=False,
    )

    module = AnsibleModule(
        argument_spec=argument_spec,
    )

    sdk, conn = openstack_cloud_from_module(module)
    src = server.Server.from_data(module.params['data'])
    params, info = src.params_and_info()

    dst_addr = module.params['dst_conversion_host']['address']
    result['dst_addr'] = dst_addr
    server_name = params['name']
    result['server_name'] = server_name

    # Do not convert source conversion host!
    if info['id'] == module.params['src_conversion_host']['id']:
        module.exit_json(skipped=True, skip_reason='Skipping conversion host.',
                         **result)

    # Assume an existing VM with the same name means it was already migrated.
    # Not necessarily true, but force the operator to delete it if needed.
    if conn.search_servers(server_name):
        module.exit_json(msg='VM already exists on destination!', **result)

    # Make sure source instance is shutdown before proceeding.
    if info['status'] != 'SHUTOFF':
        name = server_name
        msg = 'Skipping instance {} because it is not in state SHUTOFF!'
        module.exit_json(skipped=True, skip_reason=msg.format(name), **result)

    dst_auth = module.params['auth']
    src_auth = module.params['src_auth']
    ssh_key_path = module.params['ssh_key_path']

    # Copy the contents of the SSH key as a virt-v2v-wrapper parameter
    with open(ssh_key_path, 'r') as ssh_key_file:
        ssh_key = ssh_key_file.read()
        if not ssh_key.endswith('\n'):
            ssh_key += '\n'

    # Create JSON input for virt-v2v-wrapper
    wrapper_input = dict(
        vm_name=server_name,
        transport_method='ssh',
        insecure_connection=not module.params['validate_certs'],
        osp_server_id=module.params['dst_conversion_host']['id'],
        osp_source_conversion_vm_id=module.params['src_conversion_host']['id'],
        osp_source_vm_id=info['id'],
        osp_destination_project_id=conn.current_project_id,
        osp_flavor_id=params['flavor_name'],
        osp_security_groups_ids=params['security_group_names'],
        ssh_key=ssh_key,
        osp_environment={
            'os_' + key: value for (key, value) in dst_auth.items()},
        osp_source_environment={
            'os_' + key: value for (key, value) in src_auth.items()
        }
    )

    try:  # Create remote temporary directory
        v2v_dir = dst_ssh(dst_addr, ssh_key_path, ['mktemp -d -t v2v-XXXXXX'])
        sub_dirs = v2v_dir + '/{input,log/uci,lib/uci,tmp}'
        dst_ssh(dst_addr, ssh_key_path, ['mkdir -p ' + sub_dirs])
        result['v2v_dir'] = v2v_dir
    except subprocess.CalledProcessError as e:
        module.fail_json(msg='Unable to create temporary directory for '
                         'virt-v2v-wrapper on destination conversion host! '
                         'Error was: ' + e, **result)

    # Write input JSON to /input/conversion.json on destination conversion host
    command = ssh_preamble(dst_addr, ssh_key_path)
    command.extend(['-T', 'cat > ' + v2v_dir + '/input/conversion.json'])
    try:
        input_json = json.dumps(wrapper_input)
        subprocess.run(command, text=True, input=input_json, check=True)
    except subprocess.CalledProcessError as e:
        module.fail_json(msg='Unable to copy virt-v2v-wrapper parameters '
                         'file to destination conversion host! Error: ' + e,
                         **result)

    remote_dir = 'cloud-user@' + dst_addr + ':' + v2v_dir
    result['v2v_log'] = remote_dir + '/log/uci/virt-v2v-wrapper.log'
    result['v2v_state'] = remote_dir + '/lib/uci/state.json'
    result['changed'] = True

    module.exit_json(**result)


def main():
    run_module()


if __name__ == '__main__':
    main()
