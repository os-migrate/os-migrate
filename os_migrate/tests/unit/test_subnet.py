from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

import unittest

from ansible_collections.os_migrate.os_migrate.tests.unit import fixtures
from ansible_collections.os_migrate.os_migrate.plugins.module_utils \
    import subnet


class TestSubnet(unittest.TestCase):

    def test_serialize_subnet(self):
        subnet_data = fixtures.sdk_subnet()
        serialized = subnet.serialize_subnet(subnet_data)
        s_params = serialized['params']
        s_info = serialized['_info']

        self.assertEqual(serialized['type'], 'openstack.subnet.Subnet')
        self.assertEqual(s_params['allocation_pools'],
                         [{'start': '10.10.10.2', 'end': '10.10.10.254'}])
        self.assertEqual(s_params['cidr'], '10.10.10.0/24')
        self.assertEqual(s_params['description'], 'test-subnet')
        self.assertEqual(s_params['dns_nameservers'], None)
        self.assertEqual(s_params['gateway_ip'], '10.10.10.1')
        self.assertEqual(s_params['host_routes'], None)
        self.assertEqual(s_params['ip_version'], 4)
        self.assertEqual(s_params['ipv6_address_mode'], None)
        self.assertEqual(s_params['ipv6_ra_mode'], None)
        self.assertEqual(s_params['is_dhcp_enabled'], True)
        self.assertEqual(s_params['name'], 'test-subnet1')
        self.assertEqual(s_params['service_types'], None)
        self.assertEqual(s_params['tags'], [])
        self.assertEqual(s_params['use_default_subnet_pool'], None)

        self.assertEqual(s_info['created_at'], '2020-02-21T17:34:54Z')
        self.assertEqual(s_info['id'], 'uuid-test-subnet1')
        self.assertEqual(s_info['network_id'], 'uuid-test-net')
        self.assertEqual(s_info['prefix_length'], None)
        self.assertEqual(s_info['project_id'], 'uuid-tenant')
        self.assertEqual(s_info['revision_number'], 0)
        self.assertEqual(s_info['segment_id'], None)
        self.assertEqual(s_info['subnet_pool_id'], None)
        self.assertEqual(s_info['updated_at'], None)
