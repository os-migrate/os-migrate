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
            'original_name': 'm1.small',
        },
        id='uuid-test-server',
        security_groups=[
            dict(name='testing123'),
            dict(name='default'),
        ],
        name='test-server',
        status='ACTIVE',
        security_group_names=[
            'testing123',
            'default',
        ],
    )


def server_refs():
    return {
        'flavor_id': 'uuid-flavor-m1.small',
        'flavor_ref': {
            'name': 'm1.small',
            'project_name': 'test-project',
            'domain_name': 'Default',
        },
        'security_group_ids': [
            'uuid-secgroup-default',
            'uuid-secgroup-testing123',
        ],
        'security_group_refs': [
            {
                'name': 'default',
                'project_name': 'test-project',
                'domain_name': 'Default',
            },
            {
                'name': 'testing123',
                'project_name': 'test-project',
                'domain_name': 'Default',
            },
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
        self.assertEqual(params['addresses'], {
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
        self.assertEqual(params['flavor_ref']['name'], 'm1.small')
        self.assertEqual(params['security_group_refs'][0]['name'], 'default')
        self.assertEqual(params['security_group_refs'][1]['name'], 'testing123')
