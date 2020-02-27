from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

import openstack

from ansible_collections.os_migrate.os_migrate.plugins.module_utils.const \
    import ResourceType
from ansible_collections.os_migrate.os_migrate.plugins.module_utils.serialization \
    import Resource


class SubnetResource(Resource):
    expected_type = openstack.network.v2.subnet.Subnet
    serialized_type = ResourceType.SUBNET
    parameters = [
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
    information = [
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
