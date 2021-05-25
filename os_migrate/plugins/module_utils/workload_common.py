# pylint: disable=consider-using-with
from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

import json
import logging
import os
import subprocess
import time

# Default timeout for OpenStack operations
DEFAULT_TIMEOUT = 1800

# Lock to serialize volume attachments. This helps prevent device path
# mismatches between the OpenStack SDK and /dev in the VM.
ATTACH_LOCK_FILE_SOURCE = '/var/lock/v2v-source-volume-lock'
ATTACH_LOCK_FILE_DESTINATION = '/var/lock/v2v-destination-volume-lock'

# File containing ports used by all the nbdkit processes running on the source
# conversion host. There is a check to see if the port is available, but this
# should speed things up.
PORT_MAP_FILE = '/var/run/v2v-migration-ports'
PORT_LOCK_FILE = '/var/lock/v2v-migration-lock'  # Lock for the port map

try:
    from subprocess import DEVNULL
except ImportError:
    DEVNULL = open(os.devnull, 'r+')


def use_lock(lock_file):
    """ Boilerplate for functions that need to take a lock. """
    def _decorate_lock(function):
        def wait_for_lock(self):
            for second in range(DEFAULT_TIMEOUT):
                try:
                    self.log.info('Waiting for lock %s...', lock_file)
                    lock = lock_file + '.lock'
                    cmd = ['sudo', 'flock', '--timeout', '1',
                           '--conflict-exit-code', '16', lock_file, '-c',
                           '"( test ! -e ' + lock + ' || exit 17 ) ' +
                           '&& touch ' + lock + '"']
                    result = self.shell.cmd_val(cmd)
                    if result == 16:
                        self.log.info('Another conversion has the lock.')
                    elif result == 17:
                        self.log.info('Another conversion is holding the lock.')
                    elif result == 0:
                        break
                except subprocess.CalledProcessError as err:
                    self.log.info('Error waiting for lock: %s', str(err))
                    time.sleep(1)
            else:
                raise RuntimeError('Unable to acquire lock ' + lock_file)
            try:
                return function(self)
            finally:
                try:
                    lock = lock_file + '.lock'
                    result = self.shell.cmd_out(['sudo', 'rm', '-f', lock])
                    self.log.debug('Released lock: %s', result)
                except subprocess.CalledProcessError as err:
                    self.log.error('Error releasing lock: %s', str(err))
        return wait_for_lock
    return _decorate_lock


