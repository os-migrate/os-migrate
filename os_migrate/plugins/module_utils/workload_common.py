from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

import subprocess
import time

# Default timeout for OpenStack operations
DEFAULT_TIMEOUT = 600

# Lock to serialize volume attachments. This helps prevent device path
# mismatches between the OpenStack SDK and /dev in the VM.
ATTACH_LOCK_FILE_SOURCE = '/var/lock/v2v-source-volume-lock'
ATTACH_LOCK_FILE_DESTINATION = '/var/lock/v2v-destination-volume-lock'

# File containing ports used by all the nbdkit processes running on the source
# conversion host. There is a check to see if the port is available, but this
# should speed things up.
PORT_MAP_FILE = '/var/run/v2v-wrapper-ports'
PORT_LOCK_FILE = '/var/lock/v2v-wrapper-lock'  # Lock for the port map


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


class RemoteShell():
    def __init__(self, address, key_path, username='cloud-user'):
        self.address = address
        self.key_path = key_path
        self.username = username

    def _default_options(self):
        return [
            '-i', self.key_path,
            '-o', 'BatchMode=yes',
            '-o', 'StrictHostKeyChecking=no',
            '-o', 'ConnectTimeout=10',
        ]

    def ssh_preamble(self):
        """ Common options to SSH into a conversion host. """
        preamble = ['ssh']
        preamble.extend(self._default_options())
        preamble.extend([self.username + '@' + self.address])
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
        remote_path = self.username + '@' + self.address + ':' + destination
        command.extend([source, remote_path])
        return subprocess.call(command)

    def scp_from(self, source, destination, recursive=False):
        """ Copy a file from the source conversion host. """
        command = ['scp']
        command.extend(self._default_options())
        if recursive:
            command.extend(['-r'])
        remote_path = self.username + '@' + self.address + ':' + source
        command.extend([remote_path, destination])
        return subprocess.call(command)

    def test_ssh_connection(self):
        """ Quick SSH connectivity check. """
        out = self.cmd_out(['echo connected'])
        if out != 'connected':
            raise RuntimeError(self.address + ': SSH test unsuccessful!')
