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
    info_from_refs = [
        'flavor_id',
        'security_group_ids',
    ]
    params_from_sdk = [
        'addresses',
        'name',
    ]
    params_from_refs = [
        'flavor_ref',
        'security_group_refs',
    ]
    sdk_params_from_refs = [
        'flavor_id',
        'security_group_ids',
    ]

    @classmethod
    def from_sdk(cls, conn, sdk_resource):
        obj = super(Server, cls).from_sdk(conn, sdk_resource)
        return obj

    def sdk_params(self, conn):
        refs = self._refs_from_ser(conn)
        return self._to_sdk_params(refs)

    @staticmethod
    def _find_sdk_res(conn, name_or_id, filters=None):
        return conn.compute.find_server(name_or_id, **(filters or {}))

    @staticmethod
    def _refs_from_sdk(conn, sdk_res):
        refs = {}

        # There are multiple representations of server in SDK, some of
        # them don't have flavor ID info.
        flavor_id = sdk_res['flavor'].get('id')
        if flavor_id is None:
            flavor_id = conn.get_server_by_id(sdk_res['id'])['flavor']['id']

        refs['flavor_id'] = flavor_id
        refs['flavor_ref'] = reference.flavor_ref(
            conn, flavor_id)

        sec_groups = list(conn.compute.fetch_server_security_groups(sdk_res)
                          .security_groups)
        refs['security_group_ids'] = [
            sec_group['id']
            for sec_group in sec_groups]
        refs['security_group_refs'] = [
            reference.security_group_ref(conn, sec_group['id'])
            for sec_group in sec_groups]
        return refs

    def _refs_from_ser(self, conn, filters=None):
        refs = {}
        refs['flavor_id'] = reference.flavor_id(
            conn, self.params()['flavor_ref'])
        refs['flavor_ref'] = self.params()['flavor_ref']

        refs['security_group_refs'] = self.params()['security_group_refs']
        refs['security_group_ids'] = [
            reference.security_group_id(conn, sec_group_ref)
            for sec_group_ref in self.params()['security_group_refs']]

        return refs
