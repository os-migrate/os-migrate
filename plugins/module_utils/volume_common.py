# pylint: disable=consider-using-with
from __future__ import absolute_import, division, print_function

__metaclass__ = type
from ansible_collections.os_migrate.os_migrate.plugins.module_utils.server_volume import (
    ServerVolume,
)
from ansible_collections.os_migrate.os_migrate.plugins.module_utils import exc
import json
import logging
import os
import subprocess
import time
import fcntl
import errno

# Default timeout for OpenStack operations
DEFAULT_TIMEOUT = 1800

# Lock to serialize volume attachments. This helps prevent device path
# mismatches between the OpenStack SDK and /dev in the VM.
ATTACH_LOCK_FILE_SOURCE = "/var/lock/v2v-source-volume-lock"
ATTACH_LOCK_FILE_DESTINATION = "/var/lock/v2v-destination-volume-lock"

# File containing ports used by all the nbdkit processes running on the source
# conversion host. There is a check to see if the port is available, but this
# should speed things up.
PORT_MAP_FILE = "/var/run/v2v-migration-ports"
PORT_LOCK_FILE = "/var/lock/v2v-migration-lock"  # Lock for the port map

try:
    # will be fixed in another PR
    # pylint: disable-next=unused-import
    from subprocess import DEVNULL
except ImportError:
    DEVNULL = open(os.devnull, "r+", encoding="utf8")


def use_lock(lock_file):
    """Boilerplate for functions that need to take a lock."""

    def _decorate_lock(function):
        def wait_for_lock(self):
            if self.check_and_cleanup_lockfiles():
                self.log.info("Cleaned up unused lockfiles before start")
            for second in range(DEFAULT_TIMEOUT):
                try:
                    self.log.info("Waiting for lock %s...", lock_file)
                    lock = lock_file + ".lock"
                    pid = str(os.getpid())
                    cmd = [
                        "sudo",
                        "flock",
                        "--timeout",
                        "1",
                        "--conflict-exit-code",
                        "16",
                        lock_file,
                        "-c",
                        '"( test ! -e '
                        + lock
                        + " || exit 17 ) "
                        + "&& echo "
                        + pid
                        + " | sudo "
                        + " tee "
                        + lock
                        + '"',
                    ]
                    result = self.shell.cmd_val(cmd)
                    if result == 16:
                        self.log.info("Another conversion has the lock.")
                    elif result == 17:
                        self.log.info("Another conversion is holding the lock.")
                    elif result == 0:
                        break
                    time.sleep(1)
                except subprocess.CalledProcessError as err:
                    time.sleep(1)
                    self.log.info("Error waiting for lock: %s", str(err))
            else:
                raise RuntimeError("Unable to acquire lock " + lock_file)
            try:
                return function(self)
            finally:
                try:
                    lock = lock_file + ".lock"
                    result = self.shell.cmd_out(["sudo", "rm", "-f", lock])
                    self.log.debug("Released lock: %s", result)
                except subprocess.CalledProcessError as err:
                    self.log.error("Error releasing lock: %s", str(err))

        return wait_for_lock

    return _decorate_lock


