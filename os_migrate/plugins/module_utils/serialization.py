from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

from ansible_collections.os_migrate.os_migrate.plugins.module_utils import const


def new_resources_file_struct():
    data = {}
    data['os_migrate_version'] = const.Manifest().os_migrate_version()
    data['resources'] = []
    return data


# Edits resources_file_struct in place.
def add_or_replace_resource(resources, resource):
    for i, r in enumerate(resources):
        if is_same_resource(r, resource):
            resources[i] = resource
            return

    # If we didn't return by now, the resource wasn't found, so append it.
    resources.append(resource)


def is_same_resource(res1, res2):
    if res1.get('type', '__undefined1__') != res2.get('type', '__undefined2__'):
        return False

    # We can add special cases if something else than ['type'] &&
    # ['params']['name'] should be the deciding factors for sameness,
    # but it's not necessary for now.
    return (res1.get('params', {}).get('name', '__undefined1__') ==
            res2.get('params', {}).get('name', '__undefined1__'))
