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
module: import_workload_transfer_volumes

short_description: Create destination volumes and transfer source data.

extends_documentation_fragment: openstack

version_added: "2.9.0"

author: "OpenStack tenant migration tools (@os-migrate)"

description:
  - "Connect to the destination cloud to create new volumes, and copy data from the source cloud."

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
      - Dictionary with information about the destination conversion host (address, status, name, id)
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
      - Provided by the import_workloads_export_volumes module.
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
        plugin will use the 'accessIPv4' property of the conversion host instance.
    required: false
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
      ssh_user: "{{ os_migrate_conversion_host_ssh_user }}"
      transfer_uuid: "{{ exports.transfer_uuid }}"
      src_conversion_host_address:
        "{{ os_src_conversion_host_info.openstack_conversion_host.address }}"
      volume_map: "{{ exports.volume_map }}"
      state_file: "{{ os_migrate_data_dir }}/{{ prelim.server_name }}.state"
      log_file: "{{ os_migrate_data_dir }}/{{ prelim.server_name }}.log"
    register: volume_map
    when: prelim.changed

  rescue:
    - fail:
        msg: "Failed to import {{ item.params.name }}!"
'''

RETURN = '''
block_device_mapping:
  description:
    - A block_device_mapping_v2 structure for use in OpenStack's create_server().
    - Used to attach destination volumes to the new instance in the right order.
  returned: Only after successfully transferring volumes from the source cloud.
  type: dict
  sample: [{'device_name': 'vdb', 'uuid': 'fa45e86f-e22e-4128-9b01-da63ed11b33d', 'source_type': 'volume'}]
volume_map:
  description:
    - Updated mapping of source volume devices to NBD export URLs.
    - Takes the input volume_map and fills out the destination-specific fields.
  returned: Only after successfully transferring volumes from the source cloud.
  type: dict
  sample:
    "volume_map": {
        "/dev/vda": {
            "bootable": true,
            "dest_dev": "/dev/vdc",
            "dest_id": "3b7a57d7-8210-47f9-b592-a6627ae52d13",
            "image_id": null,
            "name": "migration-vm-boot",
            "port": 49196,
            "progress": 100.0,
            "size": 10,
            "snap_id": "564398da-3e39-462d-93aa-aa5b7ea8ea61",
            "source_dev": "/dev/vdat",
            "source_id": "059635b7-451f-4a64-978a-7c2e9e4c15ff",
            "url": "nbd://localhost:49180/9b8a64b3-c976-4103-b34e-995e4ab9f57b"
        }
    }

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
from ansible_collections.os_migrate.os_migrate.plugins.module_utils.server_volume \
    import ServerVolume

from ansible_collections.os_migrate.os_migrate.plugins.module_utils.workload_common \
    import OpenStackHostBase, RemoteShell, use_lock, ATTACH_LOCK_FILE_DESTINATION, DEFAULT_TIMEOUT, DEVNULL

import errno
import fcntl
import os
import re
import subprocess
import time


