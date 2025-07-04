from __future__ import absolute_import, division, print_function

__metaclass__ = type

import openstack
import unittest

from ansible_collections.os_migrate.os_migrate.plugins.module_utils import (
    const,
    security_group,
)


def sdk_security_group():
    return openstack.network.v2.security_group.SecurityGroup(
        description="Default security group",
        name="default",
        id="uuid",
        project_id="uuid-project",
        created_at="2020-01-30T14:49:06Z",
        updated_at="2020-01-30T14:49:06Z",
        tenant_id="uuid-tenant",
        revision_number="1",
    )


def serialized_security_group():
    return {
        const.RES_PARAMS: {
            "description": "Default security group",
            "name": "default",
        },
        const.RES_INFO: {
            "id": "uuid",
            "project_id": "uuid-project",
            "created_at": "2020-01-30T14:49:06Z",
            "updated_at": "2020-01-30T14:49:06Z",
            "tenant_id": "uuid-tenant",
            "revision_number": "0",
        },
        const.RES_TYPE: "openstack.network.SecurityGroup",
    }


def security_group_refs():
    return {
        "project_id": "uuid-test-project",
    }


# "Disconnected" variant of SecurityGroup resource where we make sure not to
# make requests using `conn`.
class SecurityGroup(security_group.SecurityGroup):

    def _refs_from_ser(self, conn):
        return security_group_refs()

    @staticmethod
    def _refs_from_sdk(conn, sdk_res):
        return security_group_refs()


class TestSecurityGroup(unittest.TestCase):

    def test_serialize_security_group(self):
        sec = sdk_security_group()
        serialized = SecurityGroup.from_sdk(None, sec)
        params, info = serialized.params_and_info()

        self.assertEqual(serialized.type(), "openstack.network.SecurityGroup")
        self.assertEqual(params["description"], "Default security group")
        self.assertEqual(params["name"], "default")

        self.assertEqual(info["created_at"], "2020-01-30T14:49:06Z")
        self.assertEqual(info["project_id"], "uuid-project")
        self.assertEqual(info["updated_at"], "2020-01-30T14:49:06Z")

    def test_security_group_sdk_params(self):
        ser_sec = SecurityGroup.from_data(serialized_security_group())
        refs = ser_sec._refs_from_ser(None)  # conn=None
        sdk_params = ser_sec._to_sdk_params(refs)

        self.assertEqual(sdk_params["description"], "Default security group")
