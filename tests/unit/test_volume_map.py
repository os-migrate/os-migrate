from __future__ import absolute_import, division, print_function

__metaclass__ = type

import unittest

from ansible_collections.os_migrate.os_migrate.plugins.modules.import_workload_export_volume_map import (
    build_volume_map_from_ephemeral,
    build_volume_map_from_nbdkit_disks,
    build_volume_map_from_volumes,
)


class FakeServer:
    """Minimal stand-in for a serialized Server resource."""

    def __init__(self, params=None, migration_params=None, info=None):
        self._params = params or {}
        self._migration_params = migration_params or {}
        self._info = info or {}

    def params(self):
        return self._params

    def migration_params(self):
        return self._migration_params

    def info(self):
        return self._info


class FakeFlavor:
    def __init__(self, disk=10, ephemeral=0):
        self.disk = disk
        self.ephemeral = ephemeral


class FakeCompute:
    def __init__(self, flavor=None, find_raises=False, get_flavor=None):
        self._flavor = flavor
        self._find_raises = find_raises
        self._get_flavor = get_flavor

    def find_flavor(self, name, ignore_missing=False):
        if self._find_raises:
            raise Exception("flavor not found")
        return self._flavor

    def get_flavor(self, flavor_id):
        return self._get_flavor


class FakeConn:
    def __init__(self, compute):
        self.compute = compute


class TestBuildVolumeMapFromVolumes(unittest.TestCase):

    def test_empty_volumes(self):
        server = FakeServer(params={"volumes": []})
        self.assertEqual(build_volume_map_from_volumes(server), {})

    def test_missing_volumes_key(self):
        server = FakeServer(params={})
        self.assertEqual(build_volume_map_from_volumes(server), {})

    def test_device_from_attachment(self):
        server = FakeServer(
            params={
                "volumes": [
                    {
                        "params": {"name": "boot-vol"},
                        "_info": {
                            "id": "vol-1",
                            "bootable": True,
                            "size": 20,
                            "attachments": [{"device": "/dev/vdc"}],
                        },
                    }
                ]
            }
        )
        volume_map = build_volume_map_from_volumes(server)
        self.assertEqual(list(volume_map.keys()), ["/dev/vdc"])
        self.assertEqual(
            volume_map["/dev/vdc"],
            {
                "bootable": True,
                "dest_dev": None,
                "dest_id": None,
                "image_id": None,
                "name": "boot-vol",
                "port": None,
                "progress": 0.0,
                "size": 20,
                "snap_id": None,
                "source_dev": None,
                "source_id": "vol-1",
                "url": None,
            },
        )

    def test_attachment_without_device_defaults_to_vda(self):
        server = FakeServer(
            params={
                "volumes": [
                    {
                        "params": {"name": "vol"},
                        "_info": {
                            "id": "vol-2",
                            "attachments": [{}],
                        },
                    }
                ]
            }
        )
        volume_map = build_volume_map_from_volumes(server)
        self.assertIn("/dev/vda", volume_map)

    def test_no_attachments_bootable_uses_vda(self):
        server = FakeServer(
            params={
                "volumes": [
                    {
                        "params": {"name": "boot"},
                        "_info": {
                            "id": "vol-boot",
                            "bootable": True,
                            "size": 10,
                            "attachments": [],
                        },
                    }
                ]
            }
        )
        volume_map = build_volume_map_from_volumes(server)
        self.assertIn("/dev/vda", volume_map)
        self.assertTrue(volume_map["/dev/vda"]["bootable"])

    def test_no_attachments_non_bootable_uses_vdb(self):
        server = FakeServer(
            params={
                "volumes": [
                    {
                        "params": {"name": "data"},
                        "_info": {
                            "id": "vol-data",
                            "bootable": False,
                            "size": 50,
                            "attachments": [],
                        },
                    }
                ]
            }
        )
        volume_map = build_volume_map_from_volumes(server)
        self.assertIn("/dev/vdb", volume_map)
        self.assertFalse(volume_map["/dev/vdb"]["bootable"])

    def test_default_name_from_volume_id(self):
        server = FakeServer(
            params={
                "volumes": [
                    {
                        "params": {},
                        "_info": {
                            "id": "abc-123",
                            "bootable": True,
                            "attachments": [{"device": "/dev/vda"}],
                        },
                    }
                ]
            }
        )
        volume_map = build_volume_map_from_volumes(server)
        self.assertEqual(volume_map["/dev/vda"]["name"], "volume-abc-123")

    def test_multiple_volumes(self):
        server = FakeServer(
            params={
                "volumes": [
                    {
                        "params": {"name": "boot"},
                        "_info": {
                            "id": "vol-1",
                            "bootable": True,
                            "size": 10,
                            "attachments": [{"device": "/dev/vda"}],
                        },
                    },
                    {
                        "params": {"name": "data"},
                        "_info": {
                            "id": "vol-2",
                            "bootable": False,
                            "size": 100,
                            "attachments": [{"device": "/dev/vdb"}],
                        },
                    },
                ]
            }
        )
        volume_map = build_volume_map_from_volumes(server)
        self.assertEqual(set(volume_map.keys()), {"/dev/vda", "/dev/vdb"})
        self.assertEqual(volume_map["/dev/vda"]["source_id"], "vol-1")
        self.assertEqual(volume_map["/dev/vdb"]["source_id"], "vol-2")
        self.assertEqual(volume_map["/dev/vdb"]["size"], 100)


