from __future__ import absolute_import, division, print_function

__metaclass__ = type

import unittest
from unittest import mock

from ansible_collections.os_migrate.os_migrate.plugins.modules.import_workload_src_check import (
    source_status_error,
)
from ansible_collections.os_migrate.os_migrate.plugins.modules.import_workload_dst_check import (
    prerequisite_error_message,
)
from ansible_collections.os_migrate.os_migrate.plugins.modules.import_workload_create_instance import (
    build_create_instance_result,
)
from ansible_collections.os_migrate.os_migrate.plugins.modules.import_workload_transfer_volumes import (
    apply_nbdkit_disks_to_volume_map,
)
from ansible_collections.os_migrate.os_migrate.plugins.modules.import_workload_prelim import (
    destination_server_exists,
    is_source_conversion_host,
    migration_log_paths,
)


class TestSourceStatusError(unittest.TestCase):

    def test_shutoff_ok(self):
        self.assertIsNone(source_status_error("web1", "SHUTOFF"))

    def test_active_fails(self):
        msg = source_status_error("web1", "ACTIVE")
        self.assertIn("web1", msg)
        self.assertIn("SHUTOFF", msg)
        self.assertIn("ACTIVE", msg)


class TestPrerequisiteErrorMessage(unittest.TestCase):

    def test_empty(self):
        self.assertIsNone(prerequisite_error_message([]))
        self.assertIsNone(prerequisite_error_message(None))

    def test_joins(self):
        self.assertEqual(
            prerequisite_error_message(["missing net", "missing flavor"]),
            "missing net missing flavor",
        )


class TestBuildCreateInstanceResult(unittest.TestCase):

    def test_no_server(self):
        self.assertEqual(
            build_create_instance_result(None, mock.Mock()),
            {"changed": False},
        )

    def test_with_server(self):
        sdk = mock.Mock(id="uuid-dst")
        ser = mock.Mock()
        ser.data = {"type": "openstack.compute.Server", "params": {"name": "web1"}}
        self.assertEqual(
            build_create_instance_result(sdk, ser),
            {
                "changed": True,
                "server": ser.data,
                "server_id": "uuid-dst",
            },
        )


class TestApplyNbdkitDisksToVolumeMap(unittest.TestCase):

    def test_updates_existing_entry(self):
        volume_map = {
            "/dev/vda": {
                "url": None,
                "port": None,
                "size": 1,
                "bootable": False,
                "source_id": "vol-1",
            }
        }
        disks = [
            {
                "device": "/dev/vda",
                "uri": "nbd://host:10809",
                "port": 10809,
                "size": 10,
                "bootable": True,
            }
        ]
        apply_nbdkit_disks_to_volume_map(volume_map, disks, "web1")
        self.assertEqual(volume_map["/dev/vda"]["url"], "nbd://host:10809")
        self.assertEqual(volume_map["/dev/vda"]["port"], 10809)
        self.assertEqual(volume_map["/dev/vda"]["size"], 10)
        self.assertTrue(volume_map["/dev/vda"]["bootable"])
        self.assertEqual(volume_map["/dev/vda"]["source_id"], "vol-1")

    def test_creates_missing_entry(self):
        volume_map = {}
        disks = [
            {
                "device": "/dev/vdb",
                "uri": "nbd://host:10810",
                "port": 10810,
                "size": 20,
                "bootable": False,
            }
        ]
        apply_nbdkit_disks_to_volume_map(volume_map, disks, "web1")
        entry = volume_map["/dev/vdb"]
        self.assertEqual(entry["url"], "nbd://host:10810")
        self.assertEqual(entry["name"], "web1-vdb")
        self.assertIsNone(entry["dest_id"])
        self.assertEqual(entry["progress"], 0.0)


class TestPrelimHelpers(unittest.TestCase):

    def test_is_source_conversion_host(self):
        self.assertTrue(is_source_conversion_host("uuid-ch", "uuid-ch"))
        self.assertFalse(is_source_conversion_host("uuid-vm", "uuid-ch"))

    def test_destination_server_exists(self):
        self.assertTrue(destination_server_exists(1))
        self.assertTrue(destination_server_exists(3))
        self.assertFalse(destination_server_exists(0))

    def test_migration_log_paths(self):
        paths = migration_log_paths("/var/log/osm", "web1")
        self.assertEqual(paths["log_file"], "/var/log/osm/web1.log")
        self.assertEqual(paths["state_file"], "/var/log/osm/web1.state")
