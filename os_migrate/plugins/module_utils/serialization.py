from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

from ansible_collections.os_migrate.os_migrate.plugins.module_utils import const


def new_resources_file_struct():
    """Create an empty resources file data structure into which resources
    can be added.
    """
    data = {}
    data['os_migrate_version'] = const.OS_MIGRATE_VERSION
    data['resources'] = []
    return data


def add_or_replace_resource(resources, resource):
    """Add a `resource` into `resources` struct, or replace it if already
    present (check via is_same_resource). Edits `resources` in place.

    Returns: True if something changed in resources structure, False
    otherwise
    """
    for i, r in enumerate(resources):
        if resource.is_same_resource(r):
            if r == resource.data:
                return False
            else:
                resources[i] = resource.data
                return True

    # If we didn't return by now, the resource wasn't found, so append it.
    resources.append(resource.data)
    return True


def create_resources_from_struct(struct_resources, cls_map):
    resources = []
    errors = []
    for struct_res in struct_resources:
        if not struct_res.get('type'):
            errors.append("Cannot parse resource due to missing 'type'.")
            continue
        if not cls_map.get(struct_res['type']):
            errors.append("Unknown resource type '{0}'.".format(struct_res['type']))
            continue
        resources.append(cls_map[struct_res['type']].from_data(struct_res))

    return resources, errors


# TODO: Remove when everything is a Resource
def resource_needs_update(current, target):
    """Having two serialized resources, `current` and `target`, check if
    the `current` resource is already in `target` state or if it needs
    an update. The method compares the resource representations,
    ignoring anything under `_info` dictionary keys, even in nested
    subresources.

    Returns: True if resource needs to be updated, False otherwise
    """
    current_trimmed = _trim_info(current)
    target_trimmed = _trim_info(target)
    return current_trimmed != target_trimmed


# TODO: Remove when everything is a Resource
def set_sdk_param(ser_params, ser_key, sdk_params, sdk_key):
    """Assign value from `ser_key` in `ser_params` dict as value for
    `sdk_key` in `sdk_params`, but only if it isn't None.
    """
    if ser_params.get(ser_key, None) is not None:
        sdk_params[sdk_key] = ser_params[ser_key]


# TODO: Remove when everything is a Resource
def set_sdk_params_same_name(ser_params, sdk_params, param_names):
    """Copy values from `ser_params` into `sdk_params` for all keys in
    `param_names` (list of strings), only for values in `ser_params`
    which aren't None.
    """
    for p_name in param_names:
        set_sdk_param(ser_params, p_name, sdk_params, p_name)


# TODO: Remove when everything is a Resource
def set_ser_params_same_name(ser_params, sdk_params, param_names):
    """Copy values from `sdk_params` to `ser_params` for keys listed in
    `param_names` (list of strings).
    """
    for p_name in param_names:
        ser_params[p_name] = sdk_params[p_name]


# TODO: Remove when everything is a Resource
def _trim_info(resource):
    """Returns: serialized `resource` with all the '_info' keys removed,
    even from nested resources. The original `resource` structure is
    untouched, but the returned structure does reuse data contents to
    save memory (it is not a deep copy).
    """
    def _recursive_trim(obj):
        if isinstance(obj, dict):
            result_dict = {}
            for k, v in obj.items():
                if k == const.RES_INFO:
                    continue
                result_dict[k] = _recursive_trim(v)
            return result_dict
        elif isinstance(obj, list):
            result_list = []
            for item in obj:
                result_list.append(_recursive_trim(item))
            return result_list
        else:
            return obj

    return _recursive_trim(resource)
