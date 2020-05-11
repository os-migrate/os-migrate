from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

import subprocess


def ssh_preamble(address, key_path):
    """ Common options to SSH into a conversion host. """
    return [
        'ssh',
        '-i', key_path,
        '-o', 'BatchMode=yes',
        '-o', 'StrictHostKeyChecking=no',
        '-o', 'ConnectTimeout=10',
        'cloud-user@' + address
    ]


def dst_ssh(address, key_path, command):
    """ Get text output from running one SSH command on a conversion host. """
    args = ssh_preamble(address, key_path)
    args.extend(command)
    return subprocess.check_output(args).decode('utf-8').strip()