class OpenStackVolumeBase:
    def __init__(
        self,
        openstack_connection,
        conversion_host_id,
        ssh_key_path,
        ssh_user,
        transfer_uuid,
        conversion_host_address=None,
        state_file=None,
        log_file=None,
        timeout=DEFAULT_TIMEOUT,
    ):
        # Required common parameters:
        # openstack_connection: OpenStack connection object
        # conversion_host_id: ID of conversion host instance
        # ssh_key_path: Path to SSH key authorized on conversion host
        # ssh_user: Username to create the SSH connection
        # transfer_uuid: UUID to mark processes on conversion hosts
        self.conn = openstack_connection
        self.conversion_host_id = conversion_host_id
        self.ssh_key_path = ssh_key_path
        self.ssh_user = ssh_user
        self.transfer_uuid = transfer_uuid

        # Optional parameters:
        # conversion_host_address: Optional address used to override 'access_ipv4'
        # state_file: File to hold current disk transfer state
        # log_file: Debug log path for volume migration
        self.conversion_host_address = conversion_host_address
        self.state_file = state_file
        self.log_file = log_file
        self.timeout = timeout
        # Configure logging
        self.log = logging.getLogger("osp-osp")
        log_format = logging.Formatter(
            "%(asctime)s:%(levelname)s: " + "%(message)s (%(module)s:%(lineno)d)"
        )
        if log_file:
            log_handler = logging.FileHandler(log_file)
        else:
            log_handler = logging.NullHandler()
        log_handler.setFormatter(log_format)
        self.log.addHandler(log_handler)
        self.log.setLevel(logging.DEBUG)

        if self._converter() is None:
            raise RuntimeError(f"Cannot find instance {self.conversion_host_id}")

        self.shell = RemoteShell(self._converter_address(), ssh_user, ssh_key_path)
        self.shell.test_ssh_connection()

        # Ports chosen for NBD export
        self.claimed_ports = []

    def _source_vm(self):
        """
        Changes to the VM returned by get_server_by_id are not necessarily
        reflected in existing objects, so just get a new one every time.
        """
        return self.conn.get_server_by_id(self.source_instance_id)

    def _test_source_vm_shutdown(self):
        """Make sure the source VM is shutdown, and fail if it isn't."""
        server = self.conn.compute.get_server(self._source_vm().id)
        if server.status != "SHUTOFF":
            raise RuntimeError("Source VM is not shut down!")

    def delete_migrated_volumes(self):
        """Detach destination volumes from converter and delete them."""
        self._detach_volumes_from_destination_converter()
        self._delete_volumes()

    def _volume_still_attached(self, volume, vm):
        """Check if a volume is still attached to a VM."""
        for attachment in volume.attachments:
            if attachment["server_id"] == vm.id:
                return True
        return False

    def _get_volume_maybe(self, id_maybe):
        """Get volume by id, or None if id_maybe is None or if volume doesn't exist."""
        if not id_maybe:
            return None
        return self.conn.get_volume_by_id(id_maybe)

    @use_lock(ATTACH_LOCK_FILE_DESTINATION)
    def _detach_volumes_from_destination_converter(self):
        """Detach volumes from conversion host."""
        self.log.info("Detaching volumes from the destination conversion host.")
        converter = self._converter()
        for path, mapping in self.volume_map.items():
            volume = self._get_volume_maybe(mapping["dest_id"])
            if not volume:
                continue
            if not self._volume_still_attached(volume, converter):
                self.log.info(
                    "Volume %s is not attached to conversion host, skipping detach.",
                    volume["id"],
                )
                continue

            self.log.info("Detaching volume %s.", volume["id"])
            self.conn.detach_volume(
                server=converter, volume=volume, timeout=self.timeout, wait=True
            )
            for second in range(self.timeout):
                converter = self._converter()
                volume = self.conn.get_volume_by_id(mapping["dest_id"])
                if not self._volume_still_attached(volume, converter):
                    break
                time.sleep(1)
            else:
                raise RuntimeError(
                    "Timed out waiting to detach volumes from "
                    "destination conversion host!"
                )

    def _converter_close_exports(self):
        """
        SSH to source conversion host and close the NBD export process.
        """
        self.log.info("Stopping exports from source conversion host...")
        try:
            pattern = "'" + self.transfer_uuid + "'"
            pids = self.shell.cmd_out(["pgrep", "-f", pattern]).split("\n")
            if len(pids) > 0:
                self.log.debug("Stopping NBD export PIDs (%s)", str(pids))
                try:
                    self.shell.cmd_out(["sudo", "pkill", "-f", pattern])
                except subprocess.CalledProcessError as err:
                    self.log.debug("Error stopping exports! %s", str(err))
        except subprocess.CalledProcessError as err:
            self.log.debug("Unable to get remote NBD PID! %s", str(err))

        self._release_ports()

    def _delete_volumes(self):
        """Delete destination volumes."""
        self.log.info("Deleting migrated volumes from destination.")
        for path, mapping in self.volume_map.items():
            volume = self._get_volume_maybe(mapping["dest_id"])
            if not volume:
                continue
            if volume.attachments:
                self.log.warning(
                    "Volume %s is still has attachments, skipping delete.", volume["id"]
                )
                continue

            self.log.info("Deleting volume %s.", volume["id"])
            self.conn.delete_volume(volume["id"], timeout=self.timeout, wait=True)

    def check_process(self, pid):
        """Check whether pid exists in the current process table."""
        if not pid:
            return False
        try:
            self.shell.cmd_val(["sudo", "kill", "-0", str(pid)])
        except subprocess.CalledProcessError:
            return False
        else:
            return True

    def check_and_cleanup_lockfiles(self):
        """
        Removes lockfiles found in specific directories.
        If a lockfile is not being used by a process,
        it is either deleted or not being used.
        """
        # Remove specific lockfiles
        try:
            # Remove specific lockfiles
            for lockfile in [
                ATTACH_LOCK_FILE_SOURCE,
                ATTACH_LOCK_FILE_DESTINATION,
                PORT_LOCK_FILE,
            ]:
                pid = None
                try:
                    # Use self.shell.cmd_out to run the following command on the conversion host
                    pid = self.shell.cmd_out(["sudo", "cat", f"{lockfile}.lock"])
                except Exception as err:
                    self.log.debug("Lockfile doesn't exist %s", err)

                if pid:
                    if self.check_process(pid):
                        continue

                    # The lockfile is not being used by a process, so we can remove it
                    self.shell.cmd_val(["sudo", "rm", "-f", lockfile + ".lock"])
                    return True
        except FileNotFoundError:
            return False

    def _converter(self):
        """Refresh server object to pick up any changes."""
        return self.conn.get_server_by_id(self.conversion_host_id)

    def _converter_address(self):
        """Get IP address of conversion host."""
        if self.conversion_host_address:
            return self.conversion_host_address
        else:
            return self._converter().access_ipv4

    def _update_progress(self, dev_path, progress):
        self.log.info("Transfer progress for %s: %s%%", dev_path, str(progress))
        if self.state_file is None:
            return
        self.volume_map[dev_path]["progress"] = progress
        with open(self.state_file, "w", encoding="utf8") as state:
            all_progress = {}
            for path, mapping in self.volume_map.items():
                all_progress[path] = mapping["progress"]
            json.dump(all_progress, state)

    def _attach_volumes(self, conn, name, funcs):
        """
        Attach all volumes in the volume map to the specified conversion host.
        Check the list of disks before and after attaching to be absolutely
        sure the right source data gets copied to the right destination disk.
        This is here because _attach_destination_volumes and
        _attach_volumes_to_converter looked almost identical.
        """
        self.log.info("Attaching volumes to %s wrapper", name)
        self.log.info("Volumes: %s", self.volume_map)
        host_func, ssh_func, update_func, volume_id_func = funcs
        self.log.info(
            "FUNCS: %s, %s, %s, %s", host_func, ssh_func, update_func, volume_id_func
        )
        for path, mapping in sorted(self.volume_map.items()):
            volume_id = volume_id_func(mapping)
            volume = conn.get_volume_by_id(volume_id)
            self.log.info("Attaching %s to %s conversion host", volume_id, name)

            disks_before = ssh_func(
                [
                    "lsblk",
                    "--noheadings",
                    "--list",
                    "--paths",
                    "--nodeps",
                    "--output NAME",
                ]
            )
            disks_before = set(disks_before.split())
            self.log.debug("Initial disk list: %s", disks_before)

            conn.attach_volume(
                volume=volume, wait=True, server=host_func(), timeout=self.timeout
            )
            self.log.info("Waiting for volume to appear in %s wrapper", name)
            self._wait_for_volume_dev_path(conn, volume, host_func(), self.timeout)

            disks_after = ssh_func(
                [
                    "lsblk",
                    "--noheadings",
                    "--list",
                    "--paths",
                    "--nodeps",
                    "--output NAME",
                ]
            )
            disks_after = set(disks_after.split())
            self.log.debug("Updated disk list: %s", disks_after)

            new_disks = disks_after - disks_before
            volume = conn.get_volume_by_id(volume_id)
            attachment = self._get_attachment(volume, host_func())
            dev_path = attachment["device"]
            if len(new_disks) == 1:
                if dev_path in new_disks:
                    self.log.debug(
                        "Successfully attached new disk %s, and %s "
                        "conversion host path matches OpenStack.",
                        dev_path,
                        name,
                    )
                else:
                    dev_path = new_disks.pop()
                    self.log.debug(
                        "Successfully attached new disk %s, but %s "
                        "conversion host path does not match the  "
                        "result from OpenStack. Using internal "
                        "device path %s.",
                        attachment["device"],
                        name,
                        dev_path,
                    )
            else:
                raise RuntimeError(
                    "Got unexpected disk list after attaching "
                    f"volume to {name} conversion host instance. "
                    "Failing migration procedure to avoid "
                    "assigning volumes incorrectly. New "
                    f"disks(s) inside VM: {new_disks}, disk provided by "
                    f"OpenStack: {dev_path}"
                )
            self.volume_map[path] = update_func(mapping, dev_path)

    def _get_attachment(self, volume, vm):
        """
        Get the attachment object from the volume with the matching server ID.
        Convenience method for use only when the attachment is already certain.
        """
        for attachment in volume.attachments:
            if attachment["server_id"] == vm.id:
                return attachment
        raise RuntimeError("Volume is not attached to the specified instance!")

    def _wait_for_volume_dev_path(self, conn, volume, vm, timeout):
        volume_id = volume.id
        for second in range(timeout):
            volume = conn.get_volume_by_id(volume_id)
            if volume.attachments:
                attachment = self._get_attachment(volume, vm)
                if attachment["device"].startswith("/dev/"):
                    return
            time.sleep(1)
        raise RuntimeError("Timed out waiting for volume device path!")

    def __read_used_ports(self):
        """
        Should only be called from functions locking the port list file, e.g.
        _find_free_port and _release_ports. Returns a set containing the ports
        currently used by all the migrations running on this conversion host.
        """
        try:
            cmd = [
                "sudo",
                "bash",
                "-c",
                f'"test -e {PORT_MAP_FILE} || echo [] > {PORT_MAP_FILE}"',
            ]
            result = self.shell.cmd_out(cmd)
            if result:
                self.log.debug("Port write result: %s", result)
        except subprocess.CalledProcessError as err:
            raise RuntimeError("Unable to initialize port map file!") from err

        try:  # Try to read in the set of used ports
            cmd = ["sudo", "cat", PORT_MAP_FILE]
            result = self.shell.cmd_out(cmd)
            used_ports = set(json.loads(result))
        except ValueError:
            self.log.info(
                "Unable to read port map from %s, re-initializing it...",
                PORT_MAP_FILE,
            )
            used_ports = set()
        except subprocess.CalledProcessError as err:
            self.log.debug("Unable to get port map! %s", str(err))

        self.log.info("Currently used ports: %s", str(list(used_ports)))
        return used_ports

    def __write_used_ports(self, used_ports):
        """
        Should only be called from functions locking the port list file, e.g.
        _find_free_port and _release_ports. Writes out the given port list to
        the port list file on the current conversion host.
        """
        try:  # Write out port map to destination conversion host
            cmd = ["-T", "sudo", "bash", "-c", '"cat > ' + PORT_MAP_FILE + '"']
            input_json = json.dumps(list(used_ports))
            sub = self.shell.cmd_sub(
                cmd,
                stdin=subprocess.PIPE,
                stderr=subprocess.PIPE,
                stdout=subprocess.PIPE,
                universal_newlines=True,
            )
            out, err = sub.communicate(input_json)
            if out:
                self.log.debug("Wrote port file, stdout: %s", out)
            if err:
                self.log.debug("Wrote port file, stderr: %s", err)
        except subprocess.CalledProcessError as err:
            self.log.debug(
                "Unable to write port map to conversion host! Error was: %s",
                str(err),
            )

    @use_lock(PORT_LOCK_FILE)
    def _find_free_port(self):
        """
        Reserve ports on the current conversion host. Lock a file containing
        the used ports, select some ports from the range that is unused, and
        check that the port is available on the conversion host. Add this to
        the locked file and unlock it for the next conversion.
        """
        used_ports = self.__read_used_ports()

        # Choose ports from the available possibilities, and try to bind
        ephemeral_ports = set(range(49152, 65535))
        available_ports = ephemeral_ports - used_ports

        try:
            port = available_ports.pop()
            while not self._test_port_available(port):
                self.log.info("Port %d not available, trying another.", port)
                used_ports.add(port)  # Mark used to avoid trying again
                port = available_ports.pop()
        except KeyError as err:
            raise RuntimeError("No free ports on conversion host!") from err
        used_ports.add(port)
        self.__write_used_ports(used_ports)
        self.log.info("Allocated port %d, all used: %s", port, used_ports)

        self.claimed_ports.append(port)
        return port

    @use_lock(PORT_LOCK_FILE)
    def _release_ports(self):
        used_ports = self.__read_used_ports()

        for port in self.claimed_ports:
            try:
                used_ports.remove(port)
            except KeyError:
                self.log.debug("Port already released? %d", port)

        self.log.info("Cleaning used ports: %s", used_ports)
        self.__write_used_ports(used_ports)

    def _test_port_available(self, port):
        """
        See if a port is open on the source conversion host by trying to listen
        on it.
        """
        result = self.shell.cmd_val(["timeout", "1", "nc", "-l", str(port)])
        # The 'timeout' command returns 124 when the command times out, meaning
        # nc was successful and the port is free.
        return result == 124


