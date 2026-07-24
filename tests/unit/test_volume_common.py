from __future__ import absolute_import, division, print_function

__metaclass__ = type

import json
import logging
import os
import subprocess
import unittest
from unittest import mock

from ansible_collections.os_migrate.os_migrate.plugins.module_utils import volume_common
from ansible_collections.os_migrate.os_migrate.tests.unit import utils


def make_volume_base(state_file=None, volume_map=None, address="10.0.0.5"):
    """Build OpenStackVolumeBase without SSH/OpenStack init side effects."""
    obj = volume_common.OpenStackVolumeBase.__new__(
        volume_common.OpenStackVolumeBase
    )
    obj.conn = mock.Mock()
    obj.conversion_host_id = "uuid-conversion-host"
    obj.ssh_key_path = "/tmp/test.key"
    obj.ssh_user = "cloud-user"
    obj.transfer_uuid = "uuid-transfer"
    obj.conversion_host_address = address
    obj.state_file = state_file
    obj.log_file = None
    obj.timeout = 10
    obj.log = logging.getLogger("osp-osp-test")
    obj.log.addHandler(logging.NullHandler())
    obj.shell = mock.Mock()
    obj.claimed_ports = []
    obj.volume_map = volume_map if volume_map is not None else {}
    return obj


class FakeVolume:
    def __init__(self, attachments, volume_id="uuid-vol"):
        self.attachments = attachments
        self.id = volume_id


class FakeVM:
    def __init__(self, vm_id="uuid-vm"):
        self.id = vm_id


class TestRemoteShell(unittest.TestCase):

    def test_default_options_without_key(self):
        shell = volume_common.RemoteShell("10.0.0.1", "cloud-user")
        self.assertEqual(
            shell._default_options(),
            [
                "-o",
                "BatchMode=yes",
                "-o",
                "StrictHostKeyChecking=no",
                "-o",
                "ConnectTimeout=10",
            ],
        )

    def test_default_options_with_key(self):
        shell = volume_common.RemoteShell("10.0.0.1", "cloud-user", "/tmp/key")
        options = shell._default_options()
        self.assertIn("-i", options)
        self.assertIn("/tmp/key", options)

    def test_ssh_preamble(self):
        shell = volume_common.RemoteShell("10.0.0.1", "cloud-user", "/tmp/key")
        preamble = shell.ssh_preamble()
        self.assertEqual(preamble[0], "ssh")
        self.assertEqual(preamble[-1], "cloud-user@10.0.0.1")
        self.assertIn("-i", preamble)


