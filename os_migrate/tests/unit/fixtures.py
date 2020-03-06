from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

import openstack

from ansible_collections.os_migrate.os_migrate.plugins.module_utils \
    import const


def minimal_resource():
    return {
        const.RES_TYPE: 'openstack.Minimal',
        const.RES_PARAMS: {
            'name': 'minimal',
            'description': 'minimal resource',
        },
        const.RES_INFO: {
            'id': 'id-minimal',
            'detail': 'not important for import and idempotence',
        },
    }


def minimal_resource_file_struct():
    return {
        'os_migrate_version': const.OS_MIGRATE_VERSION,
        'resources': [minimal_resource()],
    }


def resource_with_nested():
    return {
        const.RES_TYPE: 'openstack.WithNested',
        const.RES_PARAMS: {
            'name': 'with-nested',
            'description': 'resource with nested resources',
            'subresources': [
                {
                    const.RES_TYPE: 'openstack.Nested',
                    const.RES_PARAMS: {
                        'name': 'nested-1',
                    },
                    const.RES_INFO: {
                        'id': 'id-nested-1',
                        'nested-detail': 'not important',
                    },
                },
                {
                    const.RES_TYPE: 'openstack.Nested',
                    const.RES_PARAMS: {
                        'name': 'nested-2',
                    },
                    const.RES_INFO: {
                        'id': 'id-nested-2',
                        'nested-detail': 'also not important',
                    },
                },
            ],
        },
        const.RES_INFO: {
            'id': 'id-with-nested',
            'detail': 'not important for import and idempotence',
        },
    }


def sdk_router():
    return openstack.network.v2.router.Router(
        availability_zone_hints=['nova', 'zone2'],
        availability_zones=['nova', 'zone3'],
        created_at='2020-02-26T15:50:55Z',
        description='test router',
        external_gateway_info={
            'network_id': 'uuid-test-external-net',
            'external_fixed_ips': [
                {'subnet_id': 'uuid-test-external-subnet',
                 'ip_address': '172.24.4.79'},
                {'subnet_id': 'uuid-test-external-subnet-ipv6',
                 'ip_address': '2001:db8::1'},
            ],
            'enable_snat': True,
        },
        flavor_id='uuid-test-network-flavor',
        id='uuid-test-net',
        is_admin_state_up=True,
        is_distributed=True,
        is_ha=True,
        name='test-router',
        project_id='uuid-test-project',
        revision_number=3,
        routes=[
            {'destination': '192.168.50.0/24',
             'nexthop': '10.0.0.50'},
            {'destination': '192.168.50.0/24',
             'nexthop': '10.0.0.51'},
        ],
        status='ACTIVE',
        updated_at='2020-02-26T15:51:00Z',
    )


def router_refs():
    return {
        'external_gateway_nameinfo': {
            'network_name': 'test-external-net',
            'external_fixed_ips': [
                {'subnet_name': 'test-external-subnet',
                 'ip_address': '172.24.4.79'},
                {'subnet_name': 'test-external-subnet-ipv6',
                 'ip_address': '2001:db8::1'}
            ],
            'enable_snat': True,
        },
        'external_gateway_info': {
            'network_id': 'uuid-test-external-net',
            'external_fixed_ips': [
                {'subnet_id': 'uuid-test-external-subnet',
                 'ip_address': '172.24.4.79'},
                {'subnet_id': 'uuid-test-external-subnet-ipv6',
                 'ip_address': '2001:db8::1'}
            ],
            'enable_snat': True,
        },
        'flavor_name': 'test-network-flavor',
        'flavor_id': 'uuid-test-network-flavor',
    }


def security_group_rule_refs():
    return {
        'security_group_name': 'default',
        'remote_group_name': 'default',
    }


def sdk_security_group():
    return openstack.network.v2.security_group.SecurityGroup(
        description='Default security group',
        name='default',
        id='uuid',
        project_id='uuid-project',
        created_at='2020-01-30T14:49:06Z',
        updated_at='2020-01-30T14:49:06Z',
        tenant_id='uuid-tenant',
        revision_number='1',
    )


def serialized_security_group():
    return {
        const.RES_PARAMS: {
            'description': 'Default security group',
            'name': 'default',
        },
        const.RES_INFO: {
            'id': 'uuid',
            'project_id': 'uuid-project',
            'created_at': '2020-01-30T14:49:06Z',
            'updated_at': '2020-01-30T14:49:06Z',
            'tenant_id': 'uuid-tenant',
            'revision_number': '0',
        },
        const.RES_TYPE: 'openstack.network.SecurityGroup',
    }


def sdk_security_group_rule():
    return openstack.network.v2.security_group_rule.SecurityGroupRule(
        id='uuid',
        security_group_id='uuid-sec-group',
        security_group_name='default',
        remote_group_id='uuid-group',
        remote_group_name='default',
        project_id='uuid-project',
        created_at='2020-01-30T14:49:06Z',
        updated_at='2020-01-30T14:49:06Z',
        revision_number='0',
        description='null',
        direction='ingress',
        port_range_max='100',
        port_range_min='10',
        protocol='null',
        remote_ip_prefix='null',
    )


def serialized_security_group_rule():
    return {
        const.RES_PARAMS: {
            'description': 'null',
            'direction': 'ingress',
            'port_range_max': '100',
            'port_range_min': '10',
            'protocol': 'null',
            'remote_ip_prefix': 'null',
        },
        const.RES_INFO: {
            'id': 'uuid',
            'security_group_id': 'uuid-sec-group',
            'remote_group_id': 'uuid-group',
            'project_id': 'uuid-project',
            'created_at': '2020-01-30T14:49:06Z',
            'updated_at': '2020-01-30T14:49:06Z',
            'revision_number': '0',
        },
        const.RES_TYPE: 'openstack.network.SecurityGroupRule',
    }


def sdk_subnet():
    return openstack.network.v2.subnet.Subnet(
        id='uuid-test-subnet1',
        name='test-subnet1',
        tenant_id='uuid-tenant',
        network_id='uuid-test-net',
        ip_version=4,
        enable_dhcp=True,
        gateway_ip='10.10.10.1',
        cidr='10.10.10.0/24',
        allocation_pools=[{
            'start': '10.10.10.2',
            'end': '10.10.10.254'
        }],
        description='test-subnet',
        created_at='2020-02-21T17:34:54Z',
        revision_number=0
    )


def serialized_subnet():
    return {
        const.RES_PARAMS: {
            'allocation_pools': [
                {'start': '10.10.10.2', 'end': '10.10.10.254'}],
            'cidr': '10.10.10.0/24',
            'description': 'test-subnet',
            'dns_nameservers': None,
            'gateway_ip': '10.10.10.1',
            'host_routes': None,
            'ip_version': 4,
            'ipv6_address_mode': None,
            'ipv6_ra_mode': None,
            'is_dhcp_enabled': True,
            'name': 'test-subnet1',
            'service_types': None,
            'tags': [],
            'use_default_subnet_pool': None,
        },
        const.RES_INFO: {
            'created_at': '2020-02-21T17:34:54Z',
            'id': 'uuid-test-subnet1',
            'network_id': 'uuid-test-net',
            'prefix_length': None,
            'project_id': 'uuid-tenant',
            'revision_number': 0,
            'segment_id': None,
            'subnet_pool_id': None,
            'updated_at': None,
        },
        const.RES_TYPE: 'openstack.network.Subnet',
    }
