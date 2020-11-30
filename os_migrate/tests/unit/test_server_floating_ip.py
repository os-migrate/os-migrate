from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

import openstack
import unittest

from ansible_collections.os_migrate.os_migrate.plugins.module_utils \
    import const, server_floating_ip


def sdk_server_floating_ip():
    return openstack.network.v2.floating_ip.FloatingIP(
        created_at="2020-11-25T15:26:15Z",
        floating_network_id="uuid-test-external-net",
        id="uuid-test-server-fip",
        port_id="uuid-test-server-port",
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
            "router_id": "uuid-test-router",
            "updated_at": "2020-11-25T15:26:18Z",
        },
        const.RES_MIGRATION_PARAMS: {},
        const.RES_PARAMS: {
            "fixed_ip_address": "192.168.20.7",
            "floating_ip_address": "172.20.9.135",
            "tags": [],
        },
        const.RES_TYPE: "openstack.network.ServerFloatingIP",
    }


def server_floating_ip_refs():
    return {}


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

        self.assertEqual(net.type(), 'openstack.network.ServerFloatingIP')
        self.assertEqual(params['fixed_ip_address'], '192.168.20.7')
        self.assertEqual(params['floating_ip_address'], '172.20.9.135')
        self.assertEqual(params['tags'], [])
        self.assertEqual(info['created_at'], '2020-11-25T15:26:15Z')
        self.assertEqual(info['floating_network_id'], 'uuid-test-external-net')
        self.assertEqual(info['id'], 'uuid-test-server-fip')
        self.assertEqual(info['port_id'], 'uuid-test-server-port')
        self.assertEqual(info['router_id'], 'uuid-test-router')
        self.assertEqual(info['updated_at'], '2020-11-25T15:26:18Z')

    def test_server_floating_ip_sdk_params(self):
        net = ServerFloatingIP.from_data(serialized_server_floating_ip())
        refs = net._refs_from_ser(None)  # conn=None
        sdk_params = net._to_sdk_params(refs)

        self.assertEqual(sdk_params['fixed_ip_address'], '192.168.20.7')
        self.assertEqual(sdk_params['tags'], [])
