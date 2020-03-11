from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

import unittest

from ansible_collections.os_migrate.os_migrate.tests.unit import fixtures
from ansible_collections.os_migrate.os_migrate.plugins.module_utils \
    import securitygrouprule


class TestSecurityGroupRule(unittest.TestCase):

    def test_serialize_security_group_rule(self):
        sec = fixtures.sdk_security_group_rule()
        serialized = securitygrouprule.SecurityGroupRule.from_sdk(None, sec)
        params, info = serialized.params_and_info()

        self.assertEqual(serialized.type(), 'openstack.network.SecurityGroupRule')
        self.assertEqual(params['security_group_name'], 'default')
        self.assertEqual(params['remote_group_name'], 'default')
        self.assertEqual(params['description'], 'null')
        self.assertEqual(params['direction'], 'ingress')
        self.assertEqual(params['port_range_max'], 100)
        self.assertEqual(params['port_range_min'], 10)
        self.assertEqual(params['protocol'], 'null')
        self.assertEqual(params['remote_ip_prefix'], 'null')
        self.assertEqual(params['tags'], [])

        self.assertEqual(info['created_at'], '2020-01-30T14:49:06Z')
        self.assertEqual(info['id'], 'uuid')
        self.assertEqual(info['project_id'], 'uuid-project')
        self.assertEqual(info['remote_group_id'], 'uuid-group')
        self.assertEqual(info['security_group_id'], 'uuid-sec-group')
        self.assertEqual(info['updated_at'], '2020-01-30T14:49:06Z')
        self.assertEqual(info['revision_number'], 0)
#
#    def test_security_group_rule_sdk_params(self):
#        ser_sec = fixtures.serialized_security_group_rule()
#        sec_refs = fixtures.security_group_rule_refs()
#        sdk_params = network.security_group_rule_sdk_params(ser_sec, sec_refs)
#
#        self.assertEqual(sdk_params['description'], 'null')
#        self.assertEqual(sdk_params['direction'], 'ingress')
#        self.assertEqual(sdk_params['port_range_max'], '100')
#        self.assertEqual(sdk_params['port_range_min'], '10')
#        self.assertEqual(sdk_params['protocol'], 'null')
#        self.assertEqual(sdk_params['remote_ip_prefix'], 'null')
