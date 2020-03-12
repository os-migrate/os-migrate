from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

import openstack

from ansible_collections.os_migrate.os_migrate.plugins.module_utils \
    import const, resource


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
        'tags',
        'use_default_subnet_pool'
    ]

    @staticmethod
    def _create_sdk_res(conn, sdk_params):
        return conn.subnet.create_subnet(**sdk_params)

    @staticmethod
    def _find_sdk_res(conn, name_or_id):
        return conn.subnet.find_subnet(name_or_id)

    @staticmethod
    def _update_sdk_res(conn, name_or_id, sdk_params):
        return conn.subnet.update_subnet(name_or_id, **sdk_params)
