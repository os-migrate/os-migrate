from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

import openstack

from ansible_collections.os_migrate.os_migrate.plugins.module_utils \
    import const, reference, resource


class User(resource.Resource):
    resource_type = const.RES_TYPE_USER
    sdk_class = openstack.identity.v3.user.User

    info_from_sdk = [
        'id',
        'domain_id',
        'default_project_id',
    ]

    params_from_sdk = [
        'name',
        'description',
        'email',
        'is_enabled',
    ]

    params_from_refs = [
        'default_project_ref',
        'domain_ref',
    ]

    sdk_params_from_refs = [
        'default_project_id',
        'domain_id',
    ]

    @staticmethod
    def _refs_from_sdk(conn, sdk_res):
        refs = {}

        refs['default_project_ref'] = reference.project_ref(
            conn, sdk_res['default_project_id'])
        refs['default_project_id'] = sdk_res['default_project_id']

        refs['domain_id'] = sdk_res['domain_id']
        refs['domain_ref'] = reference.domain_ref(
            conn, sdk_res['domain_id'])

        return refs

    def _refs_from_ser(self, conn):
        refs = {}

        refs['default_project_ref'] = self.params()['default_project_ref']
        refs['default_project_id'] = reference.project_id(
            conn, self.params()['default_project_ref'])

        refs['domain_ref'] = self.params()['domain_ref']
        refs['domain_id'] = reference.domain_id(
            conn, self.params()['domain_ref'])

        return refs

    @staticmethod
    def _create_sdk_res(conn, sdk_params):
        return conn.identity.create_user(**sdk_params)

    @staticmethod
    def _find_sdk_res(conn, name_or_id, filters=None):
        return conn.identity.find_user(name_or_id, **(filters or {}))

    @staticmethod
    def _update_sdk_res(conn, sdk_res, sdk_params):
        return conn.identity.update_user(sdk_res, **sdk_params)
