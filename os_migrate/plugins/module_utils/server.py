from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

import openstack

from ansible_collections.os_migrate.os_migrate.plugins.module_utils \
    import const, resource


class Server(resource.Resource):

    resource_type = const.RES_TYPE_SERVER
    sdk_class = openstack.compute.v2.server.Server

    info_from_sdk = [
        'addresses',
        'id',
        'name',
        'status',
    ]

    @staticmethod
    def _find_sdk_res(conn, name_or_id):
        return conn.compute.find_server(name_or_id)
