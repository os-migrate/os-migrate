from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

import unittest

from ansible_collections.os_migrate.os_migrate.tests.unit import fixtures
from ansible_collections.os_migrate.os_migrate.plugins.module_utils \
    import serialization


class TestSerialization(unittest.TestCase):

    def test_new_resources_file_struct(self):
        file_struct = serialization.new_resources_file_struct()
        self.assertEqual(file_struct['os_migrate_version'], '0.1.0')
        self.assertEqual(file_struct['resources'], [])

    def test_add_or_replace_resource(self):
        resources = [
            {
                'type': 'openstack.network',
                'params': {'name': 'one', 'description': 'one'},
            },
            {
                'type': 'openstack.network',
                'params': {'name': 'two', 'description': 'two'},
            },
        ]

        # append at the end
        self.assertTrue(serialization.add_or_replace_resource(resources, {
            'type': 'openstack.network',
            'params': {'name': 'three', 'description': 'three'},
        }))
        self.assertEqual(resources, [
            {
                'type': 'openstack.network',
                'params': {'name': 'one', 'description': 'one'},
            },
            {
                'type': 'openstack.network',
                'params': {'name': 'two', 'description': 'two'},
            },
            {
                'type': 'openstack.network',
                'params': {'name': 'three', 'description': 'three'},
            },
        ])

        # replace existing
        self.assertTrue(serialization.add_or_replace_resource(resources, {
            'type': 'openstack.network',
            'params': {'name': 'two', 'description': 'two updated'},
        }))
        self.assertEqual(resources, [
            {
                'type': 'openstack.network',
                'params': {'name': 'one', 'description': 'one'},
            },
            {
                'type': 'openstack.network',
                'params': {'name': 'two', 'description': 'two updated'},
            },
            {
                'type': 'openstack.network',
                'params': {'name': 'three', 'description': 'three'},
            },
        ])

        # same replacement again - should return False, nothing changed
        self.assertFalse(serialization.add_or_replace_resource(resources, {
            'type': 'openstack.network',
            'params': {'name': 'two', 'description': 'two updated'},
        }))
        self.assertEqual(resources, [
            {
                'type': 'openstack.network',
                'params': {'name': 'one', 'description': 'one'},
            },
            {
                'type': 'openstack.network',
                'params': {'name': 'two', 'description': 'two updated'},
            },
            {
                'type': 'openstack.network',
                'params': {'name': 'three', 'description': 'three'},
            },
        ])

    def test_set_sdk_param(self):
        ser_params = {'a': 'b', 'c': 'd', 'e': 'f'}
        sdk_params = {'g': 'h'}
        serialization.set_sdk_param(ser_params, 'a', sdk_params, 'a')
        self.assertEqual(sdk_params, {'a': 'b', 'g': 'h'})
        serialization.set_sdk_param(ser_params, 'z', sdk_params, 'z')
        self.assertEqual(sdk_params, {'a': 'b', 'g': 'h'})
        serialization.set_sdk_param(ser_params, 'c', sdk_params, 'e')
        self.assertEqual(sdk_params, {'a': 'b', 'g': 'h', 'e': 'd'})

    def test_set_sdk_params_same_name(self):
        ser_params = {'a': 'b', 'c': 'd', 'e': 'f'}
        sdk_params = {'g': 'h'}
        serialization.set_sdk_params_same_name(
            ser_params, sdk_params, ['a', 'e', 'z'])
        self.assertEqual(sdk_params, {'a': 'b', 'g': 'h', 'e': 'f'})
