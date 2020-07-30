from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

import openstack

from ansible_collections.os_migrate.os_migrate.plugins.module_utils \
    import const, reference, resource


class Keypair(resource.Resource):
    resource_type = const.RES_TYPE_KEYPAIR
    sdk_class = openstack.compute.v2.keypair.Keypair

    info_from_sdk = [
        'created_at',
        'id',
        'user_id',
    ]

    params_from_sdk = [
        'name',
        'is_deleted',
        'fingerprint',
        'private_key',
        'public_key',
        'type',
    ]

    params_from_refs = [
        'user_ref',
    ]

    sdk_params_from_refs = [
        'user_id',
    ]

    readonly_sdk_params = ['user_id',]


    @staticmethod
    def _create_sdk_res(conn, sdk_params):
        return conn.compute.create_keypair(**sdk_params)

    @staticmethod
    def _find_sdk_res(conn, name_or_id, filters=None):
        return conn.compute.find_keypair(name_or_id, **(filters or {}))

    @staticmethod
    def _update_sdk_res(conn, sdk_res, sdk_params):
        # openstack.compute.v2.keypair.Keypair does not support update
        return

    @staticmethod
    def _refs_from_sdk(conn, sdk_res):
        refs = {}
        refs['user_id'] = sdk_res['user_id']
        refs['user_ref'] = reference.user_ref(
            conn, sdk_res['user_id'])
        return refs

    def _refs_from_ser(self, conn, filters=None):
        refs = {}
        refs['user_ref'] = self.params()['user_ref']
        refs['user_id'] = reference.user_id(
            conn, self.params()['user_ref'])
        return refs