class RemoteShell:
    def __init__(self, address, ssh_user, key_path=None):
        self.address = address
        self.ssh_user = ssh_user
        self.key_path = key_path

    def _default_options(self):
        options = [
            "-o",
            "BatchMode=yes",
            "-o",
            "StrictHostKeyChecking=no",
            "-o",
            "ConnectTimeout=10",
        ]
        if self.key_path:
            options.extend(["-i", self.key_path])
        return options

    def ssh_preamble(self):
        """Common options to SSH into a conversion host."""
        preamble = ["ssh"]
        preamble.extend(self._default_options())
        preamble.extend([self.ssh_user + "@" + self.address])
        return preamble

    def cmd_out(self, command, **kwargs):
        """Run command on the target conversion host and get the output."""
        args = self.ssh_preamble()
        args.extend(command)
        return subprocess.check_output(args, **kwargs).decode("utf-8").strip()

    def cmd_val(self, command, **kwargs):
        """Run command on the target conversion host and get return code."""
        args = self.ssh_preamble()
        args.extend(command)
        return subprocess.call(args, **kwargs)

    def cmd_sub(self, command, **kwargs):
        """Start a long-running command on the target conversion host."""
        args = self.ssh_preamble()
        args.extend(command)
        return subprocess.Popen(args, **kwargs)

    def scp_to(self, source, destination):
        """Copy a file to the target conversion host."""
        command = ["scp"]
        command.extend(self._default_options())
        remote_path = self.ssh_user + "@" + self.address + ":" + destination
        command.extend([source, remote_path])
        return subprocess.call(command)

    def scp_from(self, source, destination, recursive=False):
        """Copy a file from the source conversion host."""
        command = ["scp"]
        command.extend(self._default_options())
        if recursive:
            command.extend(["-r"])
        remote_path = self.ssh_user + "@" + self.address + ":" + source
        command.extend([remote_path, destination])
        return subprocess.call(command)

    def test_ssh_connection(self):
        """Quick SSH connectivity check."""
        out = self.cmd_out(["echo connected"])
        if out != "connected":
            raise RuntimeError(self.address + ": SSH test unsuccessful!")


