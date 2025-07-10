from __future__ import absolute_import, division, print_function

__metaclass__ = type

import openstack

from ansible_collections.os_migrate.os_migrate.plugins.module_utils import (
    const,
    reference,
    resource,
)


class Project(resource.Resource):
    resource_type = const.RES_TYPE_PROJECT
    sdk_class = openstack.identity.v3.project.Project

    info_from_sdk = [
        "domain_id",
        "id",
        "parent_id",
    ]
    params_from_sdk = [
        "description",
        "is_domain",
        "is_enabled",
        "name",
    ]
    params_from_refs = [
        "domain_ref",
        "parent_ref",
    ]
    sdk_params_from_refs = [
        "domain_id",
        "parent_id",
    ]

    @staticmethod
    def _create_sdk_res(conn, sdk_params):
        return conn.identity.create_project(**sdk_params)

    @staticmethod
    def _find_sdk_res(conn, name_or_id, filters=None):
        return conn.identity.find_project(name_or_id, **(filters or {}))

    @staticmethod
    def _refs_from_sdk(conn, sdk_res):
        refs = {}

        refs["domain_id"] = sdk_res["domain_id"]
        refs["domain_ref"] = reference.domain_ref(conn, sdk_res["domain_id"])

        refs["parent_id"] = sdk_res["parent_id"]
        # Parent can be either a project, or a domain.
        refs["parent_ref"] = reference.project_ref(
            conn, sdk_res["parent_id"], False
        ) or reference.domain_ref(conn, sdk_res["parent_id"])

        return refs

    def _refs_from_ser(self, conn):
        refs = {}

        refs["domain_ref"] = self.params()["domain_ref"]
        refs["domain_id"] = reference.domain_id(conn, self.params()["domain_ref"])

        refs["parent_ref"] = self.params()["parent_ref"]
        # Parent can be either a project, or a domain.
        refs["parent_id"] = reference.project_id(
            conn, self.params()["parent_ref"], False
        ) or reference.domain_id(conn, self.params()["parent_ref"])

        return refs

    @staticmethod
    def _update_sdk_res(conn, sdk_res, sdk_params):
        return conn.identity.update_project(sdk_res, **sdk_params)
