from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

import unittest

from ansible_collections.os_migrate.os_migrate.plugins.module_utils \
    import const
from ansible_collections.os_migrate.os_migrate.plugins.module_utils \
    import resource
from ansible_collections.os_migrate.os_migrate.plugins.module_utils \
    import serialization
from ansible_collections.os_migrate.os_migrate.tests.unit import fixtures


class MinimalResource(resource.Resource):

    resource_type = 'openstack.Minimal'
    sdk_class = dict

    info_from_sdk = ['id']
    params_from_sdk = ['name', 'description']


class TestSerialization(unittest.TestCase):

    def test_new_resources_file_struct(self):
        file_struct = serialization.new_resources_file_struct()
        self.assertEqual(file_struct['os_migrate_version'], const.OS_MIGRATE_VERSION)
        self.assertEqual(file_struct['resources'], [])

    def test_add_or_replace_resource(self):
        resources = [
            {
                'type': 'openstack.Minimal',
                'params': {'name': 'one', 'description': 'one'},
                '_info': {'id': 'id-one'},
                '_migration_params': {}
            },
            {
                'type': 'openstack.Minimal',
                'params': {'name': 'two', 'description': 'two'},
                '_info': {'id': 'id-two'},
                '_migration_params': {}
            },
        ]

        add_resource = MinimalResource.from_data({
            'type': 'openstack.Minimal',
            'params': {'name': 'three', 'description': 'three'},
            '_info': {'id': 'id-three'},
        })

        # append at the end
        self.assertTrue(serialization.add_or_replace_resource(resources,
                                                              add_resource))
        self.assertEqual(resources, [
            {
                'type': 'openstack.Minimal',
                'params': {'name': 'one', 'description': 'one'},
                '_info': {'id': 'id-one'},
                '_migration_params': {}
            },
            {
                'type': 'openstack.Minimal',
                'params': {'name': 'two', 'description': 'two'},
                '_info': {'id': 'id-two'},
                '_migration_params': {}
            },
            {
                'type': 'openstack.Minimal',
                'params': {'name': 'three', 'description': 'three'},
                '_info': {'id': 'id-three'},
                '_migration_params': {}
            },
        ])

        replace_resource = MinimalResource.from_data({
            'type': 'openstack.Minimal',
            'params': {'name': 'two', 'description': 'two updated'},
            '_info': {'id': 'id-two'},
            '_migration_params': {}
        })

        # replace existing
        self.assertTrue(serialization.add_or_replace_resource(
            resources, replace_resource))
        self.assertEqual(resources, [
            {
                'type': 'openstack.Minimal',
                'params': {'name': 'one', 'description': 'one'},
                '_info': {'id': 'id-one'},
                '_migration_params': {}
            },
            {
                'type': 'openstack.Minimal',
                'params': {'name': 'two', 'description': 'two updated'},
                '_info': {'id': 'id-two'},
                '_migration_params': {}
            },
            {
                'type': 'openstack.Minimal',
                'params': {'name': 'three', 'description': 'three'},
                '_info': {'id': 'id-three'},
                '_migration_params': {}
            },
        ])

        # same replacement again - should return False, nothing changed
        self.assertFalse(serialization.add_or_replace_resource(
            resources, replace_resource))
        self.assertEqual(resources, [
            {
                'type': 'openstack.Minimal',
                'params': {'name': 'one', 'description': 'one'},
                '_info': {'id': 'id-one'},
                '_migration_params': {}
            },
            {
                'type': 'openstack.Minimal',
                'params': {'name': 'two', 'description': 'two updated'},
                '_info': {'id': 'id-two'},
                '_migration_params': {}
            },
            {
                'type': 'openstack.Minimal',
                'params': {'name': 'three', 'description': 'three'},
                '_info': {'id': 'id-three'},
                '_migration_params': {}
            },
        ])

    def test_create_resources_from_struct(self):
        cls_map = {'openstack.Minimal': MinimalResource}
        file_struct = fixtures.minimal_resource_file_struct()
        resources, errors = serialization.create_resources_from_struct(
            file_struct['resources'], cls_map)
        self.assertEqual(errors, [])
        self.assertTrue(isinstance(resources[0], MinimalResource))

        file_struct = fixtures.minimal_resource_file_struct()
        del file_struct['resources'][0]['type']
        resources, errors = serialization.create_resources_from_struct(
            file_struct['resources'], cls_map)
        self.assertEqual(errors, ["Cannot parse resource due to missing 'type'."])
        self.assertEqual(resources, [])

        file_struct = fixtures.minimal_resource_file_struct()
        file_struct['resources'][0]['type'] = 'asdf'
        resources, errors = serialization.create_resources_from_struct(
            file_struct['resources'], cls_map)
        self.assertEqual(errors, ["Unknown resource type 'asdf'."])
        self.assertEqual(resources, [])

    def test_resource_needs_update_minimal(self):
        current = fixtures.minimal_resource()
        target = fixtures.minimal_resource()

        self.assertFalse(serialization.resource_needs_update(current, target))

        target[const.RES_INFO]['detail'] = 'updated detail'
        self.assertFalse(serialization.resource_needs_update(current, target))

        target[const.RES_PARAMS]['description'] = 'updated description'
        self.assertTrue(serialization.resource_needs_update(current, target))

    def test_resource_needs_update_nested(self):
        current = fixtures.resource_with_nested()
        target = fixtures.resource_with_nested()

        self.assertFalse(serialization.resource_needs_update(current, target))

        target[const.RES_INFO]['detail'] = 'updated detail'
        self.assertFalse(serialization.resource_needs_update(current, target))

        target[const.RES_PARAMS]['description'] = 'updated description'
        self.assertTrue(serialization.resource_needs_update(current, target))

        # reset
        current = fixtures.resource_with_nested()
        target = fixtures.resource_with_nested()

        target[const.RES_PARAMS]['subresources'][0][const.RES_INFO]['nested-detail'] \
            = 'updated detail'
        self.assertFalse(serialization.resource_needs_update(current, target))

        target[const.RES_PARAMS]['subresources'][0][const.RES_PARAMS]['name'] \
            = 'updated-name'
        self.assertTrue(serialization.resource_needs_update(current, target))

        # reset
        current = fixtures.resource_with_nested()
        target = fixtures.resource_with_nested()

        target[const.RES_PARAMS]['subresources'][0][const.RES_TYPE] \
            = 'openstack.UpdatedType'
        self.assertTrue(serialization.resource_needs_update(current, target))

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

    def test_set_ser_params_same_name(self):
        ser_params = {'g': 'h'}
        sdk_params = {'a': 'b', 'c': 'd', 'e': 'f'}
        serialization.set_ser_params_same_name(
            ser_params, sdk_params, ['a', 'e'])
        self.assertEqual(ser_params, {'a': 'b', 'g': 'h', 'e': 'f'})

        with self.assertRaises(KeyError):
            serialization.set_ser_params_same_name(
                ser_params, sdk_params, ['a', 'e', 'z'])

    def test_trim_info(self):
        resource = fixtures.resource_with_nested()
        trimmed = serialization._trim_info(resource)
        self.assertEqual(trimmed, {
            const.RES_TYPE: 'openstack.WithNested',
            const.RES_PARAMS: {
                'name': 'with-nested',
                'description': 'resource with nested resources',
                'subresources': [
                    {
                        const.RES_TYPE: 'openstack.Nested',
                        const.RES_PARAMS: {
                            'name': 'nested-1',
                        },
                    },
                    {
                        const.RES_TYPE: 'openstack.Nested',
                        const.RES_PARAMS: {
                            'name': 'nested-2',
                        },
                    },
                ],
            },
        })
