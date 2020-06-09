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
module: import_workload_export_volumes

short_description: Create NBD exports of OpenStack volumes

extends_documentation_fragment: openstack

version_added: "2.9"

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
  source_conversion_host_address:
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
      ssh_key_path: "{{ os_migrate_conversion_host_key }}"
    register: volume_map
    when: prelim.changed

  rescue:
    - fail:
        msg: "Failed to import {{ item.params.name }}!"
'''

RETURN = '''
volume_map:
  description:
    - Mapping of source volume devices to NBD export URLs.
    - This structure only has source-related fields filled out.
  returned: Only after successfully moving volumes on source cloud.
  type: dict
  sample:
    "volume_map": {
          "/dev/vda": {
              "dest_dev": null,
              "dest_id": null,
              "image_id": null,
              "name": "migration-vm-boot",
              "port": 49164,
              "progress": 0.0,
              "size": 10,
              "snap_id": "52aa3444-6d22-4348-8cc7-5146a1fb9762",
              "source_dev": "/dev/vdb",
              "source_id": "ac62dcda-181d-4491-aa40-de60aa5918f3",
              "url": "nbd://localhost:49164/f544092c-6bb8-4e3e-b509-d59b1520540d"
          }
     }
'''

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.openstack \
    import openstack_full_argument_spec, openstack_cloud_from_module

from ansible_collections.os_migrate.os_migrate.plugins.module_utils import server

from ansible_collections.os_migrate.os_migrate.plugins.module_utils.workload_common \
    import RemoteShell, use_lock, ATTACH_LOCK_FILE_SOURCE, PORT_LOCK_FILE, PORT_MAP_FILE, DEFAULT_TIMEOUT

import json
import logging
import subprocess
import time
import uuid


class OpenStackSourceHost():
    """ Export volumes from an OpenStack instance over NBD. """

    def __init__(self, source_conversion_host, source_instance, ssh_key, conn,
                 source_address=None, source_disks=None, state_file=None,
                 log_file=None):
        """
        Required parameters:
        source_conversion_host: ID of source conversion host instance
        source_instance: ID of VM to migrate from the source
        ssh_key: Path to SSH key authorized on source conversion host
        conn: OpenStack connection handle
        """
        self.source_converter = source_conversion_host
        self.source_instance = source_instance
        self.ssh_key = ssh_key
        self.conn = conn

        """
        Optional parameters:
        source_address: Override accessIPv4 property for conversion host access
        source_disks: (TODO) List of disks to migrate, otherwise all of them
        state_file: File to hold current disk transfer state
        log_file: Debug log path for workload migration
        """
        self.source_address = source_address
        self.source_disks = source_disks
        self.state_file = state_file
        self.log_file = log_file

        # Configure logging
        self.log = logging.getLogger('osp-osp')
        log_format = logging.Formatter('%(asctime)s:%(levelname)s: ' +
                                       '%(message)s (%(module)s:%(lineno)d)')
        if log_file:
            log_handler = logging.FileHandler(log_file)
        else:
            log_handler = logging.NullHandler()
        log_handler.setFormatter(log_format)
        self.log.addHandler(log_handler)
        self.log.setLevel(logging.DEBUG)

        if self._converter() is None:
            raise RuntimeError('Cannot find source instance {0}'.format(
                               self.source_converter))

        self.shell = RemoteShell(self._converter_address(), ssh_key)
        self.shell.test_ssh_connection()

        # Build up a list of VolumeMappings keyed by the original device path
        # provided by the OpenStack API. Details:
        #   source_dev: Device path (like /dev/vdb) on source conversion host
        #   source_id:  Volume ID on source conversion host
        #   dest_dev:   Device path on destination conversion host
        #   dest_id:    Volume ID on destination conversion host
        #   snap_id:    Root volumes need snapshot+new volume
        #   image_id:   Direct-from-image VMs create temporary snapshot image
        #   name:       Save volume name to set on destination
        #   size:       Volume size reported by OpenStack, in GB
        #   port:       Port used to listen for NBD connections to this volume
        #   url:        Final NBD export address from source conversion host
        #   progress:   Transfer progress percentage
        self.volume_map = {}

        # If there is a specific list of disks to transfer, remember them so
        # only those disks get transferred. (TODO)
        self.source_disks = source_disks

        # Create marker for child processes on source conversion host.
        self.transfer_uuid = str(uuid.uuid4())

    def prepare_exports(self):
        """
        Attach the source VM's volumes to the source conversion host, and start
        waiting for NBD connections.
        """
        self._test_source_vm_shutdown()
        self._get_root_and_data_volumes()
        self._detach_data_volumes_from_source()
        self._attach_volumes_to_converter()
        self._export_volumes_from_converter()

    def _source_vm(self):
        """
        Changes to the VM returned by get_server_by_id are not necessarily
        reflected in existing objects, so just get a new one every time.
        """
        return self.conn.get_server_by_id(self.source_instance)

    def _converter(self):
        """ Same idea as _source_vm, for source conversion host. """
        return self.conn.get_server_by_id(self.source_converter)

    def _converter_address(self):
        """ Get IP address of source conversion host. """
        if self.source_address:
            return self.source_address
        else:
            return self._converter().accessIPv4

    def _test_source_vm_shutdown(self):
        """ Make sure the source VM is shutdown, and fail if it isn't. """
        server = self.conn.compute.get_server(self._source_vm().id)
        if server.status != 'SHUTOFF':
            raise RuntimeError('Source VM is not shut down!')

    def _get_attachment(self, volume, vm):
        """
        Get the attachment object from the volume with the matching server ID.
        Convenience method for use only when the attachment is already certain.
        """
        for attachment in volume.attachments:
            if attachment.server_id == vm.id:
                return attachment
        raise RuntimeError('Volume is not attached to the specified instance!')

    def _update_progress(self, dev_path, progress):
        self.log.info('Transfer progress for %s: %s%%', dev_path, str(progress))
        if self.state_file is None:
            return
        self.volume_map[dev_path]['progress'] = progress
        with open(self.state_file, 'w') as state:
            all_progress = {}
            for path, mapping in self.volume_map.items():
                all_progress[path] = mapping['progress']
            json.dump(all_progress, state)

    def _get_root_and_data_volumes(self):
        """
        Volume mapping step one: get the IDs and sizes of all volumes on the
        source VM. Key off the original device path to eventually preserve this
        order on the destination.
        """
        sourcevm = self._source_vm()
        for server_volume in sourcevm.volumes:
            volume = self.conn.get_volume_by_id(server_volume['id'])
            self.log.info('Inspecting volume: %s', volume.id)
            if self.source_disks and volume.id not in self.source_disks:
                self.log.info('Volume is not in specified disk list, ignoring.')
                continue
            dev_path = self._get_attachment(volume, sourcevm).device
            self.volume_map[dev_path] = dict(
                source_dev=None, source_id=volume.id, dest_dev=None,
                dest_id=None, snap_id=None, image_id=None, name=volume.name,
                size=volume.size, port=None, url=None, progress=None)
            self._update_progress(dev_path, 0.0)

    def _detach_data_volumes_from_source(self):
        """
        Detach data volumes from source VM, and pretend to "detach" the boot
        volume by creating a new volume from a snapshot of the VM. If the VM is
        booted directly from an image, take a VM snapshot and create the new
        volume from that snapshot.
        Volume map step two: replace boot disk ID with this new volume's ID,
        and record snapshot/image ID for later deletion.
        """
        sourcevm = self._source_vm()
        if '/dev/vda' in self.volume_map:
            mapping = self.volume_map['/dev/vda']
            volume_id = mapping['source_id']

            # Create a snapshot of the root volume
            self.log.info('Creating root device snapshot')
            root_snapshot = self.conn.create_volume_snapshot(
                force=True, wait=True, volume_id=volume_id,
                name='rhosp-migration-{0}'.format(volume_id),
                timeout=DEFAULT_TIMEOUT)

            # Create a new volume from the snapshot
            self.log.info('Creating new volume from root snapshot')
            root_volume_copy = self.conn.create_volume(
                wait=True, name='rhosp-migration-{0}'.format(volume_id),
                snapshot_id=root_snapshot.id, size=root_snapshot.size,
                timeout=DEFAULT_TIMEOUT)

            # Update the volume map with the new volume ID
            self.volume_map['/dev/vda']['source_id'] = root_volume_copy.id
            self.volume_map['/dev/vda']['snap_id'] = root_snapshot.id
        elif sourcevm.image:
            self.log.info('Image-based instance, creating snapshot...')
            image = self.conn.compute.create_server_image(
                name='rhosp-migration-root-{0}'.format(sourcevm.name),
                server=sourcevm.id)
            for second in range(DEFAULT_TIMEOUT):
                refreshed_image = self.conn.get_image_by_id(image.id)
                if refreshed_image.status == 'active':
                    break
                time.sleep(1)
            else:
                raise RuntimeError(
                    'Could not create new image of image-based instance!')
            volume = self.conn.create_volume(
                image=image.id, bootable=True, wait=True, name=image.name,
                timeout=DEFAULT_TIMEOUT, size=image.min_disk)
            self.volume_map['/dev/vda'] = dict(
                source_dev=None, source_id=volume.id, dest_dev=None,
                dest_id=None, snap_id=None, image_id=image.id, name=volume.name,
                size=volume.size, port=None, url=None, progress=None)
            self._update_progress('/dev/vda', 0.0)
        else:
            raise RuntimeError('No known boot device found for this instance!')

        for path, mapping in self.volume_map.items():
            if path != '/dev/vda':  # Detach non-root volumes
                volume_id = mapping['source_id']
                volume = self.conn.get_volume_by_id(volume_id)
                self.log.info('Detaching %s from %s', volume.id, sourcevm.id)
                self.conn.detach_volume(server=sourcevm, volume=volume,
                                        wait=True, timeout=DEFAULT_TIMEOUT)

    def _wait_for_volume_dev_path(self, conn, volume, vm, timeout):
        volume_id = volume.id
        for second in range(timeout):
            volume = conn.get_volume_by_id(volume_id)
            if volume.attachments:
                attachment = self._get_attachment(volume, vm)
                if attachment.device.startswith('/dev/'):
                    return
            time.sleep(1)
        raise RuntimeError('Timed out waiting for volume device path!')

    def _attach_volumes(self, conn, name, funcs):
        """
        Attach all volumes in the volume map to the specified conversion host.
        Check the list of disks before and after attaching to be absolutely
        sure the right source data gets copied to the right destination disk.
        This is here because _attach_destination_volumes and
        _attach_volumes_to_converter looked almost identical.
        """
        self.log.info('Attaching volumes to %s wrapper', name)
        host_func, ssh_func, update_func, volume_id_func = funcs
        for path, mapping in sorted(self.volume_map.items()):
            volume_id = volume_id_func(mapping)
            volume = conn.get_volume_by_id(volume_id)
            self.log.info('Attaching %s to %s conversion host', volume_id, name)

            disks_before = ssh_func(['lsblk', '--noheadings', '--list',
                                     '--paths', '--nodeps', '--output NAME'])
            disks_before = set(disks_before.split())
            self.log.debug('Initial disk list: %s', disks_before)

            conn.attach_volume(volume=volume, wait=True, server=host_func(),
                               timeout=DEFAULT_TIMEOUT)
            self.log.info('Waiting for volume to appear in %s wrapper', name)
            self._wait_for_volume_dev_path(conn, volume, host_func(),
                                           DEFAULT_TIMEOUT)

            disks_after = ssh_func(['lsblk', '--noheadings', '--list',
                                    '--paths', '--nodeps', '--output NAME'])
            disks_after = set(disks_after.split())
            self.log.debug('Updated disk list: %s', disks_after)

            new_disks = disks_after - disks_before
            volume = conn.get_volume_by_id(volume_id)
            attachment = self._get_attachment(volume, host_func())
            dev_path = attachment.device
            if len(new_disks) == 1:
                if dev_path in new_disks:
                    self.log.debug('Successfully attached new disk %s, and %s '
                                   'conversion host path matches OpenStack.',
                                   dev_path, name)
                else:
                    dev_path = new_disks.pop()
                    self.log.debug('Successfully attached new disk %s, but %s '
                                   'conversion host path does not match the  '
                                   'result from OpenStack. Using internal '
                                   'device path %s.', attachment.device,
                                   name, dev_path)
            else:
                raise RuntimeError('Got unexpected disk list after attaching '
                                   'volume to {0} conversion host instance. '
                                   'Failing migration procedure to avoid '
                                   'assigning volumes incorrectly. New '
                                   'disks(s) inside VM: {1}, disk provided by '
                                   'OpenStack: {2}'.format(name, new_disks,
                                                           dev_path))
            self.volume_map[path] = update_func(mapping, dev_path)

    # Lock this part to have a better chance of the OpenStack device path
    # matching the device path seen inside the conversion host.
    @use_lock(ATTACH_LOCK_FILE_SOURCE)
    def _attach_volumes_to_converter(self):
        """
        Attach all the source volumes to the conversion host. Volume mapping
        step 3: fill in the volume's device path on the source conversion host.
        """
        def update_source(volume_mapping, dev_path):
            volume_mapping['source_dev'] = dev_path
            return volume_mapping

        def volume_id(volume_mapping):
            return volume_mapping['source_id']

        self._attach_volumes(self.conn, 'source', (self._converter,
                                                   self.shell.cmd_out,
                                                   update_source, volume_id))

    def _test_port_available(self, port):
        """
        See if a port is open on the source conversion host by trying to listen
        on it.
        """
        result = self.shell.cmd_val(['timeout', '1', 'nc', '-l', str(port)])
        # The 'timeout' command returns 124 when the command times out, meaning
        # nc was successful and the port is free.
        return result == 124

    @use_lock(PORT_LOCK_FILE)
    def _find_free_port(self):
        # Reserve ports on the source conversion host. Lock a file containing
        # the used ports, select some ports from the range that is unused, and
        # check that the port is available on the source conversion host. Add
        # this to the locked file and unlock it for the next conversion.
        try:
            cmd = ['sudo', 'bash', '-c',
                   '"test -e {0} || echo [] > {0}"'.format(PORT_MAP_FILE)]
            result = self.shell.cmd_out(cmd)
            self.log.debug('Port write test: %s', result)
        except subprocess.CalledProcessError as err:
            raise RuntimeError('Unable to initialize port map file! ' + str(err))

        try:  # Try to read in the set of used ports
            cmd = ['sudo', 'cat', PORT_MAP_FILE]
            result = self.shell.cmd_out(cmd)
            used_ports = set(json.loads(result))
        except ValueError:
            self.log.info('Unable to read port map from %s, re-initializing '
                          'it...', PORT_MAP_FILE)
            used_ports = set()
        except subprocess.CalledProcessError as err:
            self.log.debug('Unable to get port map! %s', str(err))

        self.log.info('Currently used ports: %s', str(used_ports))

        # Choose ports from the available possibilities, and try to bind
        ephemeral_ports = set(range(49152, 65535))
        available_ports = ephemeral_ports - used_ports

        try:
            port = available_ports.pop()
            while not self._test_port_available(port):
                self.log.info('Port %d not available, trying another.', port)
                used_ports.add(port)  # Mark used to avoid trying again
                port = available_ports.pop()
        except KeyError:
            raise RuntimeError('No free ports on conversion host!')
        used_ports.add(port)
        self.log.info('Allocated port %d, all used: %s', port, used_ports)

        try:  # Write out port map to destination conversion host
            cmd = ['-T', 'sudo', 'bash', '-c', '"cat > ' + PORT_MAP_FILE + '"']
            input_json = json.dumps(list(used_ports))
            sub = self.shell.cmd_sub(cmd, stdin=subprocess.PIPE,
                                     stderr=subprocess.PIPE,
                                     stdout=subprocess.PIPE,
                                     universal_newlines=True)
            out, err = sub.communicate(input_json)
            if out:
                self.log.debug('Wrote port file, stdout: %s', out)
            if err:
                self.log.debug('Wrote port file, stderr: %s', err)
        except subprocess.CalledProcessError as err:
            self.log.debug('Unable to write port map to destination conversion '
                           'host! Error: %s', str(err))

        return port

    def _export_volumes_from_converter(self):
        """
        SSH to source conversion host and start an NBD export. Volume mapping
        step 4: fill in the URL to the volume's matching NBD export.
        """
        self.log.info('Exporting volumes from source conversion host...')
        for path, mapping in self.volume_map.items():
            port = self._find_free_port()
            volume_id = mapping['source_id']
            disk = mapping['source_dev']
            self.log.info('Exporting %s from volume %s', disk, volume_id)

            # TODO! Get nbdkit file plugin installed on conversion appliance!
            # cmd = ['nbdkit', '--exportname', self.transfer_uuid, '--ipaddr',
            #        '127.0.0.1', '--port', str(port), 'file', disk]
            # Fall back to qemu-nbd for now
            cmd = ['sudo', 'qemu-nbd', '-p', str(port), '-b', '127.0.0.1',
                   '--verbose', '--read-only', '--persistent', '-x',
                   self.transfer_uuid, disk]
            self.log.info('Exporting %s over NBD, port %s', disk, str(port))
            self.shell.cmd_sub(cmd, stdin=subprocess.PIPE,
                               stderr=subprocess.PIPE,
                               stdout=subprocess.PIPE)

            # Check qemu-img info on this disk to make sure it is ready
            self.log.info('Waiting for valid qemu-img info on all exports...')
            for second in range(DEFAULT_TIMEOUT):
                try:
                    cmd = ['qemu-img', 'info', 'nbd://localhost:' + str(port) +
                           '/' + self.transfer_uuid]
                    image_info = self.shell.cmd_out(cmd)
                    self.log.info('qemu-img info for %s: %s', disk, image_info)
                except subprocess.CalledProcessError as error:
                    self.log.info('Got exception: %s', error)
                    self.log.info('Trying again.')
                    time.sleep(1)
                else:
                    self.log.info('All volume exports ready.')
                    break
            else:
                raise RuntimeError('Timed out starting nbdkit exports!')

            self.volume_map[path]['port'] = port
            url = 'nbd://localhost:' + str(port) + '/' + self.transfer_uuid
            self.volume_map[path]['url'] = url
            self.log.info('Volume map so far: %s', self.volume_map)


def run_module():
    argument_spec = openstack_full_argument_spec(
        conversion_host=dict(type='dict', required=True),
        data=dict(type='dict', required=True),
        ssh_key_path=dict(type='str', required=True),
        source_conversion_host_address=dict(type='str', default=None),
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
    source_instance = info['id']
    source_conversion_host = module.params['conversion_host']['id']
    ssh_key = module.params['ssh_key_path']

    # Optional parameters
    source_address = module.params.get('source_conversion_host_address', None)
    state_file = module.params.get('state_file', None)
    log_file = module.params.get('log_file', None)

    source_host = OpenStackSourceHost(source_conversion_host, source_instance,
                                      ssh_key, conn, state_file=state_file,
                                      source_address=source_address,
                                      log_file=log_file)
    source_host.prepare_exports()
    result['volume_map'] = source_host.volume_map

    module.exit_json(**result)


def main():
    run_module()


if __name__ == '__main__':
    main()
