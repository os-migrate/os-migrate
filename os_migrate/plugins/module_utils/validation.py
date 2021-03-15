from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

from ansible_collections.os_migrate.os_migrate.plugins.module_utils import \
    resource_map, serialization


def get_errors_in_file_structs(file_structs, resrc_map=None):
    """Validate a list of `file_structs` resources file
    structures. Validates unique resource naming, in the future should
    also validate internal format of resources.

    Returns: A list of validation error messages. Empty if all is ok.
    """
    if resrc_map is None:
        resrc_map = resource_map.RESOURCE_MAP

    all_resource_structs = []
    for file_struct in file_structs:
        all_resource_structs.extend(file_struct['resources'])
    all_resources, errors = serialization.create_resources_from_struct(
        all_resource_structs, resrc_map)

    errors.extend(_resource_duplicate_name_errors(all_resource_structs))
    errors.extend(_resource_data_errors(all_resources))
    return errors


def _resource_data_errors(resources):
    errors = []
    for resource in resources:
        res_data_errors = resource.data_errors()
        if res_data_errors:
            errors.append("{0}: {1}".format(resource.debug_id(), ' '.join(res_data_errors)))
    return errors


def _resource_duplicate_name_errors(resources):
    """Validate a `resources` list for duplicate naming.

    Returns: A list of validation error messages. Empty if all is ok.
    """
    # Nested dict tracking count of resources per type per name.
    # E.g. { 'some.resource.Type': { 'some-resource-name': 2 } }
    type_name_counts = {}
    for resource in resources:
        r_type = resource.get('type', None)
        r_name = resource.get('params', {}).get('name', None)
        if r_type and r_name:
            type_subdict = type_name_counts.setdefault(r_type, {})
            count = type_subdict.get(r_name, 0)
            type_subdict[r_name] = count + 1

    errors = []

    for type_, type_subdict in type_name_counts.items():
        for name, count in type_subdict.items():
            if count > 1:
                errors.append(
                    "Resource duplication: {0} resources of type '{1}' and "
                    "name '{2}'.".format(count, type_, name))

    return errors