class OpenstackVolumeExport(OpenStackVolumeBase):
    """Export volumes from an OpenStack instance over NBD."""

    def prepare_exports(self):
        """
        Prepare the volumes to be exported. This method needs to be implemented in the
        class that exports the VM or the list of detached volumes
        """
        raise NotImplementedError("Please Implement this method")

    def _get_root_and_data_volumes(self):
        """
        Volume mapping step one: get the IDs and sizes of all volumes.
        Key off the original device path to eventually preserve this
        order on the destination. This method needs to be implemented in the
        class that exports the VM or the list of detached volumes
        """
        raise NotImplementedError("Please Implement this method")

    def _validate_volumes_match_data(self):
        """
        Check that the volumes as exported into the workload metadata YAML
        still match what is actually attached on the source VM, raise
        an error if not.
        """
        scanned_volume_ids = set(
            map(lambda vol: vol["source_id"], self.volume_map.values())
        )
        data_volume_ids = set(
            map(
                lambda vol: vol.get("_info", {}).get("id"),
                self.ser_server.params()["volumes"],
            )
        )
        if data_volume_ids != scanned_volume_ids:
            message = (
                f"The scanned set of volumes on instance '{self.source_instance_id}' is not the same "
                f"as in the exported data. Scanned: {scanned_volume_ids}. In data: {data_volume_ids}."
            )
            raise exc.InconsistentState(message)

    def _detach_data_volumes_from_source(self):
        """
        Detach data volumes from source VM, and pretend to "detach" the boot
        volume by creating a new volume from a snapshot of the VM. If the VM is
        booted directly from an image, take a VM snapshot and create the new
        volume from that snapshot.
        Volume map step two: replace boot disk ID with this new volume's ID,
        and record snapshot/image ID for later deletion.
        """
        sourcevm = self._source_vm()
        if "/dev/vda" in self.volume_map:
            mapping = self.volume_map["/dev/vda"]
            volume_id = mapping["source_id"]

            # Create a snapshot of the root volume
            self.log.info("Boot-from-volume instance, creating boot volume snapshot")
            root_snapshot = self.conn.create_volume_snapshot(
                force=True,
                wait=True,
                volume_id=volume_id,
                name=f"{self.boot_volume_prefix}{volume_id}",
                timeout=self.timeout,
            )

            # Create a new volume from the snapshot
            self.log.info("Creating new volume from boot volume snapshot")
            root_volume_copy = self.conn.create_volume(
                wait=True,
                name=f"{self.boot_volume_prefix}{volume_id}",
                snapshot_id=root_snapshot.id,
                size=root_snapshot.size,
                timeout=self.timeout,
            )

            # Update the volume map with the new volume ID
            self.volume_map["/dev/vda"]["source_id"] = root_volume_copy.id
            self.volume_map["/dev/vda"]["snap_id"] = root_snapshot.id
        elif sourcevm.image and self.ser_server.migration_params()["boot_disk_copy"]:
            self.log.info(
                "Image-based instance, boot_disk_copy enabled: creating snapshot"
            )
            image = self.conn.compute.create_server_image(
                name=f"{self.boot_volume_prefix}{sourcevm.name}",
                server=sourcevm.id,
                wait=True,
                timeout=self.timeout,
            )
            image = self.conn.get_image_by_id(image.id)  # refresh
            if image.status != "active":
                raise RuntimeError(
                    "Could not create new image of image-based instance!"
                )
            volume = self.conn.create_volume(
                image=image.id,
                bootable=True,
                wait=True,
                name=image.name,
                timeout=self.timeout,
                size=max(image.size // (1024**3), image.min_disk),
            )
            self.volume_map["/dev/vda"] = dict(
                source_dev=None,
                source_id=volume["id"],
                dest_dev=None,
                dest_id=None,
                snap_id=None,
                image_id=image.id,
                name=volume["name"],
                size=volume["size"],
                port=None,
                url=None,
                progress=None,
                bootable=volume["bootable"],
            )
            self._update_progress("/dev/vda", 0.0)
        elif (
            sourcevm.image and not self.ser_server.migration_params()["boot_disk_copy"]
        ):
            self.log.info(
                "Image-based instance, boot_disk_copy disabled: skipping boot volume"
            )
        else:
            raise RuntimeError("No known boot device found for this instance!")

        for path, mapping in self.volume_map.items():
            if path != "/dev/vda":  # Detach non-root volumes
                volume_id = mapping["source_id"]
                volume = self.conn.get_volume_by_id(volume_id)
                self.log.info("Detaching %s from %s", volume["id"], sourcevm.id)
                self.conn.detach_volume(
                    server=sourcevm, volume=volume, wait=True, timeout=self.timeout
                )

    # Lock this part to have a better chance of the OpenStack device path
    # matching the device path seen inside the conversion host.
    @use_lock(ATTACH_LOCK_FILE_SOURCE)
    def _attach_volumes_to_converter(self):
        """
        Attach all the source volumes to the conversion host. Volume mapping
        step 3: fill in the volume's device path on the source conversion host.
        """

        def update_source(volume_mapping, dev_path):
            volume_mapping["source_dev"] = dev_path
            return volume_mapping

        def volume_id(volume_mapping):
            return volume_mapping["source_id"]

        self._attach_volumes(
            self.conn,
            "source",
            (self._converter, self.shell.cmd_out, update_source, volume_id),
        )

    def _export_volumes_from_converter(self):
        """
        SSH to source conversion host and start an NBD export. Volume mapping
        step 4: fill in the URL to the volume's matching NBD export.
        """
        self.log.info("Exporting volumes from source conversion host...")
        for path, mapping in self.volume_map.items():
            port = self._find_free_port()
            volume_id = mapping["source_id"]
            disk = mapping["source_dev"]
            self.log.info("Exporting %s from volume %s", disk, volume_id)

            # Fall back to qemu-nbd if nbdkit is not present
            qemu_nbd_present = self.shell.cmd_val(["which", "qemu-nbd"]) == 0
            nbdkit_present = self.shell.cmd_val(["which", "nbdkit"]) == 0
            if nbdkit_present:
                dump_plugin = ["nbdkit", "--dump-plugin", "file"]
                file_plugin_present = self.shell.cmd_val(dump_plugin) == 0
                if not file_plugin_present:
                    self.log.info("Found nbdkit, but without file plugin.")
            else:
                file_plugin_present = False

            if nbdkit_present and file_plugin_present:
                cmd = [
                    "sudo",
                    "nbdkit",
                    "--exportname",
                    self.transfer_uuid,
                    "--ipaddr",
                    "127.0.0.1",
                    "--port",
                    str(port),
                    "file",
                    "file=" + disk,
                ]
                self.log.info("Using nbdkit for export command: %s", cmd)
            elif qemu_nbd_present:
                cmd = [
                    "sudo",
                    "qemu-nbd",
                    "-p",
                    str(port),
                    "-b",
                    "127.0.0.1",
                    "--fork",
                    "--verbose",
                    "--read-only",
                    "--persistent",
                    "-x",
                    self.transfer_uuid,
                    disk,
                ]
                self.log.info("Using qemu-nbd for export command: %s", cmd)
            else:
                raise RuntimeError("No supported NBD export tool available!")

            self.log.info("Exporting %s over NBD, port %s", disk, str(port))
            result = self.shell.cmd_out(cmd)
            if result:
                self.log.debug("Result from NBD exporter: %s", result)

            # Check qemu-img info on this disk to make sure it is ready
            self.log.info("Waiting for valid qemu-img info on all exports...")
            for second in range(self.timeout):
                try:
                    cmd = [
                        "qemu-img",
                        "info",
                        "nbd://localhost:" + str(port) + "/" + self.transfer_uuid,
                    ]
                    image_info = self.shell.cmd_out(cmd)
                    self.log.info("qemu-img info for %s: %s", disk, image_info)
                except subprocess.CalledProcessError as error:
                    self.log.info("Got exception: %s", error)
                    self.log.info("Trying again.")
                    time.sleep(1)
                else:
                    self.log.info("All volume exports ready.")
                    break
            else:
                raise RuntimeError("Timed out starting nbdkit exports!")

            # pylint: disable=unnecessary-dict-index-lookup
            self.volume_map[path]["port"] = port
            self.log.info("Volume map so far: %s", self.volume_map)


class OpenstackVolumeTransfer(OpenStackVolumeBase):

    def transfer_exports(self):
        """
        Method to transfer volumes. This method needs to be implemented in the
        class that transfers the VM or the list of detached volumes
        """
        raise NotImplementedError("Please Implement this method")

    def _create_forwarding_process(self):
        """
        Find free ports on the destination conversion host and set up SSH
        forwarding to the NBD ports listening on the source conversion host.
        """
        # It is expected that key authorization has already been set up from
        # the destination conversion host to the source conversion host!
        source_shell = RemoteShell(
            self.source_conversion_host_address, ssh_user=self.shell.ssh_user
        )
        forward_ports = ["-N", "-T"]
        for path, mapping in self.volume_map.items():
            port = self._find_free_port()
            forward = f"{port}:localhost:{mapping['port']}"
            forward_ports.extend(["-L", forward])
            url = "nbd://localhost:" + str(port) + "/" + self.transfer_uuid
            self.volume_map[path]["url"] = url
        command = source_shell.ssh_preamble()
        command.extend(forward_ports)
        self.log.debug("SSH forwarding command: %s", " ".join(command))
        self.forwarding_process = self.shell.cmd_sub(command)
        self.forwarding_process_command = " ".join(command)

        # Check qemu-img info on all the disks to make sure everything is ready
        self.log.info("Waiting for valid qemu-img info on all exports...")
        pending_disks = set(self.volume_map.keys())
        for second in range(self.timeout):
            try:
                for disk in pending_disks.copy():
                    mapping = self.volume_map[disk]
                    url = mapping["url"]
                    cmd = ["qemu-img", "info", url]
                    image_info = self.shell.cmd_out(cmd)
                    self.log.info("qemu-img info for %s: %s", disk, image_info)
                    pending_disks.remove(disk)
            except subprocess.CalledProcessError as error:
                self.log.info("Got exception: %s", error)
                self.log.info("Trying again.")
                time.sleep(1)
            else:
                self.log.info("All volume exports ready.")
                break
        else:
            raise RuntimeError("Timed out starting nbdkit exports!")

    def _stop_forwarding_process(self):
        self.log.info("Stopping export forwarding on source conversion host...")
        self.log.debug("(PID was %s)", self.forwarding_process.pid)
        if self.forwarding_process:
            self.forwarding_process.terminate()

        if self.forwarding_process_command:
            self.log.info("Stopping forwarding from source conversion host...")
            try:
                pattern = 'pgrep -f "' + self.forwarding_process_command + '"'
                pids = self.shell.cmd_out([pattern]).split("\n")
                for pid in pids:  # There should really only be one of these
                    try:
                        out = self.shell.cmd_out(["sudo", "kill", pid])
                        self.log.debug("Stopped forwarding PID (%s). %s", pid, out)
                    except subprocess.CalledProcessError as err:
                        self.log.debug("Unable to stop PID %s! %s", pid, str(err))
            except subprocess.CalledProcessError as err:
                self.log.debug("Unable to get forwarding PID! %s", str(err))

    def _create_destination_volumes(self):
        """
        Volume mapping step 5: create new volumes on the destination OpenStack,
        and fill in dest_id with the new volumes.
        """
        self.log.info("Creating volumes on destination cloud")
        attached_volumes = hasattr(self, "ser_server")
        if attached_volumes:
            volumes = list(
                map(ServerVolume.from_data, self.ser_server.params()["volumes"])
            )
            src_id_volumes = {vol.info()["id"]: vol for vol in volumes}
        for path, mapping in self.volume_map.items():
            source_id = mapping["source_id"]
            sdk_params = {
                "name": mapping["name"],
                "bootable": mapping["bootable"],
                "size": mapping["size"],
                "wait": True,
                "timeout": self.timeout,
            }
            if attached_volumes:
                if source_id in src_id_volumes:
                    sdk_params.update(src_id_volumes[source_id].sdk_params(self.conn))
                elif path == "/dev/vda":
                    # This code path is exercised when the source VM has
                    # no boot volume but is being migrated with
                    # `boot_disk_copy: true` and a boot volume is being
                    # created in the destination.
                    # `None` value in boot_volume_params means we do not
                    # want to override that parameter.
                    boot_volume_params_defined = dict(
                        filter(
                            lambda item: item[1] is not None,
                            self.ser_server.migration_params()[
                                "boot_volume_params"
                            ].items(),
                        )
                    )
                    sdk_params.update(boot_volume_params_defined)
            sdk_params.pop("volume_type", None)
            new_volume = self.conn.create_volume(**sdk_params)
            self.volume_map[path]["dest_id"] = new_volume.id

    @use_lock(ATTACH_LOCK_FILE_DESTINATION)
    def _attach_destination_volumes(self):
        """
        Volume mapping step 6: attach the new destination volumes to the
        destination conversion host. Fill in the destination device name.
        """

        def update_dest(volume_mapping, dev_path):
            volume_mapping["dest_dev"] = dev_path
            return volume_mapping

        def volume_id(volume_mapping):
            return volume_mapping["dest_id"]

        self._attach_volumes(
            self.conn,
            "destination",
            (self._converter, self.shell.cmd_out, update_dest, volume_id),
        )

    def _convert_destination_volumes(self):
        """
        Finally run the commands to copy the exported source volumes to the
        local destination volumes. Attempt to sparsify the volumes to minimize
        the amount of data sent over the network.
        """
        self.log.info("Converting volumes...")
        for path, mapping in self.volume_map.items():
            self.log.info("Converting source VM's %s: %s", path, str(mapping))
            devname = os.path.basename(mapping["dest_dev"])
            overlay = "/tmp/" + devname + "-" + self.transfer_uuid + ".qcow2"

            def _log_convert(source_disk, source_format, mapping):
                """Write qemu-img convert progress to the wrapper log."""
                self.log.info("Copying volume data...")
                cmd = [
                    "sudo",
                    "qemu-img",
                    "convert",
                    "-p",
                    "-f",
                    source_format,
                    "-O",
                    "host_device",
                    source_disk,
                    mapping["dest_dev"],
                ]
                # Non-blocking output processing stolen from pre_copy.py
                img_sub = self.shell.cmd_sub(
                    cmd,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT,
                    stdin=DEVNULL,
                    universal_newlines=True,
                    bufsize=1,
                )
                flags = fcntl.fcntl(img_sub.stdout, fcntl.F_GETFL)
                flags |= os.O_NONBLOCK
                fcntl.fcntl(img_sub.stdout, fcntl.F_SETFL, flags)
                buf = b""
                while img_sub.poll() is None:
                    try:
                        buf += os.read(img_sub.stdout.fileno(), 1)
                    except (IOError, OSError) as err:
                        if err.errno != errno.EAGAIN:
                            raise
                        time.sleep(1)
                        continue
                    if buf:
                        try:
                            matches = self.qemu_progress_re.search(buf.decode())
                            if matches is not None:
                                progress = float(matches.group(1))
                                self._update_progress(path, progress)
                                buf = b""
                        except ValueError:
                            self.log.debug("No match yet. %s", str(buf))
                    else:
                        time.sleep(1)
                self.log.info("Conversion return code: %d", img_sub.returncode)
                if img_sub.returncode != 0:
                    try:
                        out = img_sub.stdout.read()
                    except (IOError, OSError) as err:
                        self.log.debug("Error reading stderr? %s", str(err))
                    raise RuntimeError("Failed to convert volume! " + out)
                # Just in case qemu-img returned before readline got to 100%
                self._update_progress(path, 100.0)

            try:
                self.log.info("Attempting initial sparsify...")
                environment = os.environ.copy()
                environment["LIBGUESTFS_BACKEND"] = "direct"

                cmd = [
                    "sudo",
                    "qemu-img",
                    "create",
                    "-f",
                    "qcow2",
                    "-b",
                    mapping["url"],
                    "-F",
                    "raw",
                    overlay,
                ]
                out = self.shell.cmd_out(cmd)
                self.log.info("Overlay output: %s", out)

                cmd = [
                    "sudo",
                    "--preserve-env=LIBGUESTFS_BACKEND",
                    "virt-sparsify",
                    "--in-place",
                    overlay,
                ]
                with open(self.log_file, "a", encoding="utf8") as log_fd:
                    img_sub = self.shell.cmd_sub(
                        cmd,
                        stdout=log_fd,
                        stderr=subprocess.STDOUT,
                        stdin=DEVNULL,
                        env=environment,
                    )
                    returncode = img_sub.wait()
                    self.log.info("Sparsify return code: %d", returncode)
                    if returncode != 0:
                        raise RuntimeError("Failed to convert volume!")

                _log_convert(overlay, "qcow2", mapping)
            except (OSError, RuntimeError, subprocess.CalledProcessError):
                self.log.info("Sparsify failed, converting whole device...")
                self.shell.cmd_val(["sudo", "rm", "-f", overlay])
                _log_convert(mapping["url"], "raw", mapping)

    @use_lock(ATTACH_LOCK_FILE_DESTINATION)
    def _detach_destination_volumes(self):
        """Disconnect new volumes from destination conversion host."""
        self.log.info("Detaching volumes from destination wrapper.")
        for path, mapping in self.volume_map.items():
            volume_id = mapping["dest_id"]
            volume = self.conn.get_volume_by_id(volume_id)
            self.conn.detach_volume(
                server=self._converter(), timeout=self.timeout, volume=volume, wait=True
            )


class OpenstackVolumeClean(OpenStackVolumeBase):

    def close_exports(self):
        """Put the source VM's volumes back where they were."""
        self._converter_close_exports()
        self._detach_volumes_from_source_converter()
        self._attach_data_volumes_to_source()

    @use_lock(ATTACH_LOCK_FILE_SOURCE)
    def _detach_volumes_from_source_converter(self):
        """Detach volumes from conversion host."""
        self.log.info("Detaching volumes from the source conversion host.")
        converter = self._converter()
        for path, mapping in self.volume_map.items():
            volume = self.conn.get_volume_by_id(mapping["source_id"])
            self.log.info("Inspecting volume %s", volume.id)
            if mapping["source_dev"] is None:
                self.log.info(
                    "Volume is not attached to conversion host, skipping detach."
                )
                continue
            self.conn.detach_volume(
                server=converter, volume=volume, timeout=self.timeout, wait=True
            )
            for second in range(self.timeout):
                converter = self._converter()
                volume = self.conn.get_volume_by_id(mapping["source_id"])
                if not self._volume_still_attached(volume, converter):
                    break
                time.sleep(1)
            else:
                raise RuntimeError(
                    "Timed out waiting to detach volumes from "
                    "source conversion host!"
                )

    def _attach_data_volumes_to_source(self):
        """Clean up the copy of the root volume and reattach data volumes."""
        self.log.info("Re-attaching volumes to source VM...")
        for path, mapping in sorted(self.volume_map.items()):
            if path == "/dev/vda":
                # Delete the temporary copy of the source root disk
                self.log.info("Removing copy of root volume")
                self.conn.delete_volume(
                    name_or_id=mapping["source_id"], wait=True, timeout=self.timeout
                )

                # Remove the root volume snapshot
                if mapping["snap_id"]:
                    self.log.info("Deleting temporary root device snapshot")
                    self.conn.delete_volume_snapshot(
                        timeout=self.timeout, wait=True, name_or_id=mapping["snap_id"]
                    )

                # Remove root image copy, for image-launched instances
                if mapping["image_id"]:
                    self.log.info("Deleting temporary root device image")
                    self.conn.delete_image(
                        timeout=self.timeout, wait=True, name_or_id=mapping["image_id"]
                    )
            else:
                # Attach data volumes back to source VM
                volume = self.conn.get_volume_by_id(mapping["source_id"])
                sourcevm = self._source_vm()
                try:
                    self._get_attachment(volume, sourcevm)
                except RuntimeError:
                    self.log.info("Attaching %s back to source VM", volume.id)
                    self.conn.attach_volume(
                        volume=volume, server=sourcevm, wait=True, timeout=self.timeout
                    )
                else:
                    self.log.info(
                        "Volume %s is already attached to source VM", volume.id
                    )
                    continue
