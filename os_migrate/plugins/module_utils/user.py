from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

import openstack

from ansible_collections.os_migrate.os_migrate.plugins.module_utils \
    import const, resource


class User(resource.Resource):
    resource_type = const.RES_TYPE_USER
    sdk_class = openstack.identity.v3.user.User

    info_from_sdk = [
        'domain_id',
        'is_enabled',
    ]

    params_from_sdk = [
        'name',
        'password',
    ]

    @staticmethod
    def _create_sdk_res(conn, sdk_params):
        return conn.identity.create_user(**sdk_params)

    @staticmethod
    def _find_sdk_res(conn, name_or_id, filters=None):
        return conn.identity.find_user(name_or_id, **(filters or {}))

    @staticmethod
    def _update_sdk_res(conn, sdk_res, sdk_params):
        return conn.identity.update_user(sdk_res, **sdk_params)