class TestBuildVolumeMapFromNbdkitDisks(unittest.TestCase):

    def test_empty_nbdkit_disks(self):
        server = FakeServer(params={"name": "vm1"}, migration_params={})
        self.assertEqual(build_volume_map_from_nbdkit_disks(server), {})

    def test_single_boot_disk(self):
        server = FakeServer(
            params={"name": "migration-vm"},
            migration_params={
                "nbdkit_disks": [
                    {
                        "device": "/dev/vda",
                        "size": 15,
                        "bootable": True,
                        "port": 10809,
                        "uri": "nbd://hypervisor:10809",
                    }
                ]
            },
        )
        volume_map = build_volume_map_from_nbdkit_disks(server)
        self.assertEqual(
            volume_map["/dev/vda"],
            {
                "bootable": True,
                "dest_dev": None,
                "dest_id": None,
                "image_id": None,
                "name": "migration-vm-vda",
                "port": 10809,
                "progress": 0.0,
                "size": 15,
                "snap_id": None,
                "source_dev": None,
                "source_id": None,
                "url": "nbd://hypervisor:10809",
            },
        )

    def test_multiple_disks(self):
        server = FakeServer(
            params={"name": "vm-multi"},
            migration_params={
                "nbdkit_disks": [
                    {
                        "device": "/dev/vda",
                        "size": 10,
                        "bootable": True,
                        "port": 10809,
                        "uri": "nbd://host:10809",
                    },
                    {
                        "device": "/dev/vdb",
                        "size": 20,
                        "bootable": False,
                        "port": 10810,
                        "uri": "nbd://host:10810",
                    },
                ]
            },
        )
        volume_map = build_volume_map_from_nbdkit_disks(server)
        self.assertEqual(set(volume_map.keys()), {"/dev/vda", "/dev/vdb"})
        self.assertEqual(volume_map["/dev/vda"]["name"], "vm-multi-vda")
        self.assertEqual(volume_map["/dev/vdb"]["name"], "vm-multi-vdb")
        self.assertEqual(volume_map["/dev/vdb"]["size"], 20)
        self.assertFalse(volume_map["/dev/vdb"]["bootable"])

    def test_default_vm_name_and_bootable(self):
        server = FakeServer(
            params={},
            migration_params={
                "nbdkit_disks": [
                    {
                        "device": "/dev/vda",
                        "size": 8,
                        "uri": "nbd://host:10809",
                    }
                ]
            },
        )
        volume_map = build_volume_map_from_nbdkit_disks(server)
        self.assertEqual(volume_map["/dev/vda"]["name"], "vm-vda")
        self.assertFalse(volume_map["/dev/vda"]["bootable"])
        self.assertIsNone(volume_map["/dev/vda"]["port"])


