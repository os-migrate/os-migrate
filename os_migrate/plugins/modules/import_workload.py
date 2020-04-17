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
module: import_workload

short_description: Import OpenStack instance

extends_documentation_fragment: openstack

version_added: "2.9"

author: "OpenStack tenant migration tools (@os-migrate)"

description:
  - "Import OpenStack instance from an OS-Migrate YAML structure"

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
  dst_conversion_host_id:
    description:
      - ID of the UCI conversion host instance running on the destination OpenStack cloud.
    required: true
    type: str
  dst_conversion_host_address:
    description:
      - IP address of the UCI conversion host instance on the destination OpenStack cloud.
    required: true
    type: str
  src_conversion_host_id:
    description:
      - ID of the UCI conversion host instance running on the source OpenStack cloud.
    required: true
    type: str
  src_conversion_host_address:
    description:
      - IP address of the UCI conversion host instance on the source OpenStack cloud.
    required: true
    type: str
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
  uci_container_image:
    description:
      - ID or name of the conversion host container image to run inside the UCI appliance.
    required: false
    type: str
    default: v2v-conversion-host
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
  os_migrate.os_migrate.os_server_address:
    auth:
        auth_url: https://src-osp:13000/v3
        username: migrate
        password: migrate
        project_domain_id: default
        project_name: migration-source
        user_domain_id: default
    server_id: ce4dda96-5d8e-4b67-aee2-9845cdc943fe
  register: os_src_conversion_host_address

- name: get destination conversion host address
  os_migrate.os_migrate.os_server_address:
    auth:
        auth_url: https://dest-osp:13000/v3
        username: migrate
        password: migrate
        project_domain_id: default
        project_name: migration-destination
        user_domain_id: default
    server_id: 2d2afe57-ace5-4187-8fca-5f10f9059ba1
  register: os_dst_conversion_host_address

- name: import workloads
  os_migrate.os_migrate.import_workload:
    auth:
        auth_url: https://dest-osp:13000/v3
        username: migrate
        password: migrate
        project_domain_id: default
        project_name: migration-destination
        user_domain_id: default
    dst_conversion_host_id: 2d2afe57-ace5-4187-8fca-5f10f9059ba1
    dst_conversion_host_address: "{{ os_dst_conversion_host_address.address }}"
    src_conversion_host_id: ce4dda96-5d8e-4b67-aee2-9845cdc943fe
    src_conversion_host_address: "{{ os_src_conversion_host_address.address }}"
    src_auth:
        auth_url: https://src-osp:13000/v3
        username: migrate
        password: migrate
        project_domain_id: default
        project_name: migration-source
        user_domain_id: default
    ssh_key_path: "{{ os_migrate_ssh_key }}"
    data: "{{ item }}"
  loop: "{{ read_workloads.resources }}"
