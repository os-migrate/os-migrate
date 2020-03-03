from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

import unittest

from ansible_collections.os_migrate.os_migrate.tests.unit import fixtures
from ansible_collections.os_migrate.os_migrate.plugins.module_utils \
    import router


class TestRouter(unittest.TestCase):

    def test_serialize_router(self):
        rtr = fixtures.sdk_router()
        rtr_refs = fixtures.router_refs()
        serialized = router.serialize_router(rtr, rtr_refs)
        s_params = serialized['params']
        s_info = serialized['_info']

        self.assertEqual(serialized['type'], 'openstack.network.Router')
        self.assertEqual(s_params['availability_zone_hints'], ['nova', 'zone2'])
        self.assertEqual(s_params['availability_zones'], ['nova', 'zone3'])
        self.assertEqual(s_params['description'], 'test router')
        self.assertEqual(s_params['is_admin_state_up'], True)
        self.assertEqual(s_params['is_distributed'], True)
        self.assertEqual(s_params['is_ha'], True)
        self.assertEqual(s_params['name'], 'test-router')
        self.assertEqual(s_params['routes'], [
            {'destination': '192.168.50.0/24', 'nexthop': '10.0.0.50'},
            {'destination': '192.168.50.0/24', 'nexthop': '10.0.0.51'},
        ])
        self.assertEqual(s_params['external_gateway_nameinfo'], {
            'network_name': 'test-external-net',
            'external_fixed_ips': [
                {'subnet_name': 'test-external-subnet', 'ip_address': '172.24.4.79'},
                {'subnet_name': 'test-external-subnet-ipv6', 'ip_address': '2001:db8::1'}
            ],
            'enable_snat': True,
        })
        self.assertEqual(s_params['flavor_name'], 'test-network-flavor')

        self.assertEqual(s_info['created_at'], '2020-02-26T15:50:55Z')
        self.assertEqual(s_info['external_gateway_info'], {
            'network_id': 'uuid-test-external-net',
            'external_fixed_ips': [
                {'subnet_id': 'uuid-test-external-subnet', 'ip_address': '172.24.4.79'},
                {'subnet_id': 'uuid-test-external-subnet-ipv6', 'ip_address': '2001:db8::1'}
            ],
            'enable_snat': True,
        })
        self.assertEqual(s_info['flavor_id'], 'uuid-test-network-flavor')
        self.assertEqual(s_info['project_id'], 'uuid-test-project')
        self.assertEqual(s_info['revision_number'], 3)
        self.assertEqual(s_info['status'], 'ACTIVE')
        self.assertEqual(s_info['updated_at'], '2020-02-26T15:51:00Z')
