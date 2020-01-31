from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

from ansible_collections.os_migrate.os_migrate.plugins.module_utils import const


def new_resources_file_struct():
    data = {}
    data['os_migrate_version'] = const.OS_MIGRATE_VERSION
    data['resources'] = []
    return data


# Edits resources_file_struct in place. Returns bool whether something changed.
def add_or_replace_resource(resources, resource):
    for i, r in enumerate(resources):
        if is_same_resource(r, resource):
            if r == resource:
                return False
            else:
                resources[i] = resource
                return True

    # If we didn't return by now, the resource wasn't found, so append it.
    resources.append(resource)
    return True


def is_same_resource(res1, res2):
    if res1.get('type', '__undefined1__') != res2.get('type', '__undefined2__'):
        return False

    # We can add special cases if something else than ['type'] &&
    # ['params']['name'] should be the deciding factors for sameness,
    # but it's not necessary for now.
    return (res1.get('params', {}).get('name', '__undefined1__') ==
            res2.get('params', {}).get('name', '__undefined1__'))


def set_sdk_param(ser_params, ser_key, sdk_params, sdk_key):
    if ser_params.get(ser_key, None) is not None:
        sdk_params[sdk_key] = ser_params[ser_key]


def set_sdk_params_same_name(ser_params, sdk_params, param_names):
    for p_name in param_names:
        set_sdk_param(ser_params, p_name, sdk_params, p_name)


def set_ser_params_same_name(ser_params, sdk_params, param_names):
    for p_name in param_names:
        ser_params[p_name] = sdk_params[p_name]
