from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

import openstack

from ansible import context

from ansible_collections.os_migrate.os_migrate.plugins.module_utils \
    import const, reference, resource


context._init_global_context({})


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

    # This needs to be overriden, because we need to feed special
    # filters to _find_sdk_res. Keypairs are owned by Users, not
    # Projects.
    def create_or_update(self, conn, filters=None):
        refs = self._refs_from_ser(conn)
        sdk_params = self._to_sdk_params(refs)

        user_filters = {}
        if refs['user_id'] is not None:
            user_filters['user_id'] = refs['user_id']

        existing = self._find_sdk_res(conn, sdk_params['name'], user_filters)
        if existing:
            if self._needs_update(self.from_sdk(conn, existing)):
                self._remove_readonly_params(sdk_params)
                sdk_res = self._update_sdk_res(conn, existing, sdk_params)
                self._hook_after_update(conn, sdk_res, False)
                return True
        else:
            sdk_res = self._create_sdk_res(conn, sdk_params)
            self._hook_after_update(conn, sdk_res, True)
            return True
        return False  # no change done

    def import_id(self):
        res_type = self.data.get('type', None)
        res_name = self.data.get('params', {}).get('name', None)
        user_name = self.data.get('params', {}).get('user_ref', {}).get('name', '')
        user_domain = self.data.get('params', {}).get('user_ref', {}).get('domain_name', '')
        if res_type and res_name:
            return f'{res_type}:{res_name}:{user_name}:{user_domain}'
        return None

    @staticmethod
    def _refs_from_sdk(conn, sdk_res):
        refs = {}

        refs['user_id'] = sdk_res['user_id']
        refs['user_ref'] = reference.user_ref(
            conn, sdk_res['user_id'])

        return refs

    def _refs_from_ser(self, conn):
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

    def _is_same_resource(self, target_data):
        # For keys, IDs are typically the same as names, so we cannot
        # rely on IDs being unique. We have to track identity by
        # looking at ID + user_ref tuple.
        ids_match = (self.data[const.RES_INFO].get('id', '__undefined1__') ==
                     target_data[const.RES_INFO].get('id', '__undefined2__'))
        user_refs_match = (self.data[const.RES_PARAMS].get('user_ref', '__undefined1__') ==
                           target_data[const.RES_PARAMS].get('user_ref', '__undefined2__'))
        return ids_match and user_refs_match
