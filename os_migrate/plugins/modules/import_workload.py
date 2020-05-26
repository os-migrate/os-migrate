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

version_added: "2.9"

author: "OpenStack tenant migration tools (@os-migrate)"

description:
  - "Import OpenStack instance from an OS-Migrate YAML structure"
  - "This module connects to the destination conversion host and runs virt-v2v-wrapper."
  - "Intended to run only from the output of import_workload_prelim."
  - "This way, paths to debug logs and progress state can be provided before transferring any bulk data."

options:
  dst_addr:
    description:
      - External IP address of destination conversion host.
    required: True
    type: str
  server_name:
    description:
      - Name of the OpenStack instance currently being migrated
    required: True
    type: str
  ssh_key_path:
    description:
      - Path to an SSH private key authorized on both source and destination clouds.
    required: true
    type: str
  transfer_log:
    description:
      - Path to a log file to store mixed stdout/stderr from running the UCI container.
    required: false
    type: str
  uci_container_image:
    description:
      - ID or name of the conversion host container image to run inside the UCI appliance.
    required: false
    type: str
    default: v2v-conversion-host
  v2v_dir:
    description:
      - Working directory for the current instance migration, on the destination conversion host.
    required: true
    type: str
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
      transfer_log: "/path/to/migrationdata/{{ prelim.server_name }}.log"
      server_name: "{{ prelim.server_name }}"
      ssh_key_path: "/path/to/migration.key"
      v2v_dir: "{{ prelim.v2v_dir }}"
    when: prelim.changed

  rescue:
    - debug:
        msg: "Failed to import {{ prelim.server_name }}!"
'''

from ansible.module_utils.basic import AnsibleModule

from ansible_collections.os_migrate.os_migrate.plugins.module_utils.workload_common \
    import ssh_preamble

import subprocess


def run_module():
    argument_spec = dict(
        dst_addr=dict(type='str', required=True),
        server_name=dict(type='str', required=True),
        ssh_key_path=dict(type='str', default=None),
        transfer_log=dict(type='str', default=None),
        uci_container_image=dict(type='str', default='v2v-conversion-host'),
        v2v_dir=dict(type='str', required=True),
    )

    module = AnsibleModule(
        argument_spec=argument_spec,
    )

    dst_addr = module.params['dst_addr']
    server_name = module.params['server_name']
    ssh_key_path = module.params['ssh_key_path']
    uci_container_image = module.params['uci_container_image']
    v2v_dir = module.params['v2v_dir']

    # Run virt-v2v-wrapper through its UCI container
    try:
        output_log = subprocess.DEVNULL
        if module.params['transfer_log']:
            try:
                output_log = open(module.params['transfer_log'], 'a')
            except OSError as e:
                msg = 'Failed to open log file for {}! Error was: {}'
                module.fail_json(changed=False, msg=msg.format(server_name, e))

        # TODO:FIXME
        # We need to remove the vddk library dependence in the near future.
        # Remove:
        # '--volume', '/opt/vmware-vix-disklib-distrib:/opt/vmware-vix-disklib-distrib',
        virt_v2v_wrapper = [
            'sudo', 'podman', 'run', '--rm', '--privileged', '--net', 'host',
            '--volume', '/dev:/dev',
            '--volume', '/var/lock:/var/lock',
            '--volume', '/etc/pki/ca-trust:/etc/pki/ca-trust',
            '--volume', '/opt/vmware-vix-disklib-distrib:/opt/vmware-vix-disklib-distrib',
            '--volume', v2v_dir + ':/data',
            '--volume', v2v_dir + '/log/uci:/var/log/uci',
            '--volume', v2v_dir + '/lib/uci:/var/lib/uci',
            '--volume', v2v_dir + '/tmp:/var/tmp',
            uci_container_image,
        ]
        args = ssh_preamble(dst_addr, ssh_key_path)
        args.extend(virt_v2v_wrapper)
        # Suppress the tons of logging from virt-v2v-wrapper stdout/stderr
        subprocess.check_call(args, stdout=output_log, stderr=output_log)
    except subprocess.CalledProcessError as e:
        # We fetch the failing method output
        if output_log != subprocess.DEVNULL and not output_log.closed:
            output_log.close()
        logs_data = "Empty"
        if module.params['transfer_log']:
            logs_data = open(module.params['transfer_log'], 'r').read()

        # We get the content of the log file
        get_logs = [
            'cat', v2v_dir + '/log/uci/virt-v2v-wrapper.log',
        ]
        args = ssh_preamble(dst_addr, ssh_key_path)
        args.extend(get_logs)
        output_log = open(module.params['transfer_log'], 'w')
        subprocess.check_call(args, stdout=output_log, stderr=output_log)
        if output_log != subprocess.DEVNULL and not output_log.closed:
            output_log.close()
        v2v_log = open(module.params['transfer_log'], 'r').read()

        msg = 'Failed to migrate {}! \n Error was: \n {} \n---\n Output Log: \n {} \n---\n v2v log: \n {}'
        module.fail_json(msg=msg.format(server_name, e, logs_data, v2v_log), changed=True, v2v_dir=v2v_dir)
    finally:
        if output_log != subprocess.DEVNULL and not output_log.closed:
            output_log.close()

    module.exit_json(changed=True, v2v_dir=v2v_dir)


def main():
    run_module()


if __name__ == '__main__':
    main()
