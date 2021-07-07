from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

import unittest

from ansible_collections.os_migrate.os_migrate.plugins.module_utils \
    import const
from ansible_collections.os_migrate.os_migrate.plugins.module_utils \
    import validation
from ansible_collections.os_migrate.os_migrate.tests.unit import fixtures


class TestValidation(unittest.TestCase):

    resrc_map = {'openstack.Minimal': fixtures.MinimalResource}

    def test_get_errors_in_file_structs_ok(self):
        file_struct = fixtures.minimal_resource_file_struct()
        self.assertEqual(
            [],
            validation.get_errors_in_file_structs([file_struct], self.resrc_map))

    def test_get_errors_in_file_structs_duplication_single(self):
        file_struct = fixtures.minimal_resource_file_struct()
        resources = file_struct['resources']
        minimal2 = fixtures.minimal_resource()
        minimal2[const.RES_INFO]['id'] = 'uuid-minimal-2'
        resources.append(minimal2)
        self.assertEqual(
            ["Resource duplication: 2 resources with import identity 'openstack.Minimal:minimal'. "
             "This would result in duplicit imports."],
            validation.get_errors_in_file_structs([file_struct], self.resrc_map))

    def test_get_errors_in_file_structs_duplication_multi(self):
        file_struct1 = fixtures.minimal_resource_file_struct()
        file_struct2 = fixtures.minimal_resource_file_struct()

        self.assertEqual(
            ["Resource duplication: 2 resources with import identity 'openstack.Minimal:minimal'. "
             "This would result in duplicit imports."],
            validation.get_errors_in_file_structs(
                [file_struct1, file_struct2], self.resrc_map))

    def test_get_errors_in_file_structs_bad_data(self):
        file_struct = fixtures.minimal_resource_file_struct()
        res = file_struct['resources'][0]
        del res['params']['name']
        self.assertEqual(
            ["openstack.Minimal::id-minimal: Missing params.name."],
            validation.get_errors_in_file_structs([file_struct], self.resrc_map))
