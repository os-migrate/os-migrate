from __future__ import absolute_import, division, print_function

__metaclass__ = type

import openstack
import unittest

from ansible_collections.os_migrate.os_migrate.plugins.module_utils import (
    const,
    exc,
    router_interface,
)


def sdk_router_interface():
    return openstack.network.v2.port.Port(
        **{
            "allowed_address_pairs": [],
            "binding_host_id": None,
            "binding_profile": None,
            "binding_vif_details": None,
            "binding_vif_type": None,
            "binding_vnic_type": "normal",
            "created_at": "2020-02-24T17:01:49Z",
            "data_plane_status": None,
            "description": "",
            "device_id": "uuid-test-router",
            "device_owner": "network:router_interface",
            "dns_assignment": None,
            "dns_domain": None,
            "dns_name": None,
            "extra_dhcp_opts": [],
            "fixed_ips": [
                {
                    "subnet_id": "uuid-test-subnet",
                    "ip_address": "192.168.0.10",
                },
            ],
            "is_admin_state_up": True,
            "is_port_security_enabled": True,
            "mac_address": "fa:16:3e:ab:cd:ef",
            "name": "",
            "network_id": "uuid-test-net",
            "project_id": "uuid-test-project",
            "propagate_uplink_status": None,
            "qos_network_policy_id": None,
            "qos_policy_id": None,
            "resource_request": None,
            "revision_number": 6,
            "security_group_ids": ["uuid-test-security-group"],
            "status": "ACTIVE",
            "trunk_details": None,
            "updated_at": "2020-02-24T17:02:05Z",
            "id": "uuid-test-router-interface",
            "tags": [],
        }
    )


def router_interface_refs():
    return {
        "device_id": "uuid-test-router",
        "device_ref": {
            "name": "test-router",
            "project_name": "test-project",
            "domain_name": "Default",
        },
        "fixed_ips": [
            {
                "subnet_id": "uuid-test-subnet",
                "ip_address": "192.168.0.10",
            },
        ],
        "fixed_ips_refs": [
            {
                "subnet_ref": {
                    "name": "test-subnet",
                    "project_name": "test-project",
                    "domain_name": "Default",
                },
                "ip_address": "192.168.0.10",
            },
        ],
        "network_id": "uuid-test-net",
        "network_ref": {
            "name": "test-net",
            "project_name": "test-project",
            "domain_name": "Default",
        },
    }


# "Disconnected" variant of RouterInterface resource where we make sure not to
# make requests using `conn`.
class RouterInterface(router_interface.RouterInterface):

    def _refs_from_ser(self, conn):
        return router_interface_refs()

    @staticmethod
    def _refs_from_sdk(conn, sdk_res):
        return router_interface_refs()


class TestRouterInterface(unittest.TestCase):

    def test_serialize_router_interface(self):
        rtr = RouterInterface.from_sdk(None, sdk_router_interface())
        params, info = rtr.params_and_info()

        self.assertEqual(rtr.type(), "openstack.network.RouterInterface")
        self.assertEqual(params["device_ref"]["name"], "test-router")
        self.assertEqual(params["device_owner"], "network:router_interface")
        self.assertEqual(
            params["fixed_ips_refs"],
            [
                {
                    "subnet_ref": {
                        "name": "test-subnet",
                        "project_name": "test-project",
                        "domain_name": "Default",
                    },
                    "ip_address": "192.168.0.10",
                },
            ],
        )
        self.assertEqual(params["network_ref"]["name"], "test-net")

        self.assertEqual(info["id"], "uuid-test-router-interface")

    def test_serialize_router_interface_distributed(self):
        sdk_rtr = sdk_router_interface()
        sdk_rtr["device_owner"] = "network:router_interface_distributed"
        rtr = RouterInterface.from_sdk(None, sdk_rtr)
        params, info = rtr.params_and_info()

        self.assertEqual(rtr.type(), "openstack.network.RouterInterface")
        self.assertEqual(params["device_ref"]["name"], "test-router")
        self.assertEqual(params["device_owner"], "network:router_interface_distributed")
        self.assertEqual(
            params["fixed_ips_refs"],
            [
                {
                    "subnet_ref": {
                        "name": "test-subnet",
                        "project_name": "test-project",
                        "domain_name": "Default",
                    },
                    "ip_address": "192.168.0.10",
                },
            ],
        )
        self.assertEqual(params["network_ref"]["name"], "test-net")

        self.assertEqual(info["id"], "uuid-test-router-interface")

    def test_unexpected_device_owner(self):
        sdk_rtr = sdk_router_interface()
        sdk_rtr["device_owner"] = "compute:nova"
        with self.assertRaises(exc.UnexpectedChoice):
            RouterInterface.from_sdk(None, sdk_rtr)

    def test_router_interface_sdk_params(self):
        data = {
            const.RES_TYPE: "openstack.network.RouterInterface",
            const.RES_PARAMS: {
                "device_owner": "network:router_interface",
                "device_ref": router_interface_refs()["device_ref"],
                "fixed_ips_refs": router_interface_refs()["fixed_ips_refs"],
                "network_ref": router_interface_refs()["network_ref"],
            },
            const.RES_INFO: {
                "id": "uuid-test-router-interface",
            },
        }
        rtr = RouterInterface.from_data(data)
        sdk_params = rtr._to_sdk_params(rtr._refs_from_ser(None))
        self.assertEqual(sdk_params["network_id"], "uuid-test-net")
        self.assertEqual(
            sdk_params["fixed_ips"],
            [
                {
                    "subnet_id": "uuid-test-subnet",
                    "ip_address": "192.168.0.10",
                },
            ],
        )
        self.assertNotIn("device_owner", sdk_params)
        self.assertNotIn("device_ref", sdk_params)

    def test_needs_update(self):
        data = {
            const.RES_TYPE: "openstack.network.RouterInterface",
            const.RES_PARAMS: {
                "device_owner": "network:router_interface",
                "device_ref": router_interface_refs()["device_ref"],
                "fixed_ips_refs": router_interface_refs()["fixed_ips_refs"],
                "network_ref": router_interface_refs()["network_ref"],
            },
            const.RES_INFO: {"id": "uuid-test-router-interface"},
        }
        r1 = RouterInterface.from_data(data)
        r2 = RouterInterface.from_data(
            {
                const.RES_TYPE: "openstack.network.RouterInterface",
                const.RES_PARAMS: {
                    "device_owner": "network:router_interface",
                    "device_ref": router_interface_refs()["device_ref"],
                    "fixed_ips_refs": router_interface_refs()["fixed_ips_refs"],
                    "network_ref": router_interface_refs()["network_ref"],
                },
                const.RES_INFO: {"id": "uuid-test-router-interface"},
            }
        )
        r2.info()["id"] = "other-id"
        self.assertFalse(r1._needs_update(r2))
        r2.params()["device_owner"] = "network:router_interface_distributed"
        self.assertTrue(r1._needs_update(r2))
