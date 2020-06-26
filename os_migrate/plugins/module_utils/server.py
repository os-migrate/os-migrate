from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

import openstack

from ansible_collections.os_migrate.os_migrate.plugins.module_utils \
    import const, reference, resource


class Server(resource.Resource):

    resource_type = const.RES_TYPE_SERVER
    sdk_class = openstack.compute.v2.server.Server

    info_from_sdk = [
        'id',
        'status',
    ]
    params_from_sdk = [
        'addresses',
        'name',
    ]
    params_from_refs = [
        'flavor_name',
        'security_group_names',
    ]

    @classmethod
    def from_sdk(cls, conn, sdk_resource):
        obj = super(Server, cls).from_sdk(conn, sdk_resource)
        return obj

    @staticmethod
    def _find_sdk_res(conn, name_or_id, filters=None):
        return conn.compute.find_server(name_or_id, **(filters or {}))

    @staticmethod
    def _refs_from_sdk(conn, sdk_res):
        refs = {}
        if 'original_name' in sdk_res['flavor']:
            refs['flavor_name'] = sdk_res['flavor']['original_name']
        elif 'name' in sdk_res['flavor']:
            refs['flavor_name'] = sdk_res['flavor']['name']
        else:
            refs['flavor_name'] = reference.server_flavor_name(
                conn, sdk_res['flavor']['id'])

        refs['security_group_names'] = [security_group['name'] for
                                        security_group in
                                        sdk_res['security_groups']]
        return refs
