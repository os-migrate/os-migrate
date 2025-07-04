from __future__ import absolute_import, division, print_function

__metaclass__ = type

import openstack
import unittest
from unittest import mock

from ansible_collections.os_migrate.os_migrate.plugins.module_utils import (
    exc,
    const,
    server_floating_ip,
)


def sdk_server_floating_ip():
    return openstack.network.v2.floating_ip.FloatingIP(
        created_at="2020-11-25T15:26:15Z",
        description="my FIP",
        dns_domain="example.org",
        dns_name="testname",
        floating_network_id="uuid-test-external-net",
        id="uuid-test-server-fip",
        port_id="uuid-test-server-port",
        qos_policy_id="uuid-test-qos-policy",
        router_id="uuid-test-router",
        updated_at="2020-11-25T15:26:18Z",
        fixed_ip_address="192.168.20.7",
        floating_ip_address="172.20.9.135",
        tags=[],
    )


def serialized_server_floating_ip():
    return {
        const.RES_INFO: {
            "created_at": "2020-11-25T15:26:15Z",
            "floating_network_id": "uuid-test-external-net",
            "id": "uuid-test-server-fip",
            "port_id": "uuid-test-server-port",
            "qos_policy_id": "uuid-test-qos-policy",
            "router_id": "uuid-test-router",
            "updated_at": "2020-11-25T15:26:18Z",
            "tags": [],
        },
        const.RES_MIGRATION_PARAMS: {},
        const.RES_PARAMS: {
            "description": "my FIP",
            "dns_domain": "example.org",
            "dns_name": "testname",
            "fixed_ip_address": "192.168.20.7",
            "floating_ip_address": "172.20.9.135",
        },
        const.RES_TYPE: "openstack.network.ServerFloatingIP",
    }


def server_floating_ip_refs():
    return {
        "floating_network_id": "uuid-test-external-net",
        "floating_network_ref": {
            "domain": None,
            "project": None,
            "name": "test-external-net",
        },
        "qos_policy_id": "uuid-test-qos-policy",
        "qos_policy_ref": {
            "domain": None,
            "project": None,
            "name": "test-qos-policy",
        },
    }


# "Disconnected" variant of ServerFloatingIP resource where we make sure not to
# make requests using `conn`.
class ServerFloatingIP(server_floating_ip.ServerFloatingIP):

    def _refs_from_ser(self, conn):
        return server_floating_ip_refs()

    @staticmethod
    def _refs_from_sdk(conn, sdk_res):
        return server_floating_ip_refs()


class TestServerFloatingIP(unittest.TestCase):

    def test_serialize_server_floating_ip(self):
        sdk_net = sdk_server_floating_ip()
        net = ServerFloatingIP.from_sdk(None, sdk_net)  # conn=None
        params, info = net.params_and_info()

        self.assertEqual(net.type(), "openstack.network.ServerFloatingIP")
        self.assertEqual(params["description"], "my FIP")
        self.assertEqual(params["dns_domain"], "example.org")
        self.assertEqual(params["dns_name"], "testname")
        self.assertEqual(params["fixed_ip_address"], "192.168.20.7")
        self.assertEqual(params["floating_ip_address"], "172.20.9.135")
        self.assertEqual(params["floating_network_ref"]["name"], "test-external-net")
        self.assertEqual(params["qos_policy_ref"]["name"], "test-qos-policy")
        self.assertEqual(info["created_at"], "2020-11-25T15:26:15Z")
        self.assertEqual(info["floating_network_id"], "uuid-test-external-net")
        self.assertEqual(info["id"], "uuid-test-server-fip")
        self.assertEqual(info["port_id"], "uuid-test-server-port")
        self.assertEqual(info["router_id"], "uuid-test-router")
        self.assertEqual(info["tags"], [])
        self.assertEqual(info["updated_at"], "2020-11-25T15:26:18Z")

    def test_server_floating_ip_sdk_params(self):
        net = ServerFloatingIP.from_data(serialized_server_floating_ip())
        refs = net._refs_from_ser(None)  # conn=None
        sdk_params = net._to_sdk_params(refs)

        self.assertEqual(
            sdk_params,
            {
                "description": "my FIP",
                "dns_domain": "example.org",
                "dns_name": "testname",
                "fixed_ip_address": "192.168.20.7",
                "floating_network_id": "uuid-test-external-net",
                "qos_policy_id": "uuid-test-qos-policy",
            },
        )

    def test_find_my_server_port(self):
        sdk_srv = {"id": "uuid-test-server"}
        port1 = {
            "fixed_ips": [
                {"ip_address": "192.168.30.3"},
                {"ip_address": "192.168.30.5"},
            ]
        }
        port2 = {
            "fixed_ips": [
                {"ip_address": "192.168.20.6"},
                {"ip_address": "192.168.20.7"},
            ]
        }
        conn = mock.Mock()
        conn.network.ports.return_value = [port1, port2]

        sdk_net = sdk_server_floating_ip()
        fip = ServerFloatingIP.from_sdk(None, sdk_net)  # conn=None

        self.assertEqual(port2, fip._find_my_server_port(conn, sdk_srv))
        conn.network.ports.assert_called_with(device_id="uuid-test-server")

    def test_find_specified_detached_floating_ip(self):
        found_fip = {"port_id": None}
        conn = mock.Mock()
        conn.network.ips.return_value = [found_fip]

        sdk_net = sdk_server_floating_ip()
        fip = ServerFloatingIP.from_sdk(None, sdk_net)  # conn=None

        self.assertEqual(found_fip, fip._find_specified_detached_floating_ip(conn))
        conn.network.ips.assert_called_with(floating_ip_address="172.20.9.135")

    def test_find_specified_detached_floating_ip_not_found(self):
        conn = mock.Mock()
        conn.network.ips.return_value = []

        sdk_net = sdk_server_floating_ip()
        fip = ServerFloatingIP.from_sdk(None, sdk_net)  # conn=None

        self.assertEqual(None, fip._find_specified_detached_floating_ip(conn))
        conn.network.ips.assert_called_with(floating_ip_address="172.20.9.135")

    def test_find_specified_detached_floating_ip_required_but_not_found(self):
        conn = mock.Mock()
        conn.network.ips.return_value = []

        sdk_net = sdk_server_floating_ip()
        fip = ServerFloatingIP.from_sdk(None, sdk_net)  # conn=None

        with self.assertRaises(exc.CannotConverge):
            fip._find_specified_detached_floating_ip(conn, required=True)
        conn.network.ips.assert_called_with(floating_ip_address="172.20.9.135")

    def test_find_specified_detached_floating_ip_attached(self):
        found_fip = {"port_id": "uuid-test-port"}
        conn = mock.Mock()
        conn.network.ips.return_value = [found_fip]

        sdk_net = sdk_server_floating_ip()
        fip = ServerFloatingIP.from_sdk(None, sdk_net)  # conn=None

        with self.assertRaises(exc.CannotConverge):
            fip._find_specified_detached_floating_ip(conn)
        conn.network.ips.assert_called_with(floating_ip_address="172.20.9.135")
