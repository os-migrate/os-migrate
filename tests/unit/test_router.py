from __future__ import absolute_import, division, print_function

__metaclass__ = type

import openstack
import unittest

from ansible_collections.os_migrate.os_migrate.plugins.module_utils import (
    const,
    router,
)


def sdk_router():
    return openstack.network.v2.router.Router(
        availability_zone_hints=["nova", "zone2"],
        availability_zones=["nova", "zone3"],
        created_at="2020-02-26T15:50:55Z",
        description="test router",
        external_gateway_info={
            "network_id": "uuid-test-external-net",
            "external_fixed_ips": [
                {"subnet_id": "uuid-test-external-subnet", "ip_address": "172.24.4.79"},
                {
                    "subnet_id": "uuid-test-external-subnet-ipv6",
                    "ip_address": "2001:db8::1",
                },
            ],
            "enable_snat": True,
        },
        flavor_id="uuid-test-network-flavor",
        id="uuid-test-router",
        is_admin_state_up=True,
        is_distributed=True,
        is_ha=True,
        name="test-router",
        project_id="uuid-test-project",
        revision_number=3,
        routes=[
            {"destination": "192.168.50.0/24", "nexthop": "10.0.0.50"},
            {"destination": "192.168.50.0/24", "nexthop": "10.0.0.51"},
        ],
        status="ACTIVE",
        updated_at="2020-02-26T15:51:00Z",
    )


def router_refs():
    return {
        "external_gateway_refinfo": {
            "network_ref": {
                "name": "test-external-net",
                "project_name": "test-project",
                "domain_name": "Default",
            },
            "external_fixed_ips": [
                {
                    "subnet_ref": {
                        "name": "test-external-subnet",
                        "project_name": "test-project",
                        "domain_name": "Default",
                    },
                    "ip_address": "172.24.4.79",
                },
                {
                    "subnet_ref": {
                        "name": "test-external-subnet-ipv6",
                        "project_name": "test-project",
                        "domain_name": "Default",
                    },
                    "ip_address": "2001:db8::1",
                },
            ],
            "enable_snat": True,
        },
        "external_gateway_info": {
            "network_id": "uuid-test-external-net",
            "external_fixed_ips": [
                {"subnet_id": "uuid-test-external-subnet", "ip_address": "172.24.4.79"},
                {
                    "subnet_id": "uuid-test-external-subnet-ipv6",
                    "ip_address": "2001:db8::1",
                },
            ],
            "enable_snat": True,
        },
        "flavor_ref": {
            "name": "test-network-flavor",
            "project_name": "test-project",
            "domain_name": "Default",
        },
        "flavor_id": "uuid-test-network-flavor",
    }


def serialized_router():
    refs = router_refs()
    return {
        const.RES_PARAMS: {
            "availability_zone_hints": ["nova", "zone2"],
            "description": "test router",
            "is_admin_state_up": True,
            "is_distributed": True,
            "is_ha": True,
            "name": "test-router",
            "tags": [],
            "external_gateway_refinfo": refs["external_gateway_refinfo"],
            "flavor_ref": refs["flavor_ref"],
        },
        const.RES_INFO: {
            "availability_zones": ["nova", "zone3"],
            "created_at": "2020-02-26T15:50:55Z",
            "external_gateway_info": refs["external_gateway_info"],
            "flavor_id": "uuid-test-network-flavor",
            "id": "uuid-test-router",
            "project_id": "uuid-test-project",
            "revision_number": 3,
            "routes": [
                {"destination": "192.168.50.0/24", "nexthop": "10.0.0.50"},
                {"destination": "192.168.50.0/24", "nexthop": "10.0.0.51"},
            ],
            "status": "ACTIVE",
            "updated_at": "2020-02-26T15:51:00Z",
        },
        const.RES_TYPE: "openstack.network.Router",
    }


# "Disconnected" variant of Router resource where we make sure not to
# make requests using `conn`.
class Router(router.Router):

    def _refs_from_ser(self, conn):
        return router_refs()

    @staticmethod
    def _refs_from_sdk(conn, sdk_res):
        return router_refs()


