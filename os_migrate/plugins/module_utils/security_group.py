from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

import openstack

from ansible_collections.os_migrate.os_migrate.plugins.module_utils \
    import const, resource


class SecurityGroup(resource.Resource):

    resource_type = const.RES_TYPE_SECURITYGROUP
    sdk_class = openstack.network.v2.security_group.SecurityGroup

    info_from_sdk = [
        'id',
        'project_id',
        'created_at',
        'updated_at',
        'revision_number',
    ]
    params_from_sdk = [
        'name',
        'description',
    ]

    @classmethod
    def from_sdk(cls, conn, sdk_resource):
        obj = super(SecurityGroup, cls).from_sdk(conn, sdk_resource)
        return obj

    @staticmethod
    def _create_sdk_res(conn, sdk_params):
        return conn.network.create_security_group(**sdk_params)

    @staticmethod
    def _find_sdk_res(conn, name_or_id, filters=None):
        # return conn.network.find_security_group(name_or_id, **(filters or {}))
        return conn.network.find_security_group(name_or_id)

    @staticmethod
    def _update_sdk_res(conn, name_or_id, sdk_params):
        return conn.network.update_security_group(name_or_id, **sdk_params)
