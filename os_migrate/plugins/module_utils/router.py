from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

import openstack

from ansible_collections.os_migrate.os_migrate.plugins.module_utils \
    import const, reference, resource


class Router(resource.Resource):

    resource_type = const.RES_TYPE_ROUTER
    sdk_class = openstack.network.v2.router.Router

    info_from_sdk = [
        'availability_zones',
        'created_at',
        'external_gateway_info',
        'flavor_id',
        'id',
        'project_id',
        'revision_number',
        'routes',
        'status',
        'updated_at',
    ]
    params_from_sdk = [
        'availability_zone_hints',
        'description',
        'is_admin_state_up',
        'is_distributed',
        'is_ha',
        'name',
    ]
    params_from_refs = [
        'external_gateway_nameinfo',
        'flavor_name',
    ]
    sdk_params_from_refs = [
        'external_gateway_info',
        'flavor_id',
    ]

    @classmethod
    def from_sdk(cls, conn, sdk_resource):
        obj = super(Router, cls).from_sdk(conn, sdk_resource)
        obj._sort_param('availability_zone_hints')
        obj._sort_info('availability_zones')
        return obj

    @staticmethod
    def _create_sdk_res(conn, sdk_params):
        return conn.network.create_router(**sdk_params)

    @staticmethod
    def _find_sdk_res(conn, name_or_id, filters=None):
        return conn.network.find_router(name_or_id, **(filters or {}))

    @staticmethod
    def _refs_from_sdk(conn, sdk_res):
        refs = {}
        refs['external_gateway_info'] = sdk_res['external_gateway_info']
        refs['flavor_id'] = sdk_res['flavor_id']

        def _external_gateway_nameinfo(conn, egi):
            if egi is None:
                return None

            egni = {}
            egni['network_name'] = reference.network_name(conn, egi['network_id'])
            # We currently do not put external_fixed_ips into params:
            # * As a tenant we cannot fetch subnet_name for a subnet in a public
            #   net, so we do not request a particular public IP for the router
            #   when recreating it. It may be worth circling back if there is a way
            #   to try and preserve the IPs.
            return egni

        refs['external_gateway_nameinfo'] = _external_gateway_nameinfo(
            conn, sdk_res['external_gateway_info'])
        refs['flavor_name'] = reference.network_flavor_name(
            conn, sdk_res['flavor_id'])

        return refs

    def _refs_from_ser(self, conn, filters=None):
        refs = {}
        params = self.params()
        refs['external_gateway_nameinfo'] = params['external_gateway_nameinfo']
        refs['flavor_name'] = params['flavor_name']

        def _external_gateway_info(conn, egni):
            if egni is None:
                return None

            egi = {}
            egi['network_id'] = reference.network_id_simple(conn, egni['network_name'])
            return egi

        refs['external_gateway_info'] = _external_gateway_info(
            conn, params['external_gateway_nameinfo'])
        refs['flavor_id'] = reference.network_flavor_id(
            conn, params['flavor_name'], filters=filters)

        return refs

    @staticmethod
    def _update_sdk_res(conn, sdk_res, sdk_params):
        return conn.network.update_router(sdk_res, **sdk_params)
