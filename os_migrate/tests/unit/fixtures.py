from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

import openstack

from ansible_collections.os_migrate.os_migrate.plugins.module_utils import const


def minimal_resource():
    return {
        'type': 'openstack.minimal',
        'params': {
            'name': 'minimal',
            'description': 'minimal resource',
        },
    }


def minimal_resource_file_struct():
    return {
        'os_migrate_version': const.Manifest().os_migrate_version(),
        'resources': [minimal_resource()],
    }


def network():
    return openstack.network.v2.network.Network(
        availability_zone_hints=['nova', 'zone2'],
        availability_zones=['nova', 'zone3'],
        created_at='2020-01-06T15:50:55Z',
        description='test network',
        dns_domain='example.org',
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
