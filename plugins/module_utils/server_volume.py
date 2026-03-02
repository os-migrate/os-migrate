from __future__ import absolute_import, division, print_function

__metaclass__ = type

import openstack

from ansible_collections.os_migrate.os_migrate.plugins.module_utils import (
    exc,
    const,
    resource,
)


def server_volumes(conn, sdk_res):
    volumes = []
    for attachment in conn.compute.volume_attachments(sdk_res):
        volumes.append(conn.block_storage.get_volume(attachment["volume_id"]))
    return volumes


class ServerVolume(resource.Resource):

    resource_type = const.RES_TYPE_SERVER_VOLUME
    sdk_class = openstack.block_storage.v3.volume.Volume

    info_from_sdk = [
        "attachments",
        "is_bootable",
        "id",
        # size is set to match the source volume, not editable
        "size",
    ]
    params_from_sdk = [
        "availability_zone",
        "name",
        "description",
        "volume_type",
        'volume_image_metadata',
    ]

    def create_or_update(self, conn, filters=None):
        raise exc.Unsupported(
            "Direct ServerVolume.create_or_update call is unsupported."
        )

    def sdk_params(self, conn):
        """Return creation SDK params which are editable by the user in the
        serialized workloads file. Other SDK params will be provided
        directly by the migration procedure and cannot be changed by
        the user.
        """
        # Presently we have nothing in refs, this is just to follow
        # the conventional approach.
        refs = self._refs_from_ser(conn)
        return self._to_sdk_params(refs)
