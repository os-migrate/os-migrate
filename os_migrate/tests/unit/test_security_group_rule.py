from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

import unittest

from ansible_collections.os_migrate.os_migrate.tests.unit import fixtures
from ansible_collections.os_migrate.os_migrate.plugins.module_utils \
    import network


class TestSecurityGroupRule(unittest.TestCase):

    def test_serialize_security_group_rule(self):
        sec = fixtures.sdk_security_group_rule()
        serialized = network.serialize_security_group_rule(sec)
        s_params = serialized['params']
        s_info = serialized['_info']

        self.assertEqual(serialized['type'], 'openstack.network.SecurityGroupRule')
        self.assertEqual(s_params['description'], 'null')
        self.assertEqual(s_params['direction'], 'ingress')
        self.assertEqual(s_params['port_range_max'], 100)
        self.assertEqual(s_params['port_range_min'], 10)
        self.assertEqual(s_params['protocol'], 'null')
        self.assertEqual(s_params['remote_ip_prefix'], 'null')
        self.assertEqual(s_params['tags'], [])

        self.assertEqual(s_info['created_at'], '2020-01-30T14:49:06Z')
        self.assertEqual(s_info['id'], 'uuid')
        self.assertEqual(s_info['project_id'], 'uuid-project')
        self.assertEqual(s_info['remote_group_id'], 'uuid-group')
        self.assertEqual(s_info['security_group_id'], 'uuid-sec-group')
        self.assertEqual(s_info['updated_at'], '2020-01-30T14:49:06Z')
        self.assertEqual(s_info['revision_number'], 0)

    def test_security_group_rule_sdk_params(self):
        ser_sec = fixtures.serialized_security_group_rule()
        sdk_params = network.security_group_rule_sdk_params(ser_sec)

        self.assertEqual(sdk_params['description'], 'null')
        self.assertEqual(sdk_params['direction'], 'ingress')
        self.assertEqual(sdk_params['port_range_max'], '100')
        self.assertEqual(sdk_params['port_range_min'], '10')
        self.assertEqual(sdk_params['protocol'], 'null')
        self.assertEqual(sdk_params['remote_ip_prefix'], 'null')