class OpenStackDestinationHost(OpenStackHostBase):
    def __init__(self, openstack_connection, destination_conversion_host_id,
                 ssh_key_path, ssh_user, transfer_uuid, source_conversion_host_address,
                 volume_map, ser_server, destination_conversion_host_address=None,
                 state_file=None, log_file=None, timeout=DEFAULT_TIMEOUT):

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
        self.qemu_progress_re = re.compile(r'\((\d+\.\d+)/100%\)')

        # SSH tunnel process
        self.forwarding_process = None
        self.forwarding_process_command = None

        self.ser_server = ser_server

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

    def _create_forwarding_process(self):
        """
        Find free ports on the destination conversion host and set up SSH
        forwarding to the NBD ports listening on the source conversion host.
        """
        # It is expected that key authorization has already been set up from
        # the destination conversion host to the source conversion host!
        source_shell = RemoteShell(self.source_conversion_host_address,
                                   ssh_user=self.shell.ssh_user)
        forward_ports = ['-N', '-T']
        for path, mapping in self.volume_map.items():
            port = self._find_free_port()
            forward = f"{port}:localhost:{mapping['port']}"
            forward_ports.extend(['-L', forward])
            url = 'nbd://localhost:' + str(port) + '/' + self.transfer_uuid
            self.volume_map[path]['url'] = url
        command = source_shell.ssh_preamble()
        command.extend(forward_ports)
        self.log.debug('SSH forwarding command: %s', ' '.join(command))
        self.forwarding_process = self.shell.cmd_sub(command)
        self.forwarding_process_command = ' '.join(command)

        # Check qemu-img info on all the disks to make sure everything is ready
        self.log.info('Waiting for valid qemu-img info on all exports...')
        pending_disks = set(self.volume_map.keys())
        for second in range(self.timeout):
            try:
                for disk in pending_disks.copy():
                    mapping = self.volume_map[disk]
                    url = mapping['url']
                    cmd = ['qemu-img', 'info', url]
                    image_info = self.shell.cmd_out(cmd)
                    self.log.info('qemu-img info for %s: %s', disk, image_info)
                    pending_disks.remove(disk)
            except subprocess.CalledProcessError as error:
                self.log.info('Got exception: %s', error)
                self.log.info('Trying again.')
                time.sleep(1)
            else:
                self.log.info('All volume exports ready.')
                break
        else:
            raise RuntimeError('Timed out starting nbdkit exports!')

    def _stop_forwarding_process(self):
        self.log.info('Stopping export forwarding on source conversion host...')
        self.log.debug('(PID was %s)', self.forwarding_process.pid)
        if self.forwarding_process:
            self.forwarding_process.terminate()

        if self.forwarding_process_command:
            self.log.info('Stopping forwarding from source conversion host...')
            try:
                pattern = 'pgrep -f "' + self.forwarding_process_command + '"'
                pids = self.shell.cmd_out([pattern]).split('\n')
                for pid in pids:  # There should really only be one of these
                    try:
                        out = self.shell.cmd_out(['sudo', 'kill', pid])
                        self.log.debug('Stopped forwarding PID (%s). %s',
                                       pid, out)
                    except subprocess.CalledProcessError as err:
                        self.log.debug('Unable to stop PID %s! %s',
                                       pid, str(err))
            except subprocess.CalledProcessError as err:
                self.log.debug('Unable to get forwarding PID! %s', str(err))

    def _create_destination_volumes(self):
        """
        Volume mapping step 5: create new volumes on the destination OpenStack,
        and fill in dest_id with the new volumes.
        """
        self.log.info('Creating volumes on destination cloud')
        volumes = list(map(ServerVolume.from_data, self.ser_server.params()['volumes']))
        src_id_volumes = {vol.info()['id']: vol for vol in volumes}
        for path, mapping in self.volume_map.items():
            source_id = mapping['source_id']
            sdk_params = {
                'name': mapping['name'],
                'bootable': mapping['bootable'],
                'size': mapping['size'],
                'wait': True,
                'timeout': self.timeout,
            }
            if source_id in src_id_volumes:
                sdk_params.update(src_id_volumes[source_id].sdk_params(self.conn))
            elif path == '/dev/vda':
                # This code path is exercised when the source VM has
                # no boot volume but is being migrated with
                # `boot_disk_copy: true` and a boot volume is being
                # created in the destination.
                # `None` value in boot_volume_params means we do not
                # want to override that parameter.
                boot_volume_params_defined = \
                    dict(filter(lambda item: item[1] is not None,
                                self.ser_server.migration_params()['boot_volume_params'].items()))
                sdk_params.update(boot_volume_params_defined)
            new_volume = self.conn.create_volume(**sdk_params)
            self.volume_map[path]['dest_id'] = new_volume.id

    @use_lock(ATTACH_LOCK_FILE_DESTINATION)
    def _attach_destination_volumes(self):
        """
        Volume mapping step 6: attach the new destination volumes to the
        destination conversion host. Fill in the destination device name.
        """
        def update_dest(volume_mapping, dev_path):
            volume_mapping['dest_dev'] = dev_path
            return volume_mapping

        def volume_id(volume_mapping):
            return volume_mapping['dest_id']

        self._attach_volumes(self.conn, 'destination', (self._converter,
                                                        self.shell.cmd_out,
                                                        update_dest,
                                                        volume_id))

    def _convert_destination_volumes(self):
        """
        Finally run the commands to copy the exported source volumes to the
        local destination volumes. Attempt to sparsify the volumes to minimize
        the amount of data sent over the network.
        """
        self.log.info('Converting volumes...')
        for path, mapping in self.volume_map.items():
            self.log.info('Converting source VM\'s %s: %s', path, str(mapping))
            devname = os.path.basename(mapping['dest_dev'])
            overlay = '/tmp/' + devname + '-' + self.transfer_uuid + '.qcow2'

            def _log_convert(source_disk, source_format, mapping):
                """ Write qemu-img convert progress to the wrapper log. """
                self.log.info('Copying volume data...')
                cmd = ['sudo', 'qemu-img', 'convert', '-p', '-f', source_format,
                       '-O', 'host_device', source_disk, mapping['dest_dev']]
                # Non-blocking output processing stolen from pre_copy.py
                img_sub = self.shell.cmd_sub(cmd,
                                             stdout=subprocess.PIPE,
                                             stderr=subprocess.STDOUT,
                                             stdin=DEVNULL,
                                             universal_newlines=True, bufsize=1)
                flags = fcntl.fcntl(img_sub.stdout, fcntl.F_GETFL)
                flags |= os.O_NONBLOCK
                fcntl.fcntl(img_sub.stdout, fcntl.F_SETFL, flags)
                buf = b''
                while img_sub.poll() is None:
                    try:
                        buf += os.read(img_sub.stdout.fileno(), 1)
                    except (IOError, OSError) as err:
                        if err.errno != errno.EAGAIN:
                            raise
                        time.sleep(1)
                        continue
                    if buf:
                        try:
                            matches = self.qemu_progress_re.search(buf.decode())
                            if matches is not None:
                                progress = float(matches.group(1))
                                self._update_progress(path, progress)
                                buf = b''
                        except ValueError:
                            self.log.debug('No match yet. %s', str(buf))
                    else:
                        time.sleep(1)
                self.log.info('Conversion return code: %d', img_sub.returncode)
                if img_sub.returncode != 0:
                    try:
                        out = img_sub.stdout.read()
                    except (IOError, OSError) as err:
                        self.log.debug('Error reading stderr? %s', str(err))
                    raise RuntimeError('Failed to convert volume! ' + out)
                # Just in case qemu-img returned before readline got to 100%
                self._update_progress(path, 100.0)

            try:
                self.log.info('Attempting initial sparsify...')
                environment = os.environ.copy()
                environment['LIBGUESTFS_BACKEND'] = 'direct'

                cmd = ['sudo', 'qemu-img', 'create', '-f', 'qcow2', '-b',
                       mapping['url'], '-F', 'raw', overlay]
                out = self.shell.cmd_out(cmd)
                self.log.info('Overlay output: %s', out)

                cmd = ['sudo', '--preserve-env=LIBGUESTFS_BACKEND',
                       'virt-sparsify', '--in-place', overlay]
                with open(self.log_file, 'a', encoding='utf8') as log_fd:
                    img_sub = self.shell.cmd_sub(cmd,
                                                 stdout=log_fd,
                                                 stderr=subprocess.STDOUT,
                                                 stdin=DEVNULL,
                                                 env=environment)
                    returncode = img_sub.wait()
                    self.log.info('Sparsify return code: %d', returncode)
                    if returncode != 0:
                        raise RuntimeError('Failed to convert volume!')

                _log_convert(overlay, 'qcow2', mapping)
            except (OSError, RuntimeError, subprocess.CalledProcessError):
                self.log.info('Sparsify failed, converting whole device...')
                self.shell.cmd_val(['sudo', 'rm', '-f', overlay])
                _log_convert(mapping['url'], 'raw', mapping)

    @use_lock(ATTACH_LOCK_FILE_DESTINATION)
    def _detach_destination_volumes(self):
        """ Disconnect new volumes from destination conversion host. """
        self.log.info('Detaching volumes from destination wrapper.')
        for path, mapping in self.volume_map.items():
            volume_id = mapping['dest_id']
            volume = self.conn.get_volume_by_id(volume_id)
            self.conn.detach_volume(server=self._converter(),
                                    timeout=self.timeout,
                                    volume=volume,
                                    wait=True)