class TestBuildVolumeMapFromEphemeral(unittest.TestCase):

    def test_no_flavor_name_returns_empty(self):
        server = FakeServer(params={"name": "vm1"})
        conn = FakeConn(FakeCompute())
        self.assertEqual(build_volume_map_from_ephemeral(conn, server), {})

    def test_boot_only_no_ephemeral(self):
        flavor = FakeFlavor(disk=20, ephemeral=0)
        conn = FakeConn(FakeCompute(flavor=flavor))
        server = FakeServer(
            params={
                "name": "boot-only",
                "flavor_ref": {"name": "m1.small"},
            }
        )
        volume_map = build_volume_map_from_ephemeral(conn, server)
        self.assertEqual(set(volume_map.keys()), {"/dev/vda"})
        self.assertEqual(
            volume_map["/dev/vda"],
            {
                "bootable": True,
                "dest_dev": None,
                "dest_id": None,
                "image_id": None,
                "name": "boot-only-boot",
                "port": None,
                "progress": 0.0,
                "size": 20,
                "snap_id": None,
                "source_dev": None,
                "source_id": None,
                "url": None,
            },
        )

    def test_ephemeral_disks_split_into_10gb_chunks(self):
        flavor = FakeFlavor(disk=15, ephemeral=20)
        conn = FakeConn(FakeCompute(flavor=flavor))
        server = FakeServer(
            params={
                "name": "eph-vm",
                "flavor_ref": {"name": "m1.ephemeral"},
            }
        )
        volume_map = build_volume_map_from_ephemeral(conn, server)
        self.assertEqual(
            set(volume_map.keys()),
            {"/dev/vda", "/dev/vdb", "/dev/vdc"},
        )
        self.assertTrue(volume_map["/dev/vda"]["bootable"])
        self.assertEqual(volume_map["/dev/vda"]["size"], 15)
        self.assertEqual(volume_map["/dev/vda"]["name"], "eph-vm-boot")
        self.assertFalse(volume_map["/dev/vdb"]["bootable"])
        self.assertEqual(volume_map["/dev/vdb"]["size"], 10)
        self.assertEqual(volume_map["/dev/vdb"]["name"], "eph-vm-ephemeral0")
        self.assertEqual(volume_map["/dev/vdc"]["name"], "eph-vm-ephemeral1")
        self.assertIsNone(volume_map["/dev/vdb"]["source_id"])

    def test_find_flavor_fails_falls_back_to_flavor_id(self):
        fallback = FakeFlavor(disk=30, ephemeral=0)
        conn = FakeConn(
            FakeCompute(find_raises=True, get_flavor=fallback)
        )
        server = FakeServer(
            params={
                "name": "fallback-vm",
                "flavor_ref": {"name": "missing-flavor"},
            },
            info={"flavor_id": "uuid-flavor"},
        )
        volume_map = build_volume_map_from_ephemeral(conn, server)
        self.assertEqual(volume_map["/dev/vda"]["size"], 30)
        self.assertEqual(volume_map["/dev/vda"]["name"], "fallback-vm-boot")

    def test_find_flavor_fails_without_flavor_id_returns_empty(self):
        conn = FakeConn(FakeCompute(find_raises=True))
        server = FakeServer(
            params={
                "name": "no-id",
                "flavor_ref": {"name": "missing-flavor"},
            },
            info={},
        )
        self.assertEqual(build_volume_map_from_ephemeral(conn, server), {})

    def test_default_vm_name(self):
        flavor = FakeFlavor(disk=10, ephemeral=0)
        conn = FakeConn(FakeCompute(flavor=flavor))
        server = FakeServer(params={"flavor_ref": {"name": "m1.tiny"}})
        volume_map = build_volume_map_from_ephemeral(conn, server)
        self.assertEqual(volume_map["/dev/vda"]["name"], "vm-boot")