'''

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.openstack \
    import openstack_full_argument_spec, openstack_cloud_from_module

from ansible_collections.os_migrate.os_migrate.plugins.module_utils import server

import json
import subprocess


def run_module():
    argument_spec = openstack_full_argument_spec(
        dst_conversion_host_id=dict(type='str', required=True),
        dst_conversion_host_address=dict(type='str', required=True),
        src_auth=dict(type='dict', required=True),
        src_auth_type=dict(default=None),
        src_region_name=dict(default=None),
        src_validate_certs=dict(default=None, type='bool'),
        src_conversion_host_id=dict(type='str', required=True),
        src_conversion_host_address=dict(type='str', required=True),
        data=dict(type='dict', required=True),
        ssh_key_path=dict(type='str', default=None),
        uci_container_image=dict(type='str', default='v2v-conversion-host'),
    )

    module = AnsibleModule(
        argument_spec=argument_spec,
    )

    sdk, conn = openstack_cloud_from_module(module)
    src = server.Server.from_data(module.params['data'])
    params, info = src.params_and_info()

    # Do not convert source conversion host!
    if info['id'] == module.params['src_conversion_host_id']:
        module.exit_json(skipped=True, skip_reason='Skipping conversion host.')

    # Assume an existing VM with the same name means it was already migrated.
    # Not necessarily true, but force the operator to delete it if needed.
    if conn.search_servers(params['name']):
        module.exit_json(changed=False, msg='VM already exists on destination!')

    # Make sure source instance is shutdown before proceeding.
    if info['status'] != 'SHUTOFF':
        name = params['name']
        msg = 'Skipping instance {} because it is not in state SHUTOFF!'
        module.exit_json(skipped=True, skip_reason=msg.format(name))

    dst_addr = module.params['dst_conversion_host_address']
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
        vm_name=params['name'],
        transport_method='ssh',
        insecure_connection=not module.params['validate_certs'],
        osp_server_id=module.params['dst_conversion_host_id'],
        osp_source_conversion_vm_id=module.params['src_conversion_host_id'],
        osp_source_vm_id=info['id'],
        osp_destination_project_id=conn.current_project_id,
        osp_flavor_id=params['flavor_name'],
        osp_security_groups_ids=params['security_group_names'],
        uci_container_image=module.params['uci_container_image'],
        ssh_key=ssh_key,
        osp_environment={
            'os_' + key: value for (key, value) in dst_auth.items()},
        osp_source_environment={
            'os_' + key: value for (key, value) in src_auth.items()
        }
    )

    try:  # Create remote temporary directory
        v2v_dir = _dst_ssh(dst_addr, ssh_key_path, ['mktemp -d -t v2v-XXXXXX'])
        sub_dirs = v2v_dir + '/{input,log/uci,lib/uci,tmp}'
        _dst_ssh(dst_addr, ssh_key_path, ['mkdir -p ' + sub_dirs])
    except subprocess.CalledProcessError as e:
        module.fail_json(msg='Unable to create temporary directory for '
                         'virt-v2v-wrapper on destination conversion host! '
                         'Error was: ' + e, changed=False)

    # Write input JSON to /input/conversion.json on destination conversion host
    command = _ssh_preamble(dst_addr, ssh_key_path)
    command.extend(['-T', 'cat > ' + v2v_dir + '/input/conversion.json'])
    try:
        input_json = json.dumps(wrapper_input)
        subprocess.run(command, text=True, input=input_json, check=True)
    except subprocess.CalledProcessError as e:
        module.fail_json(msg='Unable to copy virt-v2v-wrapper parameters '
                         'file to destination conversion host! Error: ' + e,
                         changed=False)

    # Run virt-v2v-wrapper through its UCI container
    try:
        virt_v2v_wrapper = [
            'sudo', 'podman', 'run', '--rm', '--privileged',
            '--volume', '/dev:/dev',
            '--volume', '/var/lock:/var/lock',
            '--volume', '/etc/pki/ca-trust:/etc/pki/ca-trust',
            '--volume', '/opt/vmware-vix-disklib-distrib:/opt/vmware-vix-disklib-distrib',
            '--volume', v2v_dir + ':/data',
            '--volume', v2v_dir + '/log/uci:/var/log/uci',
            '--volume', v2v_dir + '/lib/uci:/var/lib/uci',
            '--volume', v2v_dir + '/tmp:/var/tmp',
            module.params['uci_container_image'],
        ]
        args = _ssh_preamble(dst_addr, ssh_key_path)
        args.extend(virt_v2v_wrapper)
        # Suppress the tons of logging from virt-v2v-wrapper stdout/stderr
        subprocess.check_call(args, stdout=subprocess.DEVNULL,
                              stderr=subprocess.DEVNULL)
    except subprocess.CalledProcessError as e:
        msg = 'Failed to migrate {}! Error was: {}'
        module.fail_json(msg=msg.format(params['name'], e), changed=True)

    module.exit_json(changed=True)  # TODO: check actual wrapper state


def _ssh_preamble(address, key_path):
    return [
        'ssh',
        '-i', key_path,
        '-o', 'BatchMode=yes',
        '-o', 'StrictHostKeyChecking=no',
        '-o', 'ConnectTimeout=10',
        'cloud-user@' + address
    ]


def _dst_ssh(address, key_path, command):
    args = _ssh_preamble(address, key_path)
    args.extend(command)
    return subprocess.check_output(args).decode('utf-8').strip()


def main():
    run_module()


if __name__ == '__main__':
    main()
