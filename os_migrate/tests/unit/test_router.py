from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

import openstack
import unittest

from ansible_collections.os_migrate.os_migrate.plugins.module_utils \
    import router


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


# "Disconnected" variant of Network resource where we make sure not to
# make requests using `conn`.
class Router(router.Router):

    def _refs_from_ser(self, conn):
        return router_refs()

    @staticmethod
    def _refs_from_sdk(conn, sdk_res):
        return router_refs()


class TestRouter(unittest.TestCase):

    def test_serialize_router(self):
        rtr = Router.from_sdk(None, sdk_router())  # conn=None
        params, info = rtr.params_and_info()

        self.assertEqual(rtr.type(), 'openstack.network.Router')
        self.assertEqual(params['availability_zone_hints'], ['nova', 'zone2'])
        self.assertEqual(params['description'], 'test router')
        self.assertEqual(params['is_admin_state_up'], True)
        self.assertEqual(params['is_distributed'], True)
        self.assertEqual(params['is_ha'], True)
        self.assertEqual(params['name'], 'test-router')
        self.assertEqual(params['external_gateway_nameinfo'], {
            'network_name': 'test-external-net',
            'external_fixed_ips': [
                {'subnet_name': 'test-external-subnet',
                 'ip_address': '172.24.4.79'},
                {'subnet_name': 'test-external-subnet-ipv6',
                 'ip_address': '2001:db8::1'}
            ],
            'enable_snat': True,
        })
        self.assertEqual(params['flavor_name'], 'test-network-flavor')

        self.assertEqual(info['availability_zones'], ['nova', 'zone3'])
        self.assertEqual(info['created_at'], '2020-02-26T15:50:55Z')
        self.assertEqual(info['external_gateway_info'], {
            'network_id': 'uuid-test-external-net',
            'external_fixed_ips': [
                {'subnet_id': 'uuid-test-external-subnet',
                 'ip_address': '172.24.4.79'},
                {'subnet_id': 'uuid-test-external-subnet-ipv6',
                 'ip_address': '2001:db8::1'}
            ],
            'enable_snat': True,
        })
        self.assertEqual(info['flavor_id'], 'uuid-test-network-flavor')
        self.assertEqual(info['project_id'], 'uuid-test-project')
        self.assertEqual(info['revision_number'], 3)
        self.assertEqual(info['routes'], [
            {'destination': '192.168.50.0/24', 'nexthop': '10.0.0.50'},
            {'destination': '192.168.50.0/24', 'nexthop': '10.0.0.51'},
        ])
        self.assertEqual(info['status'], 'ACTIVE')
        self.assertEqual(info['updated_at'], '2020-02-26T15:51:00Z')
