from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

from ansible_collections.os_migrate.os_migrate.plugins.module_utils.resource \
    import Resource
from ansible_collections.os_migrate.os_migrate.plugins.module_utils import const


def new_resources_file_struct():
    """Create an empty resources file data structure into which resources
    can be added.
    """
    data = {}
    data['os_migrate_version'] = const.OS_MIGRATE_VERSION
    data['resources'] = []
    return data


def add_or_replace_resource(resources, resource_or_data):
    """Add a `resource` into `resources` struct, or replace it if already
    present (check via is_same_resource). Edits `resources` in place.

    Returns: True if something changed in resources structure, False
    otherwise
    """
    # TODO: remove this compatibility handler when everything is a
    # Resource, rename parameter from `resource_or_data` back to
    # `resource`
    if isinstance(resource_or_data, Resource):
        resource = resource_or_data.data
    else:
        resource = resource_or_data

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


# TODO: move sameness check into Resource when everything is a Resource
def is_same_resource(res1, res2):
    """Check whether two `res1` and `res2` dicts represent the same
    resource. Type and id are checked.

    Returns: True if same, False otherwise
    """
    # UUID should be enough of a check but just in case we get back to
    # checking by name in the future, let's keep the type check as
    # well, it doesn't hurt.
    if res1.get(const.RES_TYPE, '__undefined1__') != res2.get(
            const.RES_TYPE, '__undefined2__'):
        return False

    # We can add special cases if something else than ['type'] &&
    # ['_info']['id'] should be the deciding factors for sameness,
    # but it's not necessary for now.
    # special cases
    # projects
    if res1.get(const.RES_TYPE, '__undefined1__') == const.RES_TYPE_PROJECT:
        return (res1.get(const.RES_PARAMS, {}).get('name', '__undefined1__') ==
                res2.get(const.RES_PARAMS, {}).get('name', '__undefined2__'))

    return (res1.get(const.RES_INFO, {}).get('id', '__undefined1__') ==
            res2.get(const.RES_INFO, {}).get('id', '__undefined2__'))


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
