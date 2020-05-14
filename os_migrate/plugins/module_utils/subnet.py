from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

import openstack

from ansible_collections.os_migrate.os_migrate.plugins.module_utils \
    import const, reference, resource


class Subnet(resource.Resource):
    resource_type = const.RES_TYPE_SUBNET
    sdk_class = openstack.network.v2.subnet.Subnet

    info_from_sdk = [
        'created_at',
        'id',
        'network_id',
        'prefix_length',
        'project_id',
        'revision_number',
        'segment_id',
        'subnet_pool_id',
        'tags',
        'updated_at',
    ]

    params_from_sdk = [
        'allocation_pools',
        'cidr',
        'description',
        'dns_nameservers',
        'gateway_ip',
        'host_routes',
        'ip_version',
        'ipv6_address_mode',
        'ipv6_ra_mode',
        'is_dhcp_enabled',
        'name',
        'service_types',
        'use_default_subnet_pool'
    ]

    params_from_refs = [
        'network_name',
        'segment_name',
        'subnet_pool_name'
    ]

    sdk_params_from_refs = [
        'network_id',
        'segment_id',
        'subnet_pool_id',
    ]

    readonly_sdk_params = ['network_id', 'project_id']

    @classmethod
    def from_sdk(cls, conn, sdk_resource):
        obj = super(Subnet, cls).from_sdk(conn, sdk_resource)
        obj._sort_param('allocation_pools')
        obj._sort_param('dns_nameservers')
        obj._sort_param('host_routes', by_keys=['destination', 'nexthop'])
        return obj

    @staticmethod
    def _create_sdk_res(conn, sdk_params):
        return conn.network.create_subnet(**sdk_params)

    @staticmethod
    def _find_sdk_res(conn, name_or_id, filters=None):
        return conn.network.find_subnet(name_or_id, **(filters or {}))

    @staticmethod
    def _update_sdk_res(conn, name_or_id, sdk_params):
        return conn.network.update_subnet(name_or_id, **sdk_params)

    @staticmethod
    def _refs_from_sdk(conn, sdk_res):
        refs = {}
        refs['network_id'] = sdk_res['network_id']
        refs['network_name'] = reference.network_name(
            conn, sdk_res['network_id'])
        refs['segment_id'] = sdk_res['segment_id']
        refs['segment_name'] = reference.segment_name(
            conn, sdk_res['segment_id'])
        refs['subnet_pool_id'] = sdk_res['subnet_pool_id']
        refs['subnet_pool_name'] = reference.subnet_pool_name(
            conn, sdk_res['subnet_pool_id'])
        return refs

    def _refs_from_ser(self, conn, filters=None):
        refs = {}
        refs['network_name'] = self.params()['network_name']
        refs['network_id'] = reference.network_id(
            conn, self.params()['network_name'], filters=filters)
        refs['segment_name'] = self.params()['segment_name']
        refs['segment_id'] = reference.segment_id(
            conn, self.params()['segment_name'], filters=filters)
        refs['subnet_pool_name'] = self.params()['subnet_pool_name']
        refs['subnet_pool_id'] = reference.subnet_pool_id(
            conn, self.params()['subnet_pool_name'], filters=filters)
        return refs
