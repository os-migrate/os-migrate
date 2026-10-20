from __future__ import absolute_import, division, print_function

__metaclass__ = type

import logging
import unittest
from unittest import mock

from ansible_collections.os_migrate.os_migrate.plugins.modules import (
    import_workload_transfer_volumes as tv,
)

# Sub-methods of OpenStackDestinationVolume that transfer_exports orchestrates;
# all are mocked so we can assert the routing without touching OpenStack/SSH.
SUBMETHODS = [
    "_setup_nbdkit_disks_urls",
    "_setup_nbdkit_direct_urls",
    "_create_forwarding_process",
    "_create_destination_volumes",
    "_attach_destination_volumes",
    "_convert_destination_volumes_nbdcopy",
    "_convert_destination_volumes",
    "_detach_destination_volumes",
    "_stop_forwarding_process",
    "_release_ports",
]


def make_transfer(volume_map, nbdkit_disks=None):
    # Bypass __init__ (it opens SSH / looks up the conversion host) and wire in
    # only what transfer_exports touches. _entries_by_method stays real.
    t = tv.OpenStackDestinationVolume.__new__(tv.OpenStackDestinationVolume)
    t.volume_map = volume_map
    t.log = logging.getLogger("test-transfer-volumes")
    t.ser_server = mock.Mock()
    t.ser_server.migration_params.return_value = (
        {"nbdkit_disks": nbdkit_disks} if nbdkit_disks is not None else {}
    )
    t.nbdkit_socket_uri = "nbd://socket"
    t.nbdkit_export_name = None
    for name in SUBMETHODS:
        setattr(t, name, mock.Mock(name=name))
    return t


def nbdcopy_entry():
    return {"transfer_method": "nbdcopy", "source_id": None, "dest_id": None}


def convhost_entry(source_id="vol-1"):
    # No transfer_method tag -> defaults to the qemu/conversion-host path.
    return {"source_id": source_id, "dest_id": None}


class TestTransferExportsRouting(unittest.TestCase):
    def test_mixed_routes_each_disk_and_restores_full_map(self):
        full = {
            "/dev/vda": nbdcopy_entry(),
            "/dev/vdb": nbdcopy_entry(),
            "/dev/vdc": convhost_entry(),
        }
        t = make_transfer(
            full, nbdkit_disks=[{"device": "/dev/vda"}, {"device": "/dev/vdb"}]
        )

        seen = {}
        t._convert_destination_volumes_nbdcopy.side_effect = (
            lambda: seen.__setitem__("nbdcopy", set(t.volume_map))
        )
        t._convert_destination_volumes.side_effect = (
            lambda: seen.__setitem__("qemu", set(t.volume_map))
        )

        t.transfer_exports()

        # Local disks got nbdkit URLs; Cinder got SSH forwarding.
        t._setup_nbdkit_disks_urls.assert_called_once()
        t._create_forwarding_process.assert_called_once()
        # Destination volumes are created/attached for the whole set.
        t._create_destination_volumes.assert_called_once()
        t._attach_destination_volumes.assert_called_once()
        # Each copy step saw only its own subset of devices.
        self.assertEqual(seen["nbdcopy"], {"/dev/vda", "/dev/vdb"})
        self.assertEqual(seen["qemu"], {"/dev/vdc"})
        t._detach_destination_volumes.assert_called_once()
        # Forwarding torn down afterwards.
        t._stop_forwarding_process.assert_called_once()
        t._release_ports.assert_called_once()
        # Full map restored so the caller can build the block-device-mapping.
        self.assertEqual(set(t.volume_map), {"/dev/vda", "/dev/vdb", "/dev/vdc"})

    def test_pure_nbdkit_skips_conversion_host(self):
        full = {"/dev/vda": nbdcopy_entry(), "/dev/vdb": nbdcopy_entry()}
        t = make_transfer(
            full, nbdkit_disks=[{"device": "/dev/vda"}, {"device": "/dev/vdb"}]
        )

        t.transfer_exports()

        t._convert_destination_volumes_nbdcopy.assert_called_once()
        t._create_forwarding_process.assert_not_called()
        t._convert_destination_volumes.assert_not_called()
        t._stop_forwarding_process.assert_not_called()
        t._release_ports.assert_not_called()

    def test_pure_conversion_host_skips_nbdcopy(self):
        full = {
            "/dev/vda": convhost_entry("boot"),
            "/dev/vdb": convhost_entry("data"),
        }
        t = make_transfer(full, nbdkit_disks=None)

        t.transfer_exports()

        t._setup_nbdkit_disks_urls.assert_not_called()
        t._convert_destination_volumes_nbdcopy.assert_not_called()
        t._create_forwarding_process.assert_called_once()
        t._convert_destination_volumes.assert_called_once()
        t._stop_forwarding_process.assert_called_once()
        t._release_ports.assert_called_once()

    def test_legacy_single_disk_nbdkit_uses_socket_uri(self):
        # nbdkit entry but no nbdkit_disks list -> legacy single-socket setup.
        full = {"/dev/vda": nbdcopy_entry()}
        t = make_transfer(full, nbdkit_disks=None)

        t.transfer_exports()

        t._setup_nbdkit_direct_urls.assert_called_once_with("nbd://socket", None)
        t._setup_nbdkit_disks_urls.assert_not_called()
        t._convert_destination_volumes_nbdcopy.assert_called_once()

    def test_full_map_restored_even_if_a_step_raises(self):
        full = {"/dev/vda": nbdcopy_entry(), "/dev/vdc": convhost_entry()}
        t = make_transfer(full, nbdkit_disks=[{"device": "/dev/vda"}])
        t._convert_destination_volumes.side_effect = RuntimeError("boom")

        with self.assertRaises(RuntimeError):
            t.transfer_exports()

        # finally-block must restore the full map and tear down forwarding.
        self.assertEqual(set(t.volume_map), {"/dev/vda", "/dev/vdc"})
        t._stop_forwarding_process.assert_called_once()


if __name__ == "__main__":
    unittest.main()
