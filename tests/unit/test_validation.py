from __future__ import absolute_import, division, print_function

__metaclass__ = type

import unittest

from ansible_collections.os_migrate.os_migrate.plugins.module_utils import const
from ansible_collections.os_migrate.os_migrate.plugins.module_utils import validation
from ansible_collections.os_migrate.os_migrate.tests.unit import fixtures


class TestValidation(unittest.TestCase):

    resrc_map = {"openstack.Minimal": fixtures.MinimalResource}

    def test_get_errors_in_file_structs_ok(self):
        file_struct = fixtures.minimal_resource_file_struct()
        self.assertEqual(
            [], validation.get_errors_in_file_structs([file_struct], self.resrc_map)
        )

    def test_get_errors_in_file_structs_duplication_single(self):
        file_struct = fixtures.minimal_resource_file_struct()
        resources = file_struct["resources"]
        minimal2 = fixtures.minimal_resource()
        minimal2[const.RES_INFO]["id"] = "uuid-minimal-2"
        resources.append(minimal2)
        self.assertEqual(
            [
                "Resource duplication: 2 resources with import identity 'openstack.Minimal:minimal'. "
                "This would result in duplicit imports."
            ],
            validation.get_errors_in_file_structs([file_struct], self.resrc_map),
        )

    def test_get_errors_in_file_structs_duplication_multi(self):
        file_struct1 = fixtures.minimal_resource_file_struct()
        file_struct2 = fixtures.minimal_resource_file_struct()

        self.assertEqual(
            [
                "Resource duplication: 2 resources with import identity 'openstack.Minimal:minimal'. "
                "This would result in duplicit imports."
            ],
            validation.get_errors_in_file_structs(
                [file_struct1, file_struct2], self.resrc_map
            ),
        )

    def test_get_errors_in_file_structs_bad_data(self):
        file_struct = fixtures.minimal_resource_file_struct()
        res = file_struct["resources"][0]
        del res["params"]["name"]
        self.assertEqual(
            ["openstack.Minimal::id-minimal: Missing params.name."],
            validation.get_errors_in_file_structs([file_struct], self.resrc_map),
        )

    def test_get_errors_in_file_structs_empty_resources(self):
        file_struct = {
            "os_migrate_version": const.OS_MIGRATE_VERSION,
            "resources": [],
        }
        self.assertEqual(
            [],
            validation.get_errors_in_file_structs([file_struct], self.resrc_map),
        )

    def test_get_errors_in_file_structs_unknown_type(self):
        file_struct = {
            "os_migrate_version": const.OS_MIGRATE_VERSION,
            "resources": [{"type": "openstack.DoesNotExist", "params": {}, "_info": {}}],
        }
        errors = validation.get_errors_in_file_structs([file_struct], self.resrc_map)
        self.assertEqual(len(errors), 1)
        self.assertIn("Unknown resource type", errors[0])

    def test_get_errors_in_file_structs_missing_type(self):
        file_struct = {
            "os_migrate_version": const.OS_MIGRATE_VERSION,
            "resources": [{"params": {"name": "x"}, "_info": {}}],
        }
        errors = validation.get_errors_in_file_structs([file_struct], self.resrc_map)
        self.assertEqual(len(errors), 1)
        self.assertIn("missing 'type'", errors[0])

    def test_duplicate_names_different_types_ok(self):
        """Same name on different resource types is not a duplication error."""
        file_struct = fixtures.minimal_resource_file_struct()
        other = fixtures.minimal_resource()
        other[const.RES_TYPE] = "openstack.OtherMinimal"
        other[const.RES_INFO]["id"] = "uuid-other"
        # Use a second map entry with same import identity style via MinimalResource
        # but different type string — import_id includes type, so no conflict.
        class OtherMinimal(fixtures.MinimalResource):
            resource_type = "openstack.OtherMinimal"

        resrc_map = {
            "openstack.Minimal": fixtures.MinimalResource,
            "openstack.OtherMinimal": OtherMinimal,
        }
        file_struct["resources"].append(other)
        self.assertEqual(
            [],
            validation.get_errors_in_file_structs([file_struct], resrc_map),
        )
