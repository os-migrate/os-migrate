from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

import unittest

from ansible_collections.os_migrate.os_migrate.tests.unit import fixtures
from ansible_collections.os_migrate.os_migrate.plugins.module_utils \
    import securitygroup


class TestSecurityGroup(unittest.TestCase):

    def test_serialize_security_group(self):
        sec = fixtures.sdk_security_group()
        serialized = securitygroup.SecurityGroup.from_sdk(None, sec)
        params, info = serialized.params_and_info()

        self.assertEqual(serialized.type(), 'openstack.network.SecurityGroup')
        self.assertEqual(params['description'], 'Default security group')
        self.assertEqual(params['name'], 'default')
        self.assertEqual(params['tags'], [])

        self.assertEqual(info['created_at'], '2020-01-30T14:49:06Z')
        self.assertEqual(info['project_id'], 'uuid-project')
        self.assertEqual(info['updated_at'], '2020-01-30T14:49:06Z')
#
#    def test_security_group_sdk_params(self):
#        ser_sec = fixtures.serialized_security_group_rule
#        refs = ser_sec._refs_from_ser(None)  # conn=None
#        sdk_params = ser_sec._to_sdk_params(refs)
#
#        self.assertEqual(sdk_params['description'], 'Default security group')
#
#    def test_security_group_needs_update(self):
#        sdk_sec = fixtures.sdk_security_group()
#        serialized = securitygroup.serialize_security_group(sdk_sec)
#
#        self.assertFalse(network.security_group_needs_update(
#            sdk_sec, serialized))
#
#        serialized['_info']['id'] = 'different id'
#        self.assertFalse(network.security_group_needs_update(
#            sdk_sec, serialized))
#
#        serialized['params']['description'] = 'updated description'
#        self.assertTrue(network.security_group_needs_update(
#            sdk_sec, serialized))
