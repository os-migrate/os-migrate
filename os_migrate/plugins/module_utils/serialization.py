from __future__ import (absolute_import, division, print_function)

__metaclass__ = type

from ansible_collections.os_migrate.os_migrate.plugins.module_utils import const
from ansible_collections.os_migrate.os_migrate.plugins.module_utils.const \
    import ResourceType, Sections
from ansible_collections.os_migrate.os_migrate.plugins.module_utils import exc


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
    return (res1.get(const.RES_INFO, {}).get('id', '__undefined1__') ==
            res2.get(const.RES_INFO, {}).get('id', '__undefined2__'))


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


def set_sdk_param(ser_params, ser_key, sdk_params, sdk_key):
    """Assign value from `ser_key` in `ser_params` dict as value for
    `sdk_key` in `sdk_params`, but only if it isn't None.
    """
    if ser_params.get(ser_key, None) is not None:
        sdk_params[sdk_key] = ser_params[ser_key]


def set_sdk_params_same_name(ser_params, sdk_params, param_names):
    """Copy values from `ser_params` into `sdk_params` for all keys in
    `param_names` (list of strings), only for values in `ser_params`
    which aren't None.
    """
    for p_name in param_names:
        set_sdk_param(ser_params, p_name, sdk_params, p_name)


def set_ser_params_same_name(ser_params, sdk_params, param_names):
    """Copy values from `sdk_params` to `ser_params` for keys listed in
    `param_names` (list of strings).
    """
    for p_name in param_names:
        ser_params[p_name] = sdk_params[p_name]


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


class Resource:
    expected_type = None
    content = None
    serialized_type = None
    parameters = []
    sorted_parameters = []
    information = []
    sorted_information = []
    # supporting one external source for now.
    # could expand this in the future if needed
    external_content = None
    external_parameters = []
    external_sorted_parameters = []
    external_information = []
    external_sorted_information = []

    def __init__(self, **kwargs):
        # Go through keyword arguments, and either save their values to our
        # instance, or raise an error.
        for key, value in kwargs.items():
            setattr(self, key, value)

        expected_type = self.expected_type
        if type(self.content) != expected_type:
            raise exc.UnexpectedResourceType(expected_type, type(self.content))

    def serialize(self):
        """Serialize OpenStack SDK resource `content` into OS-Migrate
            format. Use `net_refs` for id-to-name mappings.

            Returns: Dict - OS-Migrate structure for Network
            """
        resource = {}
        params = {}
        info = {}
        resource[Sections.PARAMS.value] = params
        resource[Sections.INFO.value] = info
        resource[Sections.TYPE.value] = self.serialized_type.value

        for sorted_param in self.sorted_parameters:
            params[sorted_param] = sorted(self.content[sorted_param])
        set_ser_params_same_name(params, self.content, self.parameters)

        for sorted_info in self.sorted_information:
            info[sorted_info] = sorted(self.content[sorted_info])
        set_ser_params_same_name(info, self.content, self.information)

        if self.external_content is not None:
            set_ser_params_same_name(params, self.external_content,
                                     self.external_parameters)
            set_ser_params_same_name(info, self.external_content,
                                     self.external_information)
            for ext_sorted_param in self.external_sorted_parameters:
                params[ext_sorted_param] = sorted(
                    self.external_content[ext_sorted_param])
            for ext_sorted_info in self.external_sorted_information:
                info[ext_sorted_info] = sorted(
                    self.external_content[ext_sorted_info])

        return resource
