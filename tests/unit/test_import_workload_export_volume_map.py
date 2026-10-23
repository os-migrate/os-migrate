from __future__ import absolute_import, division, print_function

__metaclass__ = type

import unittest
from unittest import mock

from ansible_collections.os_migrate.os_migrate.plugins.modules import (
    import_workload_export_volume_map as evm,
)


class FakeServer:
    """Minimal stand-in for server.Server exposing the accessors the volume-map
    builders use, without needing a real OpenStack SDK object."""

    def __init__(self, params=None, info=None, migration_params=None):
        self._params = params or {}
        self._info = info or {}
        self._migration_params = migration_params or {}

    def params(self):
        return self._params

    def info(self):
        return self._info

    def migration_params(self):
        return self._migration_params


class TestBuildVolumeMapFromNbdkitDisks(unittest.TestCase):
    def test_maps_each_disk_by_device_with_real_size_and_url(self):
        srv = FakeServer(
            params={"name": "vm1"},
            migration_params={
                "nbdkit_disks": [
                    {
                        "device": "/dev/vda",
                        "size": 10,
                        "bootable": True,
                        "port": 10809,
                        "uri": "nbd://hyp:10809",
                    },
                    {
                        "device": "/dev/vdb",
                        "size": 5,
                        "bootable": False,
                        "port": 10810,
                        "uri": "nbd://hyp:10810",
                    },
                ]
            },
        )

        vmap = evm.build_volume_map_from_nbdkit_disks(srv)

        self.assertEqual(set(vmap), {"/dev/vda", "/dev/vdb"})
        self.assertTrue(vmap["/dev/vda"]["bootable"])
        self.assertFalse(vmap["/dev/vdb"]["bootable"])
        self.assertEqual(vmap["/dev/vda"]["url"], "nbd://hyp:10809")
        self.assertEqual(vmap["/dev/vda"]["port"], 10809)
        self.assertEqual(vmap["/dev/vda"]["size"], 10)
        # nbdkit local disks have no source Cinder volume
        self.assertIsNone(vmap["/dev/vda"]["source_id"])
        self.assertEqual(vmap["/dev/vdb"]["name"], "vm1-vdb")


class TestBuildVolumeMapFromVolumes(unittest.TestCase):
    def test_uses_real_attachment_device_and_source_id(self):
        srv = FakeServer(
            params={
                "volumes": [
                    {
                        "_info": {
                            "id": "vol-1",
                            "attachments": [{"device": "/dev/vdc"}],
                            "bootable": False,
                            "size": 3,
                        },
                        "params": {"name": "data-vol"},
                    }
                ]
            }
        )

        vmap = evm.build_volume_map_from_volumes(srv)

        self.assertIn("/dev/vdc", vmap)
        self.assertEqual(vmap["/dev/vdc"]["source_id"], "vol-1")
        self.assertEqual(vmap["/dev/vdc"]["size"], 3)
        self.assertEqual(vmap["/dev/vdc"]["name"], "data-vol")

    def test_device_fallback_from_bootable_when_no_attachment(self):
        srv = FakeServer(
            params={
                "volumes": [
                    {
                        "_info": {
                            "id": "vol-boot",
                            "attachments": [],
                            "bootable": True,
                            "size": 1,
                        },
                        "params": {},
                    }
                ]
            }
        )

        vmap = evm.build_volume_map_from_volumes(srv)

        self.assertIn("/dev/vda", vmap)
        self.assertTrue(vmap["/dev/vda"]["bootable"])
        self.assertEqual(vmap["/dev/vda"]["source_id"], "vol-boot")


class TestBuildVolumeMapFromEphemeral(unittest.TestCase):
    def test_boot_only_when_flavor_has_no_ephemeral(self):
        conn = mock.Mock()
        conn.compute.find_flavor.return_value = mock.Mock(ephemeral=0, disk=10)
        srv = FakeServer(params={"name": "vm", "flavor_ref": {"name": "m1.small"}})

        vmap = evm.build_volume_map_from_ephemeral(conn, srv)

        self.assertEqual(set(vmap), {"/dev/vda"})
        self.assertTrue(vmap["/dev/vda"]["bootable"])

    def test_boot_plus_one_entry_per_ephemeral_chunk(self):
        conn = mock.Mock()
        # 20 GB ephemeral -> 2 ephemeral disks (10 GB chunks) + boot
        conn.compute.find_flavor.return_value = mock.Mock(ephemeral=20, disk=10)
        srv = FakeServer(params={"name": "vm", "flavor_ref": {"name": "m1.eph"}})

        vmap = evm.build_volume_map_from_ephemeral(conn, srv)

        self.assertEqual(set(vmap), {"/dev/vda", "/dev/vdb", "/dev/vdc"})
        self.assertTrue(vmap["/dev/vda"]["bootable"])
        self.assertFalse(vmap["/dev/vdb"]["bootable"])
        self.assertFalse(vmap["/dev/vdc"]["bootable"])

    def test_empty_when_flavor_name_missing(self):
        srv = FakeServer(params={"name": "vm", "flavor_ref": {}})
        self.assertEqual(evm.build_volume_map_from_ephemeral(mock.Mock(), srv), {})


class TestBuildVolumeMap(unittest.TestCase):
    """The selection + nbdcopy tagging that run_module delegates to."""

    def _nbdkit_server(self, **extra_params):
        params = {"name": "vm"}
        params.update(extra_params)
        return FakeServer(
            params=params,
            migration_params={
                "nbdkit_disks": [
                    {
                        "device": "/dev/vda",
                        "size": 1,
                        "bootable": True,
                        "port": 1,
                        "uri": "nbd://x",
                    }
                ]
            },
        )

    def test_nbdkit_entries_tagged_nbdcopy(self):
        vmap = evm.build_volume_map(mock.Mock(), self._nbdkit_server())
        self.assertEqual(vmap["/dev/vda"]["transfer_method"], "nbdcopy")

    def test_nbdkit_disks_take_priority_over_attached_volumes(self):
        # A workload can have both nbdkit local disks and attached volumes; this
        # module only emits the nbdkit local disks (the Cinder volumes are
        # exported separately via the conversion host and merged in the role).
        srv = self._nbdkit_server(
            volumes=[
                {
                    "_info": {
                        "id": "vol-1",
                        "attachments": [{"device": "/dev/vdb"}],
                    },
                    "params": {},
                }
            ]
        )
        vmap = evm.build_volume_map(mock.Mock(), srv)
        self.assertEqual(set(vmap), {"/dev/vda"})
        self.assertEqual(vmap["/dev/vda"]["transfer_method"], "nbdcopy")


if __name__ == "__main__":
    unittest.main()
