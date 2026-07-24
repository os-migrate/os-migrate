from __future__ import absolute_import, division, print_function

__metaclass__ = type

from os import path
import unittest

import yaml

from ansible_collections.os_migrate.os_migrate.plugins.module_utils import const
from ansible_collections.os_migrate.os_migrate.plugins.modules.update_workload_nbdkit_uris import (
    apply_nbdkit_disks,
    update_workload_file,
)
from ansible_collections.os_migrate.os_migrate.tests.unit import utils


def sample_workloads(instance_id="uuid-instance-1", with_migration_params=False):
    resource = {
        "type": "openstack.compute.Server",
        "params": {"name": "migration-vm"},
        "_info": {"id": instance_id},
    }
    if with_migration_params:
        resource["_migration_params"] = {"boot_disk_copy": True}
    return {
        "os_migrate_version": const.OS_MIGRATE_VERSION,
        "resources": [
            resource,
            {
                "type": "openstack.compute.Server",
                "params": {"name": "other-vm"},
                "_info": {"id": "uuid-other"},
            },
        ],
    }


def sample_disks():
    return [
        {
            "device": "/dev/vda",
            "uri": "nbd://hypervisor:10809",
            "port": 10809,
            "size": 10,
            "bootable": True,
        },
        {
            "device": "/dev/vdb",
            "uri": "nbd://hypervisor:10810",
            "port": 10810,
            "size": 20,
            "bootable": False,
        },
    ]


class TestApplyNbdkitDisks(unittest.TestCase):

    def test_updates_matching_instance(self):
        data = sample_workloads()
        disks = sample_disks()
        self.assertTrue(apply_nbdkit_disks(data, "uuid-instance-1", disks))
        self.assertEqual(
            data["resources"][0]["_migration_params"]["nbdkit_disks"],
            disks,
        )
        # other workload untouched
        self.assertNotIn("_migration_params", data["resources"][1])

    def test_creates_migration_params_when_missing(self):
        data = sample_workloads(with_migration_params=False)
        self.assertTrue(apply_nbdkit_disks(data, "uuid-instance-1", sample_disks()))
        self.assertIn("_migration_params", data["resources"][0])
        self.assertIn("nbdkit_disks", data["resources"][0]["_migration_params"])

    def test_preserves_existing_migration_params(self):
        data = sample_workloads(with_migration_params=True)
        self.assertTrue(apply_nbdkit_disks(data, "uuid-instance-1", sample_disks()))
        mig = data["resources"][0]["_migration_params"]
        self.assertTrue(mig["boot_disk_copy"])
        self.assertEqual(mig["nbdkit_disks"], sample_disks())

    def test_instance_not_found(self):
        data = sample_workloads()
        self.assertFalse(apply_nbdkit_disks(data, "missing-id", sample_disks()))
        self.assertNotIn("_migration_params", data["resources"][0])

    def test_empty_resources(self):
        data = {"resources": []}
        self.assertFalse(apply_nbdkit_disks(data, "uuid-instance-1", sample_disks()))

    def test_missing_resources_key(self):
        self.assertFalse(apply_nbdkit_disks({}, "uuid-instance-1", sample_disks()))


class TestUpdateWorkloadFile(unittest.TestCase):

    def test_updates_file_on_disk(self):
        with utils.tmp_dir_context() as tmp_dir:
            file_path = path.join(tmp_dir, "workloads.yml")
            with open(file_path, "w", encoding="utf-8") as f:
                yaml.dump(sample_workloads(), f)

            disks = sample_disks()
            self.assertTrue(
                update_workload_file(file_path, "uuid-instance-1", disks)
            )

            with open(file_path, "r", encoding="utf-8") as f:
                data = yaml.safe_load(f)
            self.assertEqual(
                data["resources"][0]["_migration_params"]["nbdkit_disks"],
                disks,
            )
            self.assertEqual(data["resources"][1]["_info"]["id"], "uuid-other")

    def test_missing_instance_raises(self):
        with utils.tmp_dir_context() as tmp_dir:
            file_path = path.join(tmp_dir, "workloads.yml")
            with open(file_path, "w", encoding="utf-8") as f:
                yaml.dump(sample_workloads(), f)

            with self.assertRaises(ValueError) as ctx:
                update_workload_file(file_path, "missing-id", sample_disks())
            self.assertIn("missing-id", str(ctx.exception))
            self.assertIn(file_path, str(ctx.exception))