class TestRouter(unittest.TestCase):

    def test_serialize_router(self):
        rtr = Router.from_sdk(None, sdk_router())  # conn=None
        params, info = rtr.params_and_info()

        self.assertEqual(rtr.type(), "openstack.network.Router")
        self.assertEqual(params["availability_zone_hints"], ["nova", "zone2"])
        self.assertEqual(params["description"], "test router")
        self.assertEqual(params["is_admin_state_up"], True)
        self.assertEqual(params["is_distributed"], True)
        self.assertEqual(params["is_ha"], True)
        self.assertEqual(params["name"], "test-router")
        self.assertEqual(
            params["external_gateway_refinfo"],
            {
                "network_ref": {
                    "name": "test-external-net",
                    "project_name": "test-project",
                    "domain_name": "Default",
                },
                "external_fixed_ips": [
                    {
                        "subnet_ref": {
                            "name": "test-external-subnet",
                            "project_name": "test-project",
                            "domain_name": "Default",
                        },
                        "ip_address": "172.24.4.79",
                    },
                    {
                        "subnet_ref": {
                            "name": "test-external-subnet-ipv6",
                            "project_name": "test-project",
                            "domain_name": "Default",
                        },
                        "ip_address": "2001:db8::1",
                    },
                ],
                "enable_snat": True,
            },
        )
        self.assertEqual(params["flavor_ref"]["name"], "test-network-flavor")
        self.assertEqual(params["tags"], [])

        self.assertEqual(info["availability_zones"], ["nova", "zone3"])
        self.assertEqual(info["created_at"], "2020-02-26T15:50:55Z")
        self.assertEqual(
            info["external_gateway_info"],
            {
                "network_id": "uuid-test-external-net",
                "external_fixed_ips": [
                    {
                        "subnet_id": "uuid-test-external-subnet",
                        "ip_address": "172.24.4.79",
                    },
                    {
                        "subnet_id": "uuid-test-external-subnet-ipv6",
                        "ip_address": "2001:db8::1",
                    },
                ],
                "enable_snat": True,
            },
        )
        self.assertEqual(info["flavor_id"], "uuid-test-network-flavor")
        self.assertEqual(info["project_id"], "uuid-test-project")
        self.assertEqual(info["revision_number"], 3)
        self.assertEqual(
            info["routes"],
            [
                {"destination": "192.168.50.0/24", "nexthop": "10.0.0.50"},
                {"destination": "192.168.50.0/24", "nexthop": "10.0.0.51"},
            ],
        )
        self.assertEqual(info["status"], "ACTIVE")
        self.assertEqual(info["updated_at"], "2020-02-26T15:51:00Z")

    def test_router_sdk_params(self):
        rtr = Router.from_data(serialized_router())
        sdk_params = rtr._to_sdk_params(rtr._refs_from_ser(None))

        self.assertEqual(sdk_params["name"], "test-router")
        self.assertEqual(sdk_params["description"], "test router")
        self.assertEqual(sdk_params["is_admin_state_up"], True)
        self.assertEqual(sdk_params["is_distributed"], True)
        self.assertEqual(sdk_params["is_ha"], True)
        self.assertEqual(sdk_params["availability_zone_hints"], ["nova", "zone2"])
        self.assertEqual(sdk_params["flavor_id"], "uuid-test-network-flavor")
        self.assertEqual(
            sdk_params["external_gateway_info"],
            router_refs()["external_gateway_info"],
        )
        # tags are applied via hook, not create/update kwargs
        self.assertNotIn("tags", sdk_params)
        # info-only fields must not be sent to the API
        self.assertNotIn("status", sdk_params)
        self.assertNotIn("revision_number", sdk_params)
        self.assertNotIn("routes", sdk_params)

    def test_router_skip_falsey_availability_zone_hints(self):
        data = serialized_router()
        data[const.RES_PARAMS]["availability_zone_hints"] = []
        rtr = Router.from_data(data)
        sdk_params = rtr._to_sdk_params(rtr._refs_from_ser(None))
        self.assertNotIn("availability_zone_hints", sdk_params)

    def test_needs_update(self):
        rtr1 = Router.from_data(serialized_router())
        rtr2 = Router.from_data(serialized_router())
        rtr2.info()["status"] = "DOWN"
        self.assertFalse(rtr1._needs_update(rtr2))
        rtr2.params()["description"] = "changed"
        self.assertTrue(rtr1._needs_update(rtr2))
