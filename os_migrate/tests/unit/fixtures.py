from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

import openstack

from ansible_collections.os_migrate.os_migrate.plugins.module_utils import const


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


def sdk_network():
    return openstack.network.v2.network.Network(
        availability_zone_hints=['nova', 'zone2'],
        availability_zones=['nova', 'zone3'],
        created_at='2020-01-06T15:50:55Z',
        description='test network',
        dns_domain='example.org',
        id='uuid-test-net',
        ipv4_address_scope_id=None,
        ipv6_address_scope_id=None,
        is_admin_state_up=True,
        is_default=False,
        is_port_security_enabled=True,
        is_router_external=False,
        is_shared=False,
        mtu=1400,
        name='test-net',
        project_id='uuid-test-project',
        provider_network_type='vxlan',
        provider_physical_network='physnet',
        provider_segmentation_id='456',
        qos_policy_id='uuid-test-qos-policy',
        revision_number=3,
        segments=[],
        status='ACTIVE',
        subnet_ids=['uuid-test-subnet1', 'uuid-test-subnet2'],
        updated_at='2020-01-06T15:51:00Z',
        is_vlan_transparent=False,
    )


def network_refs():
    return {
        'project_id': 'uuid-test-project',
        'project_name': 'test-project',
        'qos_policy_id': 'uuid-test-qos-policy',
        'qos_policy_name': 'test-qos-policy',
        'subnet_ids': ['uuid-test-subnet1', 'uuid-test-subnet2'],
        'subnet_names': ['test-subnet1', 'test-subnet2'],
    }


def serialized_network():
    return {
        const.RES_PARAMS: {
            'availability_zone_hints': ['nova', 'zone2'],
            'description': 'test network',
            'dns_domain': 'example.org',
            'is_admin_state_up': True,
            'is_default': False,
            'is_port_security_enabled': True,
            'is_router_external': False,
            'is_shared': False,
            'is_vlan_transparent': False,
            'mtu': 1400,
            'name': 'test-net',
            'project_name': 'test-project',
            'provider_network_type': 'vxlan',
            'provider_physical_network': 'physnet',
            'provider_segmentation_id': '456',
            'qos_policy_name': 'test-qos-policy',
            'segments': [],
        },
        const.RES_INFO: {
            'availability_zones': ['nova', 'zone3'],
            'created_at': '2020-01-06T15:50:55Z',
            'project_id': 'uuid-test-project',
            'revision_number': 3,
            'status': 'ACTIVE',
            'subnet_ids': ['uuid-test-subnet1', 'uuid-test-subnet2'],
            'qos_policy_id': 'uuid-test-qos-policy',
            'updated_at': '2020-01-06T15:51:00Z',
        },
        const.RES_TYPE: 'openstack.network.Network',
    }
