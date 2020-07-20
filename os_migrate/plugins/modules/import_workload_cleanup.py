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
module: import_workload_cleanup

short_description: Clean up temporary volumes after a workload migration

extends_documentation_fragment: openstack

version_added: "2.9"

author: "OpenStack tenant migration tools (@os-migrate)"

description:
  - Remove any temporary snapshots or volumes associated with this workload migration.

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
        plugin will use the 'accessIPv4' property of the conversion host instance.
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
      ssh_key_path: "{{ os_migrate_conversion_keypair_private_path }}"
      transfer_uuid: "{{ exports.transfer_uuid }}"
      src_conversion_host_address:
        "{{ os_src_conversion_host_info.openstack_conversion_host.address }}"
      volume_map: "{{ exports.volume_map }}"
      state_file: "{{ os_migrate_data_dir }}/{{ prelim.server_name }}.state"
      log_file: "{{ os_migrate_data_dir }}/{{ prelim.server_name }}.log"
    register: transfer
    when: prelim.changed

  - name: clean up after migration
    os_migrate.os_migrate.import_workload_cleanup:
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
      ssh_key_path: "{{ os_migrate_conversion_keypair_private_path }}"
      ssh_user: "{{ os_migrate_conversion_host_ssh_user }}"
      transfer_uuid: "{{ exports.transfer_uuid }}"
      volume_map: "{{ exports.volume_map }}"
      state_file: "{{ os_migrate_data_dir }}/{{ prelim.server_name }}.state"
      log_file: "{{ os_migrate_data_dir }}/{{ prelim.server_name }}.log"
    when: prelim.changed

  rescue:
    - fail:
        msg: "Failed to import {{ item.params.name }}!"
