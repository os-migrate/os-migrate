from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

import unittest

from ansible_collections.os_migrate.os_migrate.tests.unit import fixtures
from ansible_collections.os_migrate.os_migrate.plugins.module_utils \
    import subnet


class TestSubnet(unittest.TestCase):

    def test_serialize_subnet(self):
        subnet_data = fixtures.sdk_subnet()
        serialized = subnet.Subnet.from_sdk(None, subnet_data)
        params, info = serialized.params_and_info()

        self.assertEqual(serialized.type(), 'openstack.subnet.Subnet')
        self.assertEqual(params['allocation_pools'],
                         [{'start': '10.10.10.2', 'end': '10.10.10.254'}])
        self.assertEqual(params['cidr'], '10.10.10.0/24')
        self.assertEqual(params['description'], 'test-subnet')
        self.assertEqual(params['dns_nameservers'], None)
        self.assertEqual(params['gateway_ip'], '10.10.10.1')
        self.assertEqual(params['host_routes'], None)
        self.assertEqual(params['ip_version'], 4)
        self.assertEqual(params['ipv6_address_mode'], None)
        self.assertEqual(params['ipv6_ra_mode'], None)
        self.assertEqual(params['is_dhcp_enabled'], True)
        self.assertEqual(params['name'], 'test-subnet1')
        self.assertEqual(params['service_types'], None)
        self.assertEqual(params['tags'], [])
        self.assertEqual(params['use_default_subnet_pool'], None)

        self.assertEqual(info['created_at'], '2020-02-21T17:34:54Z')
        self.assertEqual(info['id'], 'uuid-test-subnet1')
        self.assertEqual(info['network_id'], 'uuid-test-net')
        self.assertEqual(info['prefix_length'], None)
        self.assertEqual(info['project_id'], 'uuid-tenant')
        self.assertEqual(info['revision_number'], 0)
        self.assertEqual(info['segment_id'], None)
        self.assertEqual(info['subnet_pool_id'], None)
        self.assertEqual(info['updated_at'], None)
