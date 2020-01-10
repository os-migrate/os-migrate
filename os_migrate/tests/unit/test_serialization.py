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
        serialization.add_or_replace_resource(resources, {
            'type': 'openstack.network',
            'params': {'name': 'three', 'description': 'three'},
        })
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
        serialization.add_or_replace_resource(resources, {
            'type': 'openstack.network',
            'params': {'name': 'two', 'description': 'two updated'},
        })
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
