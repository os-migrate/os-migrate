from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

import unittest

from ansible_collections.os_migrate.os_migrate.tests.unit import fixtures
from ansible_collections.os_migrate.os_migrate.plugins.module_utils \
    import network


class TestNetwork(unittest.TestCase):

    def test_serialize_network(self):
        net = fixtures.sdk_network()
        serialized = network.serialize_network(net)
        s_params = serialized['params']
        s_info = serialized['info']

        self.assertEqual(serialized['type'], 'openstack.network')
        self.assertEqual(s_params['availability_zone_hints'], ['nova', 'zone2'])
        self.assertEqual(s_params['description'], 'test network')
        self.assertEqual(s_params['dns_domain'], 'example.org')
        self.assertEqual(s_params['is_admin_state_up'], True)
        self.assertEqual(s_params['is_default'], False)
        self.assertEqual(s_params['is_port_security_enabled'], True)
        self.assertEqual(s_params['is_router_external'], False)
        self.assertEqual(s_params['is_shared'], False)
        self.assertEqual(s_params['is_vlan_transparent'], False)
        self.assertEqual(s_params['mtu'], 1400)
        self.assertEqual(s_params['name'], 'test-net')
        self.assertEqual(s_params['provider_network_type'], 'vxlan')
        self.assertEqual(s_params['provider_physical_network'], 'physnet')
        self.assertEqual(s_params['provider_segmentation_id'], '456')
        self.assertEqual(s_params['qos_policy_id'], 'uuid-test-qos-policy')
        self.assertEqual(s_params['segments'], [])

        self.assertEqual(s_info['availability_zones'], ['nova', 'zone3'])
        self.assertEqual(s_info['created_at'], '2020-01-06T15:50:55Z')
        self.assertEqual(s_info['project_id'], 'uuid-test-project')
        self.assertEqual(s_info['revision_number'], 3)
        self.assertEqual(s_info['status'], 'ACTIVE')
        self.assertEqual(s_info['subnet_ids'], ['uuid-test-subnet1', 'uuid-test-subnet2'])
        self.assertEqual(s_info['updated_at'], '2020-01-06T15:51:00Z')

    def test_network_sdk_params(self):
        ser_net = fixtures.serialized_network()
        sdk_params = network.network_sdk_params(ser_net)

        self.assertEqual(sdk_params['availability_zone_hints'], ['nova', 'zone2'])
        self.assertEqual(sdk_params['description'], 'test network')
        self.assertEqual(sdk_params['dns_domain'], 'example.org')
        self.assertEqual(sdk_params['is_admin_state_up'], True)
        self.assertEqual(sdk_params['is_default'], False)
        self.assertEqual(sdk_params['is_port_security_enabled'], True)
        self.assertEqual(sdk_params['is_router_external'], False)
        self.assertEqual(sdk_params['is_shared'], False)
        self.assertEqual(sdk_params['is_vlan_transparent'], False)
        self.assertEqual(sdk_params['mtu'], 1400)
        self.assertEqual(sdk_params['name'], 'test-net')
        self.assertEqual(sdk_params['provider_network_type'], 'vxlan')
        self.assertEqual(sdk_params['provider_physical_network'], 'physnet')
        self.assertEqual(sdk_params['provider_segmentation_id'], '456')
        self.assertEqual(sdk_params['qos_policy_id'], 'uuid-test-qos-policy')
        self.assertEqual(sdk_params['segments'], [])
        # disallowed params when creating a network
        self.assertNotIn('availability_zones', sdk_params)
        self.assertNotIn('revision_number', sdk_params)
