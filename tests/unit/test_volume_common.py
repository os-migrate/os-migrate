from __future__ import absolute_import, division, print_function

__metaclass__ = type

import logging
import unittest
from unittest import mock

from ansible_collections.os_migrate.os_migrate.plugins.module_utils import volume_common


UEFI_METADATA = {"hw_firmware_type": "uefi", "hw_machine_type": "q35"}


def volume_transfer():
    # Bypass __init__, which looks up the conversion host and opens an SSH
    # connection, and wire in only what _copy_volume_image_metadata needs.
    transfer = volume_common.OpenstackVolumeTransfer.__new__(
        volume_common.OpenstackVolumeTransfer
    )
    transfer.conn = mock.Mock()
    transfer.log = logging.getLogger("test-volume-common")
    return transfer


class TestEntriesByMethod(unittest.TestCase):
    def _transfer(self, volume_map):
        transfer = volume_transfer()
        transfer.volume_map = volume_map
        return transfer

    def test_splits_mixed_map_by_transfer_method(self):
        volume_map = {
            "/dev/vda": {"transfer_method": "nbdcopy"},
            "/dev/vdc": {"transfer_method": "nbdcopy"},
            "/dev/vdb": {"source_id": "cinder-vol-id"},
        }
        transfer = self._transfer(volume_map)

        nbdcopy = transfer._entries_by_method("nbdcopy")
        convhost = transfer._entries_by_method("qemu")

        self.assertEqual(set(nbdcopy), {"/dev/vda", "/dev/vdc"})
        self.assertEqual(set(convhost), {"/dev/vdb"})

    def test_untagged_entries_default_to_conversion_host(self):
        # Entries produced by the conversion-host export (and detached volumes)
        # carry no transfer_method and must keep the previous qemu-img behaviour.
        volume_map = {"/dev/vda": {"source_id": "x"}, "/dev/vdb": {"source_id": "y"}}
        transfer = self._transfer(volume_map)

        self.assertEqual(transfer._entries_by_method("nbdcopy"), {})
        self.assertEqual(set(transfer._entries_by_method("qemu")), {"/dev/vda", "/dev/vdb"})

    def test_pure_nbdkit_map_has_no_conversion_host_entries(self):
        volume_map = {"/dev/vda": {"transfer_method": "nbdcopy"}}
        transfer = self._transfer(volume_map)

        self.assertEqual(set(transfer._entries_by_method("nbdcopy")), {"/dev/vda"})
        self.assertEqual(transfer._entries_by_method("qemu"), {})

    def test_returned_entries_share_mapping_objects(self):
        # Fields filled in later must propagate back to the original map.
        volume_map = {"/dev/vda": {"transfer_method": "nbdcopy"}}
        transfer = self._transfer(volume_map)

        subset = transfer._entries_by_method("nbdcopy")
        subset["/dev/vda"]["dest_id"] = "new-dest-id"

        self.assertEqual(volume_map["/dev/vda"]["dest_id"], "new-dest-id")


class TestCopyVolumeImageMetadata(unittest.TestCase):
    def test_posts_cinder_action_with_metadata_wrapper(self):
        transfer = volume_transfer()
        new_volume = mock.Mock(id="uuid-dest-volume")

        transfer._copy_volume_image_metadata(
            {"image_metadata": UEFI_METADATA}, new_volume
        )

        transfer.conn.block_storage.post.assert_called_once_with(
            "volumes/uuid-dest-volume/action",
            json={"os-set_image_metadata": {"metadata": UEFI_METADATA}},
        )
        transfer.conn.block_storage.post.return_value.raise_for_status.assert_called_once_with()

    def test_skips_when_no_image_metadata(self):
        for mapping in ({}, {"image_metadata": None}, {"image_metadata": {}}):
            transfer = volume_transfer()
            transfer._copy_volume_image_metadata(mapping, mock.Mock(id="uuid"))
            transfer.conn.block_storage.post.assert_not_called()

    def test_http_error_is_logged_not_raised(self):
        transfer = volume_transfer()
        response = transfer.conn.block_storage.post.return_value
        response.raise_for_status.side_effect = Exception("400 Bad Request")

        with self.assertLogs("test-volume-common", level="WARNING") as logs:
            transfer._copy_volume_image_metadata(
                {"image_metadata": UEFI_METADATA}, mock.Mock(id="uuid")
            )

        self.assertIn("400 Bad Request", logs.output[0])