class OpenStackHostBase():
    def __init__(self, openstack_connection, conversion_host_id, ssh_key_path,
                 ssh_user, transfer_uuid, conversion_host_address=None,
                 state_file=None, log_file=None, timeout=DEFAULT_TIMEOUT):
        # Required common parameters:
        # openstack_connection: OpenStack connection object
        # conversion_host_id: ID of conversion host instance
        # ssh_key_path: Path to SSH key authorized on conversion host
        # ssh_user: Username to create the SSH connection
        # transfer_uuid: UUID to mark processes on conversion hosts
        self.conn = openstack_connection
        self.conversion_host_id = conversion_host_id
        self.ssh_key_path = ssh_key_path
        self.ssh_user = ssh_user
        self.transfer_uuid = transfer_uuid

        # Optional parameters:
        # conversion_host_address: Optional address used to override 'accessIPv4'
        # state_file: File to hold current disk transfer state
        # log_file: Debug log path for workload migration
        self.conversion_host_address = conversion_host_address
        self.state_file = state_file
        self.log_file = log_file
        self.timeout = timeout

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
            raise RuntimeError('Cannot find instance {0}'.format(
                               self.conversion_host_id))

        self.shell = RemoteShell(self._converter_address(), ssh_user, ssh_key_path)
        self.shell.test_ssh_connection()

        # Ports chosen for NBD export
        self.claimed_ports = []

    def _converter(self):
        """ Refresh server object to pick up any changes. """
        return self.conn.get_server_by_id(self.conversion_host_id)

    def _converter_address(self):
        """ Get IP address of conversion host. """
        if self.conversion_host_address:
            return self.conversion_host_address
        else:
            return self._converter().accessIPv4

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
                               timeout=self.timeout)
            self.log.info('Waiting for volume to appear in %s wrapper', name)
            self._wait_for_volume_dev_path(conn, volume, host_func(),
                                           self.timeout)

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

    def _get_attachment(self, volume, vm):
        """
        Get the attachment object from the volume with the matching server ID.
        Convenience method for use only when the attachment is already certain.
        """
        for attachment in volume.attachments:
            if attachment.server_id == vm.id:
                return attachment
        raise RuntimeError('Volume is not attached to the specified instance!')

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

    def __read_used_ports(self):
        """
        Should only be called from functions locking the port list file, e.g.
        _find_free_port and _release_ports. Returns a set containing the ports
        currently used by all the migrations running on this conversion host.
        """
        try:
            cmd = ['sudo', 'bash', '-c',
                   '"test -e {0} || echo [] > {0}"'.format(PORT_MAP_FILE)]
            result = self.shell.cmd_out(cmd)
            if result:
                self.log.debug('Port write result: %s', result)
        except subprocess.CalledProcessError as err:
            raise RuntimeError('Unable to initialize port map file!') from err

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

        self.log.info('Currently used ports: %s', str(list(used_ports)))
        return used_ports

    def __write_used_ports(self, used_ports):
        """
        Should only be called from functions locking the port list file, e.g.
        _find_free_port and _release_ports. Writes out the given port list to
        the port list file on the current conversion host.
        """
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
            self.log.debug('Unable to write port map to conversion host! '
                           'Error was: %s', str(err))

    @use_lock(PORT_LOCK_FILE)
    def _find_free_port(self):
        """
        Reserve ports on the current conversion host. Lock a file containing
        the used ports, select some ports from the range that is unused, and
        check that the port is available on the conversion host. Add this to
        the locked file and unlock it for the next conversion.
        """
        used_ports = self.__read_used_ports()

        # Choose ports from the available possibilities, and try to bind
        ephemeral_ports = set(range(49152, 65535))
        available_ports = ephemeral_ports - used_ports

        try:
            port = available_ports.pop()
            while not self._test_port_available(port):
                self.log.info('Port %d not available, trying another.', port)
                used_ports.add(port)  # Mark used to avoid trying again
                port = available_ports.pop()
        except KeyError as err:
            raise RuntimeError('No free ports on conversion host!') from err
        used_ports.add(port)
        self.__write_used_ports(used_ports)
        self.log.info('Allocated port %d, all used: %s', port, used_ports)

        self.claimed_ports.append(port)
        return port

    @use_lock(PORT_LOCK_FILE)
    def _release_ports(self):
        used_ports = self.__read_used_ports()

        for port in self.claimed_ports:
            try:
                used_ports.remove(port)
            except KeyError:
                self.log.debug('Port already released? %d', port)

        self.log.info('Cleaning used ports: %s', used_ports)
        self.__write_used_ports(used_ports)

    def _test_port_available(self, port):
        """
        See if a port is open on the source conversion host by trying to listen
        on it.
        """
        result = self.shell.cmd_val(['timeout', '1', 'nc', '-l', str(port)])
        # The 'timeout' command returns 124 when the command times out, meaning
        # nc was successful and the port is free.
        return result == 124


class RemoteShell():
    def __init__(self, address, ssh_user, key_path=None):
        self.address = address
        self.ssh_user = ssh_user
        self.key_path = key_path

    def _default_options(self):
        options = [
            '-o', 'BatchMode=yes',
            '-o', 'StrictHostKeyChecking=no',
            '-o', 'ConnectTimeout=10',
        ]
        if self.key_path:
            options.extend(['-i', self.key_path])
        return options

    def ssh_preamble(self):
        """ Common options to SSH into a conversion host. """
        preamble = ['ssh']
        preamble.extend(self._default_options())
        preamble.extend([self.ssh_user + '@' + self.address])
        return preamble

    def cmd_out(self, command, **kwargs):
        """ Run command on the target conversion host and get the output. """
        args = self.ssh_preamble()
        args.extend(command)
        return subprocess.check_output(args, **kwargs).decode('utf-8').strip()

    def cmd_val(self, command, **kwargs):
        """ Run command on the target conversion host and get return code. """
        args = self.ssh_preamble()
        args.extend(command)
        return subprocess.call(args, **kwargs)

    def cmd_sub(self, command, **kwargs):
        """ Start a long-running command on the target conversion host. """
        args = self.ssh_preamble()
        args.extend(command)
        return subprocess.Popen(args, **kwargs)

    def scp_to(self, source, destination):
        """ Copy a file to the target conversion host. """
        command = ['scp']
        command.extend(self._default_options())
        remote_path = self.ssh_user + '@' + self.address + ':' + destination
        command.extend([source, remote_path])
        return subprocess.call(command)

    def scp_from(self, source, destination, recursive=False):
        """ Copy a file from the source conversion host. """
        command = ['scp']
        command.extend(self._default_options())
        if recursive:
            command.extend(['-r'])
        remote_path = self.ssh_user + '@' + self.address + ':' + source
        command.extend([remote_path, destination])
        return subprocess.call(command)

    def test_ssh_connection(self):
        """ Quick SSH connectivity check. """
        out = self.cmd_out(['echo connected'])
        if out != 'connected':
            raise RuntimeError(self.address + ': SSH test unsuccessful!')
