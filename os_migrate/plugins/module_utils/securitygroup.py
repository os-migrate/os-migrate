from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

import openstack

from ansible_collections.os_migrate.os_migrate.plugins.module_utils \
    import const, reference, resource


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
        obj._sort_param('name')
        obj._sort_info('id')
        return obj

    @staticmethod
    def _create_sdk_res(conn, sdk_params):
        return conn.network.create_security_group(**sdk_params)

    @staticmethod
    def _find_sdk_res(conn, name_or_id):
        return conn.network.find_security_group(name_or_id)

    @staticmethod
    def _refs_from_sdk(conn, sdk_res):
        refs = {}
        refs['security_group_name'] = reference.security_group_name(
            conn, sdk_res['security_group_id'])
        refs['remote_group_name'] = reference.security_group_name(
            conn, sdk_res['remote_group_id'])
        return refs

    def _refs_from_ser(self, conn):
        refs = {}
        refs['security_group_name'] = self.params()['security_group_name']
        refs['security_group_id'] = reference.security_group_id(
            conn, self.params()['security_group_name'])
        return refs

    @staticmethod
    def _update_sdk_res(conn, name_or_id, sdk_params):
        return conn.network.update_security_group(name_or_id, **sdk_params)
