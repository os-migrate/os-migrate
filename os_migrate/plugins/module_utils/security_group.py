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
    def _clean_all_rules(conn, sdk_res):
        rules = list(conn.network.security_group_rules(security_group_id=sdk_res['id']))
        for rule in rules:
            conn.network.delete_security_group_rule(rule['id'])

    @staticmethod
    def _create_sdk_res(conn, sdk_params):
        return conn.network.create_security_group(**sdk_params)

    @staticmethod
    def _find_sdk_res(conn, name_or_id, filters=None):
        return conn.network.find_security_group(name_or_id, **(filters or {}))

    def _hook_after_update(self, conn, sdk_res, is_create):
        if is_create:
            # Security groups are auto-created with default rules. This is
            # nice when creating them from scratch, but undesirable when
            # migrating. If the user kept the default rules in the source
            # security group, they got exported and will get imported, but
            # we want an empty group to start with.
            self._clean_all_rules(conn, sdk_res)

    @staticmethod
    def _update_sdk_res(conn, sdk_res, sdk_params):
        return conn.network.update_security_group(sdk_res, **sdk_params)