class TestOpenStackVolumeBaseHelpers(unittest.TestCase):

    def test_converter_address_uses_override(self):
        base = make_volume_base(address="192.0.2.10")
        self.assertEqual(base._converter_address(), "192.0.2.10")
        base.conn.get_server_by_id.assert_not_called()

    def test_converter_address_falls_back_to_access_ipv4(self):
        base = make_volume_base(address=None)
        server = mock.Mock()
        server.access_ipv4 = "203.0.113.9"
        base.conn.get_server_by_id.return_value = server
        self.assertEqual(base._converter_address(), "203.0.113.9")
        base.conn.get_server_by_id.assert_called_once_with("uuid-conversion-host")

    def test_get_attachment_found(self):
        base = make_volume_base()
        vm = FakeVM("uuid-vm")
        volume = FakeVolume(
            [
                {"server_id": "other", "device": "/dev/vdb"},
                {"server_id": "uuid-vm", "device": "/dev/vda"},
            ]
        )
        self.assertEqual(
            base._get_attachment(volume, vm),
            {"server_id": "uuid-vm", "device": "/dev/vda"},
        )

    def test_get_attachment_missing_raises(self):
        base = make_volume_base()
        with self.assertRaises(RuntimeError):
            base._get_attachment(FakeVolume([]), FakeVM())

    def test_volume_still_attached(self):
        base = make_volume_base()
        vm = FakeVM("uuid-vm")
        attached = FakeVolume([{"server_id": "uuid-vm", "device": "/dev/vda"}])
        detached = FakeVolume([{"server_id": "other", "device": "/dev/vda"}])
        self.assertTrue(base._volume_still_attached(attached, vm))
        self.assertFalse(base._volume_still_attached(detached, vm))

    def test_update_progress_without_state_file(self):
        base = make_volume_base(
            state_file=None,
            volume_map={"/dev/vda": {"progress": 0.0}},
        )
        base._update_progress("/dev/vda", 42.5)
        # mapping not updated when there is no state file
        self.assertEqual(base.volume_map["/dev/vda"]["progress"], 0.0)

    def test_update_progress_writes_state_file(self):
        with utils.tmp_dir_context() as tmp_dir:
            state_path = os.path.join(tmp_dir, "progress.json")
            base = make_volume_base(
                state_file=state_path,
                volume_map={
                    "/dev/vda": {"progress": 0.0},
                    "/dev/vdb": {"progress": 10.0},
                },
            )
            base._update_progress("/dev/vda", 55.0)
            self.assertEqual(base.volume_map["/dev/vda"]["progress"], 55.0)
            with open(state_path, encoding="utf8") as f:
                self.assertEqual(
                    json.load(f),
                    {"/dev/vda": 55.0, "/dev/vdb": 10.0},
                )

    def test_check_process_empty_pid(self):
        base = make_volume_base()
        self.assertFalse(base.check_process(None))
        self.assertFalse(base.check_process(""))
        base.shell.cmd_val.assert_not_called()

    def test_check_process_running(self):
        base = make_volume_base()
        base.shell.cmd_val.return_value = 0
        self.assertTrue(base.check_process(1234))
        base.shell.cmd_val.assert_called_once_with(["sudo", "kill", "-0", "1234"])

    def test_check_process_not_running(self):
        base = make_volume_base()
        base.shell.cmd_val.side_effect = subprocess.CalledProcessError(1, "kill")
        self.assertFalse(base.check_process(9999))

    def test_test_port_available(self):
        base = make_volume_base()
        base.shell.cmd_val.return_value = 124
        self.assertTrue(base._test_port_available(49152))
        base.shell.cmd_val.return_value = 1
        self.assertFalse(base._test_port_available(49152))

    def test_read_used_ports_valid_json(self):
        base = make_volume_base()
        base.shell.cmd_out.side_effect = ["", "[49152, 49153]"]
        ports = base._OpenStackVolumeBase__read_used_ports()
        self.assertEqual(ports, {49152, 49153})

    def test_read_used_ports_invalid_json_reinitializes(self):
        base = make_volume_base()
        base.shell.cmd_out.side_effect = ["", "not-json"]
        ports = base._OpenStackVolumeBase__read_used_ports()
        self.assertEqual(ports, set())

    def test_check_and_cleanup_lockfiles_removes_stale(self):
        base = make_volume_base()
        base.shell.cmd_out.return_value = "4242"
        base.check_process = mock.Mock(return_value=False)
        self.assertTrue(base.check_and_cleanup_lockfiles())
        base.shell.cmd_val.assert_called()
        args = base.shell.cmd_val.call_args[0][0]
        self.assertEqual(args[0:3], ["sudo", "rm", "-f"])

    def test_get_volume_maybe_none_id(self):
        base = make_volume_base()
        self.assertIsNone(base._get_volume_maybe(None))
        self.assertIsNone(base._get_volume_maybe(""))
        base.conn.get_volume_by_id.assert_not_called()

    def test_get_volume_maybe_fetches(self):
        base = make_volume_base()
        vol = FakeVolume([], volume_id="uuid-vol")
        base.conn.get_volume_by_id.return_value = vol
        self.assertIs(base._get_volume_maybe("uuid-vol"), vol)

    def test_validate_volumes_match_data_ok(self):
        obj = volume_common.OpenstackVolumeExport.__new__(
            volume_common.OpenstackVolumeExport
        )
        obj.source_instance_id = "uuid-vm"
        obj.volume_map = {
            "/dev/vda": {"source_id": "vol-1"},
            "/dev/vdb": {"source_id": "vol-2"},
        }
        ser = mock.Mock()
        ser.params.return_value = {
            "volumes": [
                {"_info": {"id": "vol-1"}},
                {"_info": {"id": "vol-2"}},
            ]
        }
        obj.ser_server = ser
        obj._validate_volumes_match_data()

    def test_validate_volumes_match_data_mismatch(self):
        obj = volume_common.OpenstackVolumeExport.__new__(
            volume_common.OpenstackVolumeExport
        )
        obj.source_instance_id = "uuid-vm"
        obj.volume_map = {"/dev/vda": {"source_id": "vol-1"}}
        ser = mock.Mock()
        ser.params.return_value = {
            "volumes": [
                {"_info": {"id": "vol-1"}},
                {"_info": {"id": "vol-extra"}},
            ]
        }
        obj.ser_server = ser
        with self.assertRaises(volume_common.exc.InconsistentState):
            obj._validate_volumes_match_data()

    def test_parse_qemu_img_progress(self):
        self.assertEqual(
            volume_common.parse_qemu_img_progress("foo (12.5/100%) bar"),
            12.5,
        )
        self.assertIsNone(volume_common.parse_qemu_img_progress("no progress yet"))
        self.assertEqual(
            volume_common.parse_qemu_img_progress(
                "(99.0/100%)", volume_common.QEMU_PROGRESS_RE
            ),
            99.0,
        )

    def test_test_source_vm_shutdown_ok(self):
        base = make_volume_base()
        base._source_vm = mock.Mock(return_value=FakeVM("uuid-vm"))
        base.conn.compute.get_server.return_value = mock.Mock(status="SHUTOFF")
        base._test_source_vm_shutdown()

    def test_test_source_vm_shutdown_raises(self):
        base = make_volume_base()
        base._source_vm = mock.Mock(return_value=FakeVM("uuid-vm"))
        base.conn.compute.get_server.return_value = mock.Mock(status="ACTIVE")
        with self.assertRaises(RuntimeError):
            base._test_source_vm_shutdown()

    def test_wait_for_volume_dev_path_success(self):
        base = make_volume_base()
        vm = FakeVM("uuid-vm")
        volume = FakeVolume([], volume_id="uuid-vol")
        attached = FakeVolume(
            [{"server_id": "uuid-vm", "device": "/dev/vdc"}],
            volume_id="uuid-vol",
        )
        base.conn.get_volume_by_id.side_effect = [volume, attached]
        with mock.patch.object(volume_common.time, "sleep"):
            base._wait_for_volume_dev_path(base.conn, volume, vm, timeout=5)

    def test_wait_for_volume_dev_path_timeout(self):
        base = make_volume_base()
        vm = FakeVM("uuid-vm")
        volume = FakeVolume([], volume_id="uuid-vol")
        base.conn.get_volume_by_id.return_value = volume
        with mock.patch.object(volume_common.time, "sleep"):
            with self.assertRaises(RuntimeError) as ctx:
                base._wait_for_volume_dev_path(base.conn, volume, vm, timeout=2)
        self.assertIn("Timed out", str(ctx.exception))

    def test_attach_volumes_matching_path(self):
        base = make_volume_base(
            volume_map={"/dev/vda": {"source_id": "vol-1", "dest_dev": None}}
        )
        host = FakeVM("uuid-converter")
        volume_before = FakeVolume([], volume_id="vol-1")
        volume_after = FakeVolume(
            [{"server_id": "uuid-converter", "device": "/dev/vdb"}],
            volume_id="vol-1",
        )
        base.conn.get_volume_by_id.side_effect = [
            volume_before,
            volume_after,
        ]
        base._wait_for_volume_dev_path = mock.Mock()

        ssh_func = mock.Mock(side_effect=["/dev/vda\n", "/dev/vda\n/dev/vdb\n"])

        def update_func(mapping, path):
            mapping = dict(mapping)
            mapping["dest_dev"] = path
            return mapping

        base._attach_volumes(
            base.conn,
            "destination",
            (
                lambda: host,
                ssh_func,
                update_func,
                lambda m: m["source_id"],
            ),
        )
        self.assertEqual(base.volume_map["/dev/vda"]["dest_dev"], "/dev/vdb")
        base.conn.attach_volume.assert_called_once()

    def test_attach_volumes_path_mismatch_uses_lsblk(self):
        base = make_volume_base(
            volume_map={"/dev/vda": {"source_id": "vol-1", "dest_dev": None}}
        )
        host = FakeVM("uuid-converter")
        volume_before = FakeVolume([], volume_id="vol-1")
        volume_after = FakeVolume(
            [{"server_id": "uuid-converter", "device": "/dev/vdX"}],
            volume_id="vol-1",
        )
        base.conn.get_volume_by_id.side_effect = [volume_before, volume_after]
        base._wait_for_volume_dev_path = mock.Mock()
        ssh_func = mock.Mock(side_effect=["/dev/vda\n", "/dev/vda\n/dev/vdb\n"])

        def update_func(mapping, path):
            mapping = dict(mapping)
            mapping["dest_dev"] = path
            return mapping

        base._attach_volumes(
            base.conn,
            "destination",
            (lambda: host, ssh_func, update_func, lambda m: m["source_id"]),
        )
        self.assertEqual(base.volume_map["/dev/vda"]["dest_dev"], "/dev/vdb")

    def test_attach_volumes_unexpected_disks_raises(self):
        base = make_volume_base(
            volume_map={"/dev/vda": {"source_id": "vol-1", "dest_dev": None}}
        )
        host = FakeVM("uuid-converter")
        volume_before = FakeVolume([], volume_id="vol-1")
        volume_after = FakeVolume(
            [{"server_id": "uuid-converter", "device": "/dev/vdb"}],
            volume_id="vol-1",
        )
        base.conn.get_volume_by_id.side_effect = [volume_before, volume_after]
        base._wait_for_volume_dev_path = mock.Mock()
        ssh_func = mock.Mock(
            side_effect=["/dev/vda\n", "/dev/vda\n/dev/vdb\n/dev/vdc\n"]
        )

        with self.assertRaises(RuntimeError) as ctx:
            base._attach_volumes(
                base.conn,
                "destination",
                (
                    lambda: host,
                    ssh_func,
                    lambda m, p: m,
                    lambda m: m["source_id"],
                ),
            )
        self.assertIn("unexpected disk list", str(ctx.exception))

    def test_find_free_port_reserves_available(self):
        base = make_volume_base()
        base.check_and_cleanup_lockfiles = mock.Mock(return_value=False)
        base.shell.cmd_val.return_value = 0
        base.shell.cmd_out.return_value = ""
        used = set(range(49152, 65535)) - {50000}
        base._OpenStackVolumeBase__read_used_ports = mock.Mock(return_value=used)
        base._OpenStackVolumeBase__write_used_ports = mock.Mock()
        base._test_port_available = mock.Mock(return_value=True)

        with mock.patch.object(volume_common.time, "sleep"):
            port = base._find_free_port()

        self.assertEqual(port, 50000)
        self.assertEqual(base.claimed_ports, [50000])
        written = base._OpenStackVolumeBase__write_used_ports.call_args[0][0]
        self.assertIn(50000, written)

    def test_find_free_port_skips_unavailable(self):
        base = make_volume_base()
        base.check_and_cleanup_lockfiles = mock.Mock(return_value=False)
        base.shell.cmd_val.return_value = 0
        base.shell.cmd_out.return_value = ""
        used = set(range(49152, 65535)) - {50000, 50001}
        base._OpenStackVolumeBase__read_used_ports = mock.Mock(return_value=used)
        base._OpenStackVolumeBase__write_used_ports = mock.Mock()
        base._test_port_available = mock.Mock(side_effect=[False, True])

        with mock.patch.object(volume_common.time, "sleep"):
            port = base._find_free_port()

        self.assertIn(port, (50000, 50001))
        self.assertEqual(base._test_port_available.call_count, 2)

    def test_release_ports_removes_claimed(self):
        base = make_volume_base()
        base.claimed_ports = [50000, 50001]
        base.check_and_cleanup_lockfiles = mock.Mock(return_value=False)
        base.shell.cmd_val.return_value = 0
        base.shell.cmd_out.return_value = ""
        used = {50000, 50001, 50002}
        base._OpenStackVolumeBase__read_used_ports = mock.Mock(return_value=used)
        base._OpenStackVolumeBase__write_used_ports = mock.Mock()

        with mock.patch.object(volume_common.time, "sleep"):
            base._release_ports()

        written = base._OpenStackVolumeBase__write_used_ports.call_args[0][0]
        self.assertEqual(written, {50002})

    def test_test_port_available(self):
        base = make_volume_base()
        base.shell.cmd_val.return_value = 124
        self.assertTrue(base._test_port_available(50000))
        base.shell.cmd_val.return_value = 1
        self.assertFalse(base._test_port_available(50000))

    def test_nbdkit_direct_url(self):
        self.assertEqual(
            volume_common.nbdkit_direct_url("nbd+unix:///tmp/sock"),
            "nbd+unix:///tmp/sock",
        )
        self.assertEqual(
            volume_common.nbdkit_direct_url("nbd+unix:///tmp/sock", "export1"),
            "nbd+unix:///tmp/sock/export1",
        )

    def test_setup_nbdkit_direct_urls_assigns_urls(self):
        obj = volume_common.OpenstackVolumeTransfer.__new__(
            volume_common.OpenstackVolumeTransfer
        )
        obj.log = logging.getLogger("osp-osp-test")
        obj.log.addHandler(logging.NullHandler())
        obj.timeout = 1
        obj.shell = mock.Mock()
        obj.shell.cmd_out.return_value = "image: raw"
        obj.volume_map = {
            "/dev/vda": {"url": None},
            "/dev/vdb": {"url": None},
        }
        with mock.patch.object(volume_common.time, "sleep"):
            obj._setup_nbdkit_direct_urls("nbd+unix:///tmp/s", "exp")
        self.assertEqual(obj.volume_map["/dev/vda"]["url"], "nbd+unix:///tmp/s/exp")
        self.assertEqual(obj.volume_map["/dev/vdb"]["url"], "nbd+unix:///tmp/s/exp")
