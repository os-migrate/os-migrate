from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

import openstack

from ansible_collections.os_migrate.os_migrate.plugins.module_utils \
    import const, resource


class Project(resource.Resource):
    resource_type = const.RES_TYPE_PROJECT
    sdk_class = openstack.identity.v3.project.Project

    info_from_sdk = [
        'domain_id',
        'parent_id',
    ]

    params_from_sdk = [
        'description',
        'is_domain',
        'is_enabled',
        'name',
    ]

    @staticmethod
    def _create_sdk_res(conn, sdk_params):
        return conn.identity.create_project(**sdk_params)

    @staticmethod
    def _find_sdk_res(conn, name_or_id, filters=None):
        return conn.identity.find_project(name_or_id, **(filters or {}))

    @staticmethod
    def _update_sdk_res(conn, sdk_res, sdk_params):
        return conn.identity.update_project(sdk_res, **sdk_params)
