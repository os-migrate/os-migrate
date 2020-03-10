from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

from copy import deepcopy
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
    # TODO: import
    # sdk_params_from_refs = [
    #     'external_gateway_info',
    #     'flavor_id',
    # ]

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
    def _find_sdk_res(conn, name_or_id):
        return conn.network.find_router(name_or_id)

    @staticmethod
    def _refs_from_sdk(conn, sdk_res):
        refs = {}
        refs['external_gateway_info'] = sdk_res['external_gateway_info']
        refs['flavor_id'] = sdk_res['flavor_id']

        def _external_gateway_nameinfo(conn, egi):
            egni = deepcopy(egi)
            del egni['network_id']
            del egni['external_fixed_ips']

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

    # TODO: import
    # def _refs_from_ser(self, conn):
    #     refs = {}
    #     return refs

    @staticmethod
    def _update_sdk_res(conn, name_or_id, sdk_params):
        return conn.network.update_router(name_or_id, **sdk_params)
