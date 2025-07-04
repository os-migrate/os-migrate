from __future__ import absolute_import, division, print_function

__metaclass__ = type

import openstack
import unittest

from ansible_collections.os_migrate.os_migrate.plugins.module_utils import (
    const,
    network,
)


def sdk_network():
    return openstack.network.v2.network.Network(
        availability_zone_hints=["nova", "zone2"],
        availability_zones=["nova", "zone3"],
        created_at="2020-01-06T15:50:55Z",
        description="test network",
        dns_domain="example.org",
        id="uuid-test-net",
        ipv4_address_scope_id=None,
        ipv6_address_scope_id=None,
        is_admin_state_up=True,
        is_default=False,
        is_port_security_enabled=True,
        is_router_external=False,
        is_shared=False,
        mtu=1400,
        name="test-net",
        project_id="uuid-test-project",
        provider_network_type="vxlan",
        provider_physical_network="physnet",
        provider_segmentation_id="456",
        qos_policy_id="uuid-test-qos-policy",
        revision_number=3,
        segments=[],
        status="ACTIVE",
        subnet_ids=["uuid-test-subnet1", "uuid-test-subnet2"],
        updated_at="2020-01-06T15:51:00Z",
        is_vlan_transparent=False,
    )


def serialized_network():
    return {
        const.RES_PARAMS: {
            "availability_zone_hints": ["nova", "zone2"],
            "description": "test network",
            "dns_domain": "example.org",
            "is_admin_state_up": True,
            "is_default": False,
            "is_port_security_enabled": True,
            "is_router_external": False,
            "is_shared": False,
            "is_vlan_transparent": False,
            "mtu": 1400,
            "name": "test-net",
            "project_name": "test-project",
            "provider_network_type": "vxlan",
            "provider_physical_network": "physnet",
            "provider_segmentation_id": "456",
            "qos_policy_ref": {
                "name": "test-qos-policy",
                "project_name": "test-project",
                "domain_name": "Default",
            },
            "segments": [],
            "tags": [],
        },
        const.RES_INFO: {
            "availability_zones": ["nova", "zone3"],
            "created_at": "2020-01-06T15:50:55Z",
            "project_id": "uuid-test-project",
            "revision_number": 3,
            "status": "ACTIVE",
            "subnet_ids": ["uuid-test-subnet1", "uuid-test-subnet2"],
            "qos_policy_id": "uuid-test-qos-policy",
            "updated_at": "2020-01-06T15:51:00Z",
        },
        const.RES_TYPE: "openstack.network.Network",
    }


def network_refs():
    return {
        "qos_policy_id": "uuid-test-qos-policy",
        "qos_policy_ref": {
            "name": "test-qos-policy",
            "project_name": "test-project",
            "domain_name": "Default",
        },
    }


# "Disconnected" variant of Network resource where we make sure not to
# make requests using `conn`.
class Network(network.Network):

    def _refs_from_ser(self, conn):
        return network_refs()

    @staticmethod
    def _refs_from_sdk(conn, sdk_res):
        return network_refs()


class TestNetwork(unittest.TestCase):

    def test_serialize_network(self):
        sdk_net = sdk_network()
        net = Network.from_sdk(None, sdk_net)  # conn=None
        params, info = net.params_and_info()

        self.assertEqual(net.type(), "openstack.network.Network")
        self.assertEqual(params["availability_zone_hints"], ["nova", "zone2"])
        self.assertEqual(params["description"], "test network")
        self.assertEqual(params["dns_domain"], "example.org")
        self.assertEqual(params["is_admin_state_up"], True)
        self.assertEqual(params["is_default"], False)
        self.assertEqual(params["is_port_security_enabled"], True)
        self.assertEqual(params["is_router_external"], False)
        self.assertEqual(params["is_shared"], False)
        self.assertEqual(params["is_vlan_transparent"], False)
        self.assertEqual(params["mtu"], 1400)
        self.assertEqual(params["name"], "test-net")
        self.assertEqual(params["provider_network_type"], "vxlan")
        self.assertEqual(params["provider_physical_network"], "physnet")
        self.assertEqual(params["provider_segmentation_id"], "456")
        self.assertEqual(params["qos_policy_ref"]["name"], "test-qos-policy")
        self.assertEqual(params["segments"], [])
        self.assertEqual(params["tags"], [])

        self.assertEqual(info["availability_zones"], ["nova", "zone3"])
        self.assertEqual(info["created_at"], "2020-01-06T15:50:55Z")
        self.assertEqual(info["id"], "uuid-test-net")
        self.assertEqual(info["project_id"], "uuid-test-project")
        self.assertEqual(info["revision_number"], 3)
        self.assertEqual(info["status"], "ACTIVE")
        self.assertEqual(info["subnet_ids"], ["uuid-test-subnet1", "uuid-test-subnet2"])
        self.assertEqual(info["updated_at"], "2020-01-06T15:51:00Z")
        self.assertEqual(info["qos_policy_id"], "uuid-test-qos-policy")

    def test_network_sdk_params(self):
        net = Network.from_data(serialized_network())
        refs = net._refs_from_ser(None)  # conn=None
        sdk_params = net._to_sdk_params(refs)

        self.assertEqual(sdk_params["availability_zone_hints"], ["nova", "zone2"])
        self.assertEqual(sdk_params["description"], "test network")
        self.assertEqual(sdk_params["dns_domain"], "example.org")
        self.assertEqual(sdk_params["is_admin_state_up"], True)
        self.assertEqual(sdk_params["is_default"], False)
        self.assertEqual(sdk_params["is_port_security_enabled"], True)
        self.assertEqual(sdk_params["is_router_external"], False)
        self.assertEqual(sdk_params["is_shared"], False)
        self.assertEqual(sdk_params["is_vlan_transparent"], False)
        self.assertEqual(sdk_params["mtu"], 1400)
        self.assertEqual(sdk_params["name"], "test-net")
        self.assertEqual(sdk_params["provider_network_type"], "vxlan")
        self.assertEqual(sdk_params["provider_physical_network"], "physnet")
        self.assertEqual(sdk_params["provider_segmentation_id"], "456")
        self.assertEqual(sdk_params["qos_policy_id"], "uuid-test-qos-policy")
        self.assertEqual(sdk_params["segments"], [])
        # disallowed params when creating a network
        self.assertNotIn("availability_zones", sdk_params)
        self.assertNotIn("revision_number", sdk_params)

    def test_network_import_when_dns_domain_is_false(self):
        ser = serialized_network()
        ser["params"]["dns_domain"] = ""
        net = Network.from_data(ser)
        refs = net._refs_from_ser(None)
        sdk_params = net._to_sdk_params(refs)

        self.assertNotIn("dns_domain", sdk_params)
