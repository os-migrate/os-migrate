from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

import openstack

from ansible_collections.os_migrate.os_migrate.plugins.module_utils \
    import const, resource


class Flavor(resource.Resource):
    resource_type = const.RES_TYPE_FLAVOR
    sdk_class = openstack.compute.v2.flavor.Flavor

    info_from_sdk = [
        'id',
    ]

    params_from_sdk = [
        'description',
        'disk',
        'ephemeral',
        'extra_specs',
        'is_disabled',
        'is_public',
        'links',
        'name',
        'ram',
        'rxtx_factor',
        'swap',
        'vcpus',
    ]

    @staticmethod
    def _create_sdk_res(conn, sdk_params):
        return conn.compute.create_flavor(**sdk_params)

    @staticmethod
    def _find_sdk_res(conn, name_or_id, filters=None):
        return conn.compute.find_flavor(name_or_id, **(filters or {}))

    @staticmethod
    def _update_sdk_res(conn, sdk_res, sdk_params):
        return
