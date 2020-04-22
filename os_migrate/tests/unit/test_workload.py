from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

import openstack
import unittest

from ansible_collections.os_migrate.os_migrate.plugins.module_utils \
    import server


def sdk_server():
    return openstack.compute.v2.server.Server(
        addresses={
            'external_network': [
                {'OS-EXT-IPS-MAC:mac_addr': 'fa:16:3e:d7:ae:16',
                 'OS-EXT-IPS:type': 'fixed',
                 'addr': '10.19.2.50',
                 'version': 4},
            ],
        },
        flavor={
            'id': 'a96b2815-3525-4eea-9ab4-14ba58e17835',
        },
        id='uuid-test-server',
        security_groups=[
            dict(name='testing123'),
            dict(name='default'),
        ],
        name='test-server',
        status='ACTIVE',
        flavor_name='m1.small',
        security_group_names=[
            'testing123',
            'default',
        ],
    )


def server_refs():
    return {
        'addresses': {
            'external_network': [
                {'OS-EXT-IPS-MAC:mac_addr': 'fa:16:3e:d7:ae:16',
                 'OS-EXT-IPS:type': 'fixed',
                 'addr': '10.19.2.50',
                 'version': 4},
            ],
        },
        'flavor': {
            'id': 'a96b2815-3525-4eea-9ab4-14ba58e17835',
            'links': {
                'href': 'http://test-server:13774/flavors/a96b2815-3525-4eea-9ab4-14ba58e17835',
                'rel': 'bookmark',
            },
        },
        'id': 'uuid-test-server',
        'name': 'test-server',
        'status': 'ACTIVE',
        'flavor_name': 'm1.small',
        'security_group_names': [
            'testing123',
            'default',
        ],
    }


class Server(server.Server):
    def _refs_from_ser(self, conn):
        return server_refs()

    @staticmethod
    def _refs_from_sdk(conn, sdk_res):
        return server_refs()


class TestServer(unittest.TestCase):
    def test_serialize_server(self):
        srv = Server.from_sdk(None, sdk_server())
        params, info = srv.params_and_info()

        self.assertEqual(srv.type(), 'openstack.compute.Server')
        self.assertEqual(info['addresses'], {
            'external_network': [
                {'OS-EXT-IPS-MAC:mac_addr': 'fa:16:3e:d7:ae:16',
                 'OS-EXT-IPS:type': 'fixed',
                 'addr': '10.19.2.50',
                 'version': 4},
            ],
        })
        self.assertEqual(info['id'], 'uuid-test-server')
        self.assertEqual(params['name'], 'test-server')
        self.assertEqual(info['status'], 'ACTIVE')
        self.assertEqual(info['flavor_id'], 'a96b2815-3525-4eea-9ab4-14ba58e17835')
        self.assertEqual(params['flavor_name'], 'm1.small')
        self.assertEqual(params['security_group_names'], [
            'testing123',
            'default',
        ])