'''

RETURN = '''
'''

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.openstack \
    import openstack_full_argument_spec, openstack_cloud_from_module

from ansible_collections.os_migrate.os_migrate.plugins.module_utils import server

from ansible_collections.os_migrate.os_migrate.plugins.module_utils.workload_common \
    import use_lock, ATTACH_LOCK_FILE_SOURCE, DEFAULT_TIMEOUT, OpenStackHostBase

import subprocess
import time


class OpenStackSourceHostCleanup(OpenStackHostBase):
    """ Removes temporary migration volumes and snapshots from source cloud. """

    def __init__(self, openstack_connection, source_conversion_host_id,
                 ssh_key_path, ssh_user, source_instance_id, transfer_uuid,
                 volume_map, source_conversion_host_address=None, state_file=None,
                 log_file=None):

        super(OpenStackSourceHostCleanup, self).__init__(
            openstack_connection,
            source_conversion_host_id,
            ssh_key_path,
            ssh_user,
            transfer_uuid,
            conversion_host_address=source_conversion_host_address,
            state_file=state_file,
            log_file=log_file
        )

        # Required unique parameters:
        # source_instance_id: ID of VM that was migrated from the source
        # volume_map: Volume map returned by export_volumes module
        self.source_instance_id = source_instance_id
        self.volume_map = volume_map

        # This will make _release_ports clean up ports from the export module
        for path, mapping in volume_map.items():
            port = mapping['port']
            self.claimed_ports.append(port)

    def _source_vm(self):
        """
        Changes to the VM returned by get_server_by_id are not necessarily
        reflected in existing objects, so just get a new one every time.
        """
        return self.conn.get_server_by_id(self.source_instance_id)

    def close_exports(self):
        """ Put the source VM's volumes back where they were. """
        self._converter_close_exports()
        self._detach_volumes_from_converter()
        self._attach_data_volumes_to_source()

    def _converter_close_exports(self):
        """
        SSH to source conversion host and close the NBD export process.
        """
        self.log.info('Stopping exports from source conversion host...')
        try:
            pattern = "'" + self.transfer_uuid + "'"
            pids = self.shell.cmd_out(['pgrep', '-f', pattern]).split('\n')
            if len(pids) > 0:
                self.log.debug('Stopping NBD export PIDs (%s)', str(pids))
                try:
                    self.shell.cmd_out(['sudo', 'pkill', '-f', pattern])
                except subprocess.CalledProcessError as err:
                    self.log.debug('Error stopping exports! %s', str(err))
        except subprocess.CalledProcessError as err:
            self.log.debug('Unable to get remote NBD PID! %s', str(err))

        self._release_ports()

    def _volume_still_attached(self, volume, vm):
        """ Check if a volume is still attached to a VM. """
        for attachment in volume.attachments:
            if attachment.server_id == vm.id:
                return True
        return False

    @use_lock(ATTACH_LOCK_FILE_SOURCE)
    def _detach_volumes_from_converter(self):
        """ Detach volumes from conversion host. """
        self.log.info('Removing volumes from conversion host.')
        converter = self._converter()
        for path, mapping in self.volume_map.items():
            volume = self.conn.get_volume_by_id(mapping['source_id'])
            self.log.info('Inspecting volume %s', volume.id)
            if mapping['source_dev'] is None:
                self.log.info('Volume is not attached to conversion host, '
                              'skipping detach.')
                continue
            self.conn.detach_volume(server=converter, volume=volume,
                                    timeout=DEFAULT_TIMEOUT, wait=True)
            for second in range(DEFAULT_TIMEOUT):
                converter = self._converter()
                volume = self.conn.get_volume_by_id(mapping['source_id'])
                if not self._volume_still_attached(volume, converter):
                    break
                time.sleep(1)
            else:
                raise RuntimeError('Timed out waiting to detach volumes from '
                                   'source conversion host!')

    def _attach_data_volumes_to_source(self):
        """ Clean up the copy of the root volume and reattach data volumes. """
        self.log.info('Re-attaching volumes to source VM...')
        for path, mapping in sorted(self.volume_map.items()):
            if path == '/dev/vda':
                # Delete the temporary copy of the source root disk
                self.log.info('Removing copy of root volume')
                self.conn.delete_volume(name_or_id=mapping['source_id'],
                                        wait=True, timeout=DEFAULT_TIMEOUT)

                # Remove the root volume snapshot
                if mapping['snap_id']:
                    self.log.info('Deleting temporary root device snapshot')
                    self.conn.delete_volume_snapshot(
                        timeout=DEFAULT_TIMEOUT, wait=True,
                        name_or_id=mapping['snap_id'])

                # Remove root image copy, for image-launched instances
                if mapping['image_id']:
                    self.log.info('Deleting temporary root device image')
                    self.conn.delete_image(
                        timeout=DEFAULT_TIMEOUT, wait=True,
                        name_or_id=mapping['image_id'])
            else:
                # Attach data volumes back to source VM
                volume = self.conn.get_volume_by_id(mapping['source_id'])
                sourcevm = self._source_vm()
                try:
                    self._get_attachment(volume, sourcevm)
                except RuntimeError:
                    self.log.info('Attaching %s back to source VM', volume.id)
                    self.conn.attach_volume(volume=volume, server=sourcevm,
                                            wait=True, timeout=DEFAULT_TIMEOUT)
                else:
                    self.log.info('Volume %s is already attached to source VM',
                                  volume.id)
                    continue


def run_module():
    argument_spec = openstack_full_argument_spec(
        data=dict(type='dict', required=True),
        conversion_host=dict(type='dict', required=True),
        ssh_key_path=dict(type='str', required=True),
        ssh_user=dict(type='str', required=True),
        transfer_uuid=dict(type='str', required=True),
        volume_map=dict(type='dict', required=True),
        src_conversion_host_address=dict(type='str', default=None),
        state_file=dict(type='str', default=None),
        log_file=dict(type='str', default=None),
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

    # Required parameters
    source_conversion_host_id = module.params['conversion_host']['id']
    ssh_key_path = module.params['ssh_key_path']
    ssh_user = module.params['ssh_user']
    source_instance_id = info['id']
    transfer_uuid = module.params['transfer_uuid']
    volume_map = module.params['volume_map']

    # Optional parameters
    source_conversion_host_address = \
        module.params.get('src_conversion_host_address', None)
    state_file = module.params.get('state_file', None)
    log_file = module.params.get('log_file', None)

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
        log_file=log_file
    )
    host_cleanup.close_exports()

    module.exit_json(**result)


def main():
    run_module()


if __name__ == '__main__':
    main()
