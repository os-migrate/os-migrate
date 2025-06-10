from __future__ import absolute_import, division, print_function

__metaclass__ = type

import openstack
import unittest

from ansible_collections.os_migrate.os_migrate.plugins.module_utils import (
    const,
    security_group_rule,
)


def security_group_rule_refs():
    return {
        "security_group_id": "uuid-test-default-secgroup",
        "security_group_ref": {
            "name": "test-default-secgroup",
            "project_name": "test-project",
            "domain_name": "Default",
        },
        "remote_group_id": "uuid-test-remote-secgroup",
        "remote_group_ref": {
            "name": "test-remote-secgroup",
            "project_name": "test-project",
            "domain_name": "Default",
        },
    }


def sdk_security_group_rule():
    return openstack.network.v2.security_group_rule.SecurityGroupRule(
        id="uuid",
        security_group_id="uuid-sec-group",
        security_group_name="default",
        remote_group_id="uuid-group",
        remote_group_name="default",
        project_id="uuid-project",
        created_at="2020-01-30T14:49:06Z",
        updated_at="2020-01-30T14:49:06Z",
        revision_number="0",
        description="null",
        direction="ingress",
        ether_type="IPv4",
        port_range_max="100",
        port_range_min="10",
        protocol="null",
        remote_ip_prefix="null",
    )


def serialized_security_group_rule():
    return {
        const.RES_PARAMS: {
            "description": "null",
            "direction": "ingress",
            "ether_type": "IPv4",
            "port_range_max": "100",
            "port_range_min": "10",
            "protocol": "null",
            "remote_group_ref": {
                "name": "test-remote-secgroup",
                "project_name": "test-project",
                "domain_name": "Default",
            },
            "remote_ip_prefix": "null",
            "security_group_ref": {
                "name": "test-default-secgroup",
                "project_name": "test-project",
                "domain_name": "Default",
            },
        },
        const.RES_INFO: {
            "id": "uuid",
            "project_id": "uuid-project",
            "created_at": "2020-01-30T14:49:06Z",
            "updated_at": "2020-01-30T14:49:06Z",
            "remote_group_id": "uuid-test-remote-secgroup",
            "revision_number": "0",
            "security_group_id": "uuid-test-default-secgroup",
        },
        const.RES_TYPE: "openstack.network.SecurityGroupRule",
    }


# "Disconnected" variant of SecurityGroupRule resource where we make sure not to
# make requests using `conn`.
class SecurityGroupRule(security_group_rule.SecurityGroupRule):

    def _refs_from_ser(self, conn):
        return security_group_rule_refs()

    @staticmethod
    def _refs_from_sdk(conn, sdk_res):
        return security_group_rule_refs()


class TestSecurityGroupRule(unittest.TestCase):

    def test_serialize_security_group_rule(self):
        sec = sdk_security_group_rule()
        serialized = SecurityGroupRule.from_sdk(None, sec)
        params, info = serialized.params_and_info()

        self.assertEqual(serialized.type(), "openstack.network.SecurityGroupRule")
        self.assertEqual(params["security_group_ref"]["name"], "test-default-secgroup")
        self.assertEqual(params["remote_group_ref"]["name"], "test-remote-secgroup")
        self.assertEqual(params["description"], "null")
        self.assertEqual(params["direction"], "ingress")
        self.assertEqual(params["ether_type"], "IPv4")
        self.assertEqual(params["port_range_max"], 100)
        self.assertEqual(params["port_range_min"], 10)
        self.assertEqual(params["protocol"], "null")
        self.assertEqual(params["remote_ip_prefix"], "null")

        self.assertEqual(info["created_at"], "2020-01-30T14:49:06Z")
        self.assertEqual(info["id"], "uuid")
        self.assertEqual(info["project_id"], "uuid-project")
        self.assertEqual(info["remote_group_id"], "uuid-group")
        self.assertEqual(info["security_group_id"], "uuid-sec-group")
        self.assertEqual(info["updated_at"], "2020-01-30T14:49:06Z")
        self.assertEqual(info["revision_number"], 0)

    def test_security_group_rule_sdk_params(self):
        ser_secrule = SecurityGroupRule.from_data(serialized_security_group_rule())
        refs = ser_secrule._refs_from_ser(None)  # conn=None

        sdk_params = ser_secrule._to_sdk_params(refs)

        self.assertEqual(sdk_params["description"], "null")
        self.assertEqual(sdk_params["direction"], "ingress")
        self.assertEqual(sdk_params["ether_type"], "IPv4")
        self.assertEqual(sdk_params["port_range_max"], "100")
        self.assertEqual(sdk_params["port_range_min"], "10")
        self.assertEqual(sdk_params["protocol"], "null")
        self.assertEqual(sdk_params["remote_ip_prefix"], "null")
