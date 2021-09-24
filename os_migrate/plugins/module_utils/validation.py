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

    errors.extend(_resource_duplicate_name_errors(all_resources))
    errors.extend(_resource_data_errors(all_resources))
    return errors


def _resource_data_errors(resources):
    errors = []
    for resource in resources:
        res_data_errors = resource.data_errors()
        if res_data_errors:
            errors.append(f"{resource.debug_id()}: {' '.join(res_data_errors)}")
    return errors


def _resource_duplicate_name_errors(resources):
    """Validate a `resources` list for duplicate naming.

    Returns: A list of validation error messages. Empty if all is ok.
    """
    import_id_counts = {}
    for resource in resources:
        import_id = resource.import_id()
        if import_id:
            count = import_id_counts.get(import_id, 0)
            import_id_counts[import_id] = count + 1

    errors = []
    for import_id, count in import_id_counts.items():
        if count > 1:
            errors.append(
                f"Resource duplication: {count} resources with import identity '{import_id}'. "
                "This would result in duplicit imports.")

    return errors
