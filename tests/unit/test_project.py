from __future__ import absolute_import, division, print_function

__metaclass__ = type

import openstack
import unittest

from ansible_collections.os_migrate.os_migrate.plugins.module_utils import (
    const,
    project,
)


def sdk_project():
    return openstack.identity.v3.project.Project(
        domain_id="uuid-test-domain",
        is_enabled=True,
        parent_id="uuid-test-parent-project",
        description="",
        is_domain=False,
        name="test-project",
    )


def serialized_project():
    return {
        const.RES_PARAMS: {
            "description": "",
            "domain_ref": {
                "domain_name": None,
                "name": "test-domain",
                "project_name": None,
            },
            "is_domain": False,
            "is_enabled": True,
            "name": "test-project",
            "parent_ref": {
                "domain_name": "test-domain",
                "name": "test-parent-project",
                "project_name": None,
            },
        },
        const.RES_INFO: {
            "domain_id": "uuid-test-domain",
            "parent_id": "uuid-test-parent-project",
        },
        const.RES_TYPE: "openstack.identity.Project",
    }


def project_refs():
    return {
        "domain_id": "uuid-test-domain",
        "domain_ref": {
            "domain_name": None,
            "name": "test-domain",
            "project_name": None,
        },
        "project_id": "uuid-test-parent-project",
        "parent_ref": {
            "domain_name": "test-domain",
            "name": "test-parent-project",
            "project_name": None,
        },
    }


# "Disconnected" variant of Project resource where we make sure not to
# make requests using `conn`.
class Project(project.Project):

    def _refs_from_ser(self, conn):
        return project_refs()

    @staticmethod
    def _refs_from_sdk(conn, sdk_res):
        return project_refs()


class TestProject(unittest.TestCase):

    def test_serialize_project(self):
        sdk_proj = sdk_project()
        proj = Project.from_sdk(None, sdk_proj)  # conn=None
        params, info = proj.params_and_info()

        self.assertEqual(proj.type(), "openstack.identity.Project")
        self.assertEqual(params["description"], "")
        self.assertEqual(params["is_domain"], False)
        self.assertEqual(params["is_enabled"], True)
        self.assertEqual(params["name"], "test-project")
        self.assertEqual(
            params["domain_ref"],
            {
                "domain_name": None,
                "name": "test-domain",
                "project_name": None,
            },
        )
        self.assertEqual(
            params["parent_ref"],
            {
                "domain_name": "test-domain",
                "name": "test-parent-project",
                "project_name": None,
            },
        )

        self.assertEqual(info["domain_id"], "uuid-test-domain")
        self.assertEqual(info["parent_id"], "uuid-test-parent-project")

    def test_project_sdk_params(self):
        proj = Project.from_data(serialized_project())
        sdk_params = proj._to_sdk_params(proj._refs_from_ser(None))

        self.assertEqual(sdk_params["description"], "")
        self.assertEqual(sdk_params["is_domain"], False)
        self.assertEqual(sdk_params["is_enabled"], True)
        self.assertEqual(sdk_params["name"], "test-project")
