from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

import yaml
from os import path
import unittest

from ansible_collections.os_migrate.os_migrate.plugins.module_utils import const
from ansible_collections.os_migrate.os_migrate.plugins.module_utils import exc
from ansible_collections.os_migrate.os_migrate.plugins.module_utils import filesystem
from ansible_collections.os_migrate.os_migrate.tests.unit import fixtures
from ansible_collections.os_migrate.os_migrate.tests.unit import utils


class TestFilesystem(unittest.TestCase):

    def test_write_or_replace_resource_new_file(self):
        minimal_resource = fixtures.MinimalResource.from_data(
            fixtures.valid_minimalresource_data())
        with utils.tmp_dir_context() as tmp_dir:
            file_path = path.join(tmp_dir, 'resources.yml')
            filesystem.write_or_replace_resource(
                file_path, minimal_resource)

            file_struct = filesystem.load_resources_file(file_path)
            resource = file_struct['resources'][0]
            self.assertEqual(resource['type'], 'openstack.Minimal')
            self.assertEqual(resource['params']['name'], 'minimal')
            self.assertEqual(
                resource['params']['description'], 'minimal resource')

    def test_write_or_replace_resource_existing_file(self):
        with utils.tmp_dir_context() as tmp_dir:
            file_path = path.join(tmp_dir, 'resources.yml')
            with open(file_path, 'w', encoding='utf8') as f:
                f.write(yaml.dump(fixtures.minimal_resource_file_struct()))

            minimal2 = fixtures.MinimalResource.from_data(
                fixtures.valid_minimalresource_data())
            minimal2.data[const.RES_PARAMS]['name'] = 'minimal2'
            minimal2.data[const.RES_PARAMS]['description'] = 'minimal two'
            minimal2.data[const.RES_INFO]['id'] = 'id-minimal2'
            self.assertTrue(
                filesystem.write_or_replace_resource(file_path, minimal2))
            # repeated replacement should report no changes - return False
            self.assertFalse(
                filesystem.write_or_replace_resource(file_path, minimal2))

            file_struct = filesystem.load_resources_file(file_path)
            resource0 = file_struct['resources'][0]
            resource1 = file_struct['resources'][1]
            self.assertEqual(resource0['type'], 'openstack.Minimal')
            self.assertEqual(resource0['params']['name'], 'minimal')
            self.assertEqual(resource0['_info']['id'], 'id-minimal')
            self.assertEqual(
                resource0['params']['description'], 'minimal resource')
            self.assertEqual(resource1['type'], 'openstack.Minimal')
            self.assertEqual(resource1['params']['name'], 'minimal2')
            self.assertEqual(resource1['_info']['id'], 'id-minimal2')
            self.assertEqual(
                resource1['params']['description'], 'minimal two')

    def test_load_resources_file(self):
        with utils.tmp_dir_context() as tmp_dir:
            file_path = path.join(tmp_dir, 'resources.yml')

            struct = fixtures.minimal_resource_file_struct()
            with open(file_path, 'w', encoding='utf8') as f:
                f.write(yaml.dump(struct))
            self.assertEqual(filesystem.load_resources_file(file_path), struct)

            struct['os_migrate_version'] = '0.0.never-released'
            with open(file_path, 'w', encoding='utf8') as f:
                f.write(yaml.dump(struct))
            with self.assertRaises(exc.DataVersionMismatch):
                filesystem.load_resources_file(file_path)

            del struct['os_migrate_version']
            with open(file_path, 'w', encoding='utf8') as f:
                f.write(yaml.dump(struct))
            with self.assertRaises(exc.DataVersionMismatch):
                filesystem.load_resources_file(file_path)
