from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

import yaml
from os import path

from ansible_collections.os_migrate.os_migrate.plugins.module_utils import const
from ansible_collections.os_migrate.os_migrate.plugins.module_utils import serialization


def write_or_replace_resource(file_path, resource):
    if path.exists(file_path):
        file_struct = _load_resources_file(file_path)
    else:
        file_struct = serialization.new_resources_file_struct()

    resources = file_struct['resources']

    serialization.add_or_replace_resource(resources, resource)

    # TODO: Write the file only if contents changed.
    # Return True if contents changed, False otherwise
    _write_resources_file(file_path, file_struct)
    return True


def _load_resources_file(file_path):
    with open(file_path, 'r') as f:
        file_struct = yaml.load(f)
    return file_struct


def _write_resources_file(file_path, file_struct):
    with open(file_path, 'w') as f:
        f.write(yaml.dump(file_struct))
