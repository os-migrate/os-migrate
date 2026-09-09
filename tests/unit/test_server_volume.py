from __future__ import absolute_import, division, print_function

__metaclass__ = type

import openstack
import unittest

from ansible_collections.os_migrate.os_migrate.plugins.module_utils import server_volume


def sdk_server_volume():
    sdk_params = {
        "availability_zone": "nova",
        "description": "test volume description",
        "is_bootable": False,
        "id": "uuid-test-volume",
        "name": "test-volume",
        "size": 1,
        "volume_type": "tripleo",
        "volume_image_metadata": {"image_id": "uuid-test-image"},
    }
    return openstack.block_storage.v3.volume.Volume(**sdk_params)


# "Disconnected" variant of ServerVolume resource where we make sure not to
# make requests using `conn`.
class ServerVolume(server_volume.ServerVolume):

    # Nothing to override for now
    pass


class TestServerVolume(unittest.TestCase):

    def test_serialize_server_volume(self):
        sv = ServerVolume.from_sdk(None, sdk_server_volume())
        params, info = sv.params_and_info()

        self.assertEqual(sv.type(), "openstack.network.ServerVolume")
        self.assertEqual(params["availability_zone"], "nova")
        self.assertEqual(params["description"], "test volume description")
        self.assertEqual(params["name"], "test-volume")
        self.assertEqual(params["volume_type"], "tripleo")
        self.assertEqual(
            params["volume_image_metadata"],
            {"image_id": "uuid-test-image"},
        )
        self.assertEqual(info["id"], "uuid-test-volume")
        self.assertEqual(info["is_bootable"], False)
        self.assertEqual(info["size"], 1)

    def test_sdk_params(self):
        sv = ServerVolume.from_sdk(None, sdk_server_volume())
        self.assertEqual(
            sv.sdk_params(None),
            {
                "availability_zone": "nova",
                "description": "test volume description",
                "name": "test-volume",
                "volume_type": "tripleo",
                "volume_image_metadata": {"image_id": "uuid-test-image"},
            },
        )

    def test_needs_update(self):
        sv1 = ServerVolume.from_sdk(None, sdk_server_volume())
        sv2 = ServerVolume.from_sdk(None, sdk_server_volume())
        self.assertFalse(sv1._needs_update(sv2))
        sv2.info()["id"] = "other-uuid"
        self.assertFalse(sv1._needs_update(sv2))
        sv2.params()["description"] = "changed description"
        self.assertTrue(sv1._needs_update(sv2))
