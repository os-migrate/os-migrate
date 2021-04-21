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
        # There doesn't seem to be an API for disabling a flavor.
        'is_disabled',
    ]

    params_from_sdk = [
        'description',
        'disk',
        'ephemeral',
        'extra_specs',
        'is_public',
        'name',
        'ram',
        'rxtx_factor',
        'swap',
        'vcpus',
    ]
    sdk_params_from_params = [x for x in params_from_sdk if x not in ['extra_specs']]

    def _data_from_sdk_and_refs(self, sdk_res, refs):
        super()._data_from_sdk_and_refs(sdk_res, refs)
        params = self.params()
        # APIs before microversion 2.75 return '' instead of 0, but
        # only 0 is accepted when creating a flavor.
        if params['swap'] == '':
            params['swap'] = 0

    def _hook_after_update(self, conn, sdk_res, is_create):
        params = self.params()
        delete_extra_specs = list(set(sdk_res['extra_specs'].keys()) -
                                  set(params['extra_specs'].keys()))
        for prop_name in delete_extra_specs:
            conn.compute.delete_flavor_extra_specs_property(sdk_res, prop_name)
        for prop_name in params['extra_specs'].keys():
            if sdk_res['extra_specs'].get(prop_name) != params['extra_specs'][prop_name]:
                conn.compute.update_flavor_extra_specs_property(
                    sdk_res, prop_name, params['extra_specs'][prop_name])

    @staticmethod
    def _create_sdk_res(conn, sdk_params):
        return conn.compute.create_flavor(**sdk_params)

    @staticmethod
    def _find_sdk_res(conn, name_or_id, filters=None):
        return conn.compute.find_flavor(name_or_id, **(filters or {}))

    @staticmethod
    def _update_sdk_res(conn, sdk_res, sdk_params):
        return sdk_res
