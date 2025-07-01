from __future__ import absolute_import, division, print_function

__metaclass__ = type

import openstack

from ansible_collections.os_migrate.os_migrate.plugins.module_utils import (
    const,
    reference,
    resource,
)


class UserProjectRoleAssignment(resource.Resource):
    resource_type = const.RES_TYPE_USER_PROJECT_ROLE_ASSIGNMENT
    sdk_class = openstack.identity.v3.role_assignment.RoleAssignment

    info_from_refs = [
        "project_id",
        "role_id",
        "user_id",
    ]

    params_from_refs = [
        "project_ref",
        "role_ref",
        "user_ref",
    ]

    sdk_params_from_refs = [
        "project_id",
        "role_id",
        "user_id",
    ]

    @staticmethod
    def _refs_from_sdk(conn, sdk_res):
        refs = {}

        refs["project_ref"] = reference.project_ref(
            conn, sdk_res["scope"]["project"]["id"]
        )
        refs["project_id"] = sdk_res["scope"]["project"]["id"]

        refs["role_id"] = sdk_res["role"]["id"]
        refs["role_ref"] = reference.role_ref(conn, sdk_res["role"]["id"])

        refs["user_id"] = sdk_res["user"]["id"]
        refs["user_ref"] = reference.user_ref(conn, sdk_res["user"]["id"])

        return refs

    def _refs_from_ser(self, conn):
        refs = {}

        refs["project_ref"] = self.params()["project_ref"]
        refs["project_id"] = reference.project_id(conn, self.params()["project_ref"])

        refs["role_ref"] = self.params()["role_ref"]
        refs["role_id"] = reference.role_id(conn, self.params()["role_ref"])

        refs["user_ref"] = self.params()["user_ref"]
        refs["user_id"] = reference.user_id(conn, self.params()["user_ref"])

        return refs

    def create_or_update(self, conn, filters=None):
        """Create the resource `self` in the target OpenStack cloud connection
        `conn`, or update it if it already exists but needs to be
        updated, or do nothing if it already matches desired
        state. Existing resources to be looked up for idempotence
        purposes will be filtered by `filters`.

        Returns: True if any change was made, False otherwise
        """

        refs = self._refs_from_ser(conn)
        sdk_params = self._to_sdk_params(refs)
        assignments = list(
            conn.identity.role_assignments(
                user_id=sdk_params["user_id"],
                scope_project_id=sdk_params["project_id"],
                role_id=sdk_params["role_id"],
            )
        )

        if len(assignments) == 0:
            conn.identity.assign_project_role_to_user(
                sdk_params["project_id"], sdk_params["user_id"], sdk_params["role_id"]
            )
            return True

        return False

    def _is_same_resource(self, target_data):
        """Check if `target_data` dict is the same resource as self.

        Returns: True if the `target` is the same resource as self.
        """
        # if something else than ['type'] && ['_info']['id'] should be the
        # deciding factors for sameness, just override the following method in
        # the specific subclass
        same_project = self.data[const.RES_INFO].get(
            "project_id", "__undefined1__"
        ) == target_data[const.RES_INFO].get("project_id", "__undefined2__")
        same_role = self.data[const.RES_INFO].get(
            "role_id", "__undefined1__"
        ) == target_data[const.RES_INFO].get("role_id", "__undefined2__")
        same_user = self.data[const.RES_INFO].get(
            "user_id", "__undefined1__"
        ) == target_data[const.RES_INFO].get("user_id", "__undefined2__")

        return same_project and same_role and same_user
