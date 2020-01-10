from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

import yaml
from os import path
import unittest

from ansible_collections.os_migrate.os_migrate.plugins.module_utils import filesystem
from ansible_collections.os_migrate.os_migrate.tests.unit import fixtures
from ansible_collections.os_migrate.os_migrate.tests.unit import utils


class TestFilesystem(unittest.TestCase):

    def test_write_or_replace_resource_new_file(self):
        with utils.tmp_dir_context() as tmp_dir:
            file_path = path.join(tmp_dir, 'resources.yml')
            filesystem.write_or_replace_resource(
                file_path, fixtures.minimal_resource())

            file_struct = filesystem._load_resources_file(file_path)
            resource = file_struct['resources'][0]
            self.assertEqual(resource['type'], 'openstack.minimal')
            self.assertEqual(resource['params']['name'], 'minimal')
            self.assertEqual(
                resource['params']['description'], 'minimal resource')

    def test_write_or_replace_resource_existing_file(self):
        with utils.tmp_dir_context() as tmp_dir:
            file_path = path.join(tmp_dir, 'resources.yml')
            with open(file_path, 'w') as f:
                f.write(yaml.dump(fixtures.minimal_resource_file_struct()))

            minimal2 = fixtures.minimal_resource()
            minimal2['params']['name'] = 'minimal2'
            minimal2['params']['description'] = 'minimal two'
            filesystem.write_or_replace_resource(file_path, minimal2)

            file_struct = filesystem._load_resources_file(file_path)
            resource0 = file_struct['resources'][0]
            resource1 = file_struct['resources'][1]
            self.assertEqual(resource0['type'], 'openstack.minimal')
            self.assertEqual(resource0['params']['name'], 'minimal')
            self.assertEqual(
                resource0['params']['description'], 'minimal resource')
            self.assertEqual(resource1['type'], 'openstack.minimal')
            self.assertEqual(resource1['params']['name'], 'minimal2')
            self.assertEqual(
                resource1['params']['description'], 'minimal two')
