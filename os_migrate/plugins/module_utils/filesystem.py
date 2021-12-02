from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

import yaml
from os import path

from ansible_collections.os_migrate.os_migrate.plugins.module_utils import const
from ansible_collections.os_migrate.os_migrate.plugins.module_utils import exc
from ansible_collections.os_migrate.os_migrate.plugins.module_utils import serialization


def write_or_replace_resource(file_path, resource):
    """Add (or replace if already present) a `resource` into a resource
    file at `file_path`. If the resource is already present *and* its
    serialization is up to date, the file will not be modified.

    Returns: True if the file was modified, False otherwise
    """
    if path.exists(file_path):
        file_struct = load_resources_file(file_path)
    else:
        file_struct = serialization.new_resources_file_struct()

    resources = file_struct['resources']

    if serialization.add_or_replace_resource(resources, resource):
        _write_resources_file(file_path, file_struct)
        return True
    else:
        return False


def load_resources_file(file_path):
    """Load resources file at `file_path`.

    Returns: Structure (dict) of the loaded file.
    """
    with open(file_path, 'r', encoding='utf8') as f:
        file_struct = yaml.safe_load(f)

    file_os_migrate_version = file_struct.get('os_migrate_version', None)
    if file_os_migrate_version != const.OS_MIGRATE_VERSION:
        raise exc.DataVersionMismatch(file_path, file_os_migrate_version)

    return file_struct


def _write_resources_file(file_path, file_struct):
    """Write `file_struct` resources file structure into a file at
    `file_path`.
    """
    with open(file_path, 'w', encoding='utf8') as f:
        f.write(yaml.safe_dump(file_struct))