def run_module():
    argument_spec = openstack_full_argument_spec(
        auth=dict(type='dict', no_log=True, required=True),
        data=dict(type='dict', required=True),
        conversion_host=dict(type='dict', required=True),
        ssh_key_path=dict(type='str', required=True),
        ssh_user=dict(type='str', required=True),
        transfer_uuid=dict(type='str', required=True),
        src_conversion_host_address=dict(type='str', required=True),
        volume_map=dict(type='dict', required=True),
        dst_conversion_host_address=dict(type='str', default=None),
        state_file=dict(type='str', default=None),
        log_file=dict(type='str', default=None),
        timeout=dict(type='int', default=DEFAULT_TIMEOUT),
    )

    result = dict(
        changed=False,
    )

    module = AnsibleModule(
        argument_spec=argument_spec,
    )

    sdk, conn = openstack_cloud_from_module(module)
    ser_server = server.Server.from_data(module.params['data'])
    params, info = ser_server.params_and_info()

    # Required parameters
    destination_conversion_host_id = module.params['conversion_host']['id']
    ssh_key_path = module.params['ssh_key_path']
    ssh_user = module.params['ssh_user']
    transfer_uuid = module.params['transfer_uuid']
    source_conversion_host_address = \
        module.params['src_conversion_host_address']
    volume_map = module.params['volume_map']

    # Optional parameters
    destination_conversion_host_address = \
        module.params.get('dst_conversion_host_address', None)
    state_file = module.params.get('state_file', None)
    log_file = module.params.get('log_file', None)
    timeout = module.params['timeout']

    destination_host = OpenStackDestinationHost(
        conn,
        destination_conversion_host_id,
        ssh_key_path,
        ssh_user,
        transfer_uuid,
        source_conversion_host_address,
        volume_map,
        ser_server,
        destination_conversion_host_address=destination_conversion_host_address,
        state_file=state_file,
        log_file=log_file,
        timeout=timeout,
    )
    destination_host.transfer_exports()

    block_device_mapping = []
    for path in sorted(destination_host.volume_map.keys()):
        name = path.split('/')[-1]
        uuid = destination_host.volume_map[path]['dest_id']

        if path == '/dev/vda':
            entry = {
                'boot_index': 0,
                'delete_on_termination': True,
                'destination_type': 'volume',
                'device_name': name,
                'source_type': 'volume',
                'uuid': uuid,
            }
        else:
            entry = {
                'boot_index': -1,
                'delete_on_termination': False,
                'destination_type': 'volume',
                'device_name': name,
                'source_type': 'volume',
                'uuid': uuid,
            }
        block_device_mapping.append(entry)

    result['volume_map'] = destination_host.volume_map
    result['block_device_mapping'] = block_device_mapping

    module.exit_json(**result)


def main():
    run_module()


if __name__ == '__main__':
    main()
