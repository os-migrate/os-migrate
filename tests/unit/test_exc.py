from __future__ import absolute_import, division, print_function

__metaclass__ = type

import unittest

from ansible_collections.os_migrate.os_migrate.plugins.module_utils import const
from ansible_collections.os_migrate.os_migrate.plugins.module_utils import exc


class TestExceptions(unittest.TestCase):

    def test_cannot_converge(self):
        err = exc.CannotConverge("need manual fix")
        self.assertEqual(str(err), "need manual fix")

    def test_data_version_mismatch(self):
        err = exc.DataVersionMismatch("/data/networks.yml", "0.9.0")
        message = str(err)
        self.assertIn(const.OS_MIGRATE_VERSION, message)
        self.assertIn("/data/networks.yml", message)
        self.assertIn("0.9.0", message)

    def test_empty_yaml_file_error(self):
        err = exc.EmptyYAMLFileError("/data/empty.yml")
        self.assertEqual(str(err), "Detected empty resource file at /data/empty.yml")

    def test_inconsistent_state(self):
        err = exc.InconsistentState("volume attached twice")
        self.assertEqual(str(err), "Inconsistent state: 'volume attached twice'.")

    def test_unexpected_resource_type(self):
        err = exc.UnexpectedResourceType("openstack.network.Network", "bad.Type")
        self.assertEqual(
            str(err),
            "Expected resource type 'openstack.network.Network' but got 'bad.Type'.",
        )

    def test_unexpected_value(self):
        err = exc.UnexpectedValue("status", "ACTIVE", "ERROR")
        self.assertEqual(
            str(err),
            "Unexpected value of 'status': expected 'ACTIVE' but got 'ERROR'.",
        )

    def test_unexpected_choice(self):
        err = exc.UnexpectedChoice("boot_disk_copy", [True, False], "maybe")
        self.assertEqual(
            str(err),
            "Unexpected value of 'boot_disk_copy': expected one of "
            "[True, False] but got 'maybe'.",
        )

    def test_unsupported(self):
        err = exc.Unsupported("live migration")
        self.assertEqual(str(err), "Unsupported: 'live migration'.")

    def test_invalid_input_type(self):
        err = exc.InvalidInputType("data_copy", "boolean")
        self.assertEqual(str(err), "Invalid type of 'data_copy': expected 'boolean'.")
