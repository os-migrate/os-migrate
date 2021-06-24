from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

import openstack

from ansible_collections.os_migrate.os_migrate.plugins.module_utils \
    import const, reference, resource


class Keypair(resource.Resource):
    # according to https://github.com/openstack/openstacksdk/blob/a4a2a7b42ec2ae7e186b44aeb7242fddd84944f7/openstack/cloud/_compute.py#L601
    # keypairs are created with name and public key.  user is not used.
    resource_type = const.RES_TYPE_KEYPAIR
    sdk_class = openstack.compute.v2.keypair.Keypair

    info_from_sdk = [
        'created_at',
        'id',
        'user_id',
        'fingerprint',
        'is_deleted',
    ]

    params_from_sdk = [
        'name',
        'public_key',
        'type',
    ]

    params_from_refs = [
        'user_ref',
    ]

    sdk_params_from_refs = [
        'user_id',
    ]

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
            conn, self.params()['user_ref'], none_if_auth=True)

        return refs

    @staticmethod
    def _create_sdk_res(conn, sdk_params):
        try:
            return conn.compute.create_keypair(**sdk_params)
        except openstack.exceptions.BadRequestException:
            sdk_params_no_type = {k: v for k, v in sdk_params.items() if k != 'type'}
            return conn.compute.create_keypair(**sdk_params_no_type)

    @staticmethod
    def _find_sdk_res(conn, name_or_id, filters=None):
        return conn.compute.find_keypair(name_or_id, **(filters or {}))

    @staticmethod
    def _update_sdk_res(conn, sdk_res, sdk_params):
        # openstack.compute.v2.keypair.Keypair does not support update
        return sdk_res
