from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

import openstack
import unittest


from ansible_collections.os_migrate.os_migrate.plugins.module_utils \
    import exc, server_port


def sdk_server_port(**kwargs):
    sdk_params = {
        'allowed_address_pairs': [],
        'binding_host_id': None,
        'binding_profile': None,
        'binding_vif_details': None,
        'binding_vif_type': None,
        'binding_vnic_type': 'normal',
        'created_at': '2020-02-24T17:01:49Z',
        'data_plane_status': None,
        'description': '',
        'device_id': 'uuid-test-server',
        'device_owner': 'compute:avail_zone',
        'dns_assignment': None,
        'dns_domain': None,
        'dns_name': None,
        'extra_dhcp_opts': [],
        'fixed_ips': [
            {
                'subnet_id': 'uuid-test-subnet',
                'ip_address': '192.168.0.11',
            },
        ],
        'is_admin_state_up': True,
        'is_port_security_enabled': True,
        'mac_address': 'fa:16:3e:ab:cd:ef',
        'name': '',
        'network_id': 'uuid-test-net',
        'project_id': 'uuid-test-project',
        'propagate_uplink_status': None,
        'qos_network_policy_id': None,
        'qos_policy_id': None,
        'resource_request': None,
        'revision_number': 6,
        'security_group_ids': ['uuid-test-security-group'],
        'status': 'ACTIVE',
        'trunk_details': None,
        'updated_at': '2020-02-24T17:02:05Z',
        'id': 'uuid-test-server-port',
        'tags': [],
    }
    if kwargs.get('too_many_ips'):
        sdk_params['fixed_ips'].append({
            'subnet_id': 'uuid-test-subnet',
            'ip_address': '192.168.0.12',
        })
    return openstack.network.v2.port.Port(**sdk_params)


def server_port_refs(**kwargs):
    refs = {
        'fixed_ips': [
            {
                'subnet_id': 'uuid-test-subnet',
                'ip_address': '192.168.0.11',
            },
        ],
        'fixed_ips_refs': [
            {
                'subnet_ref': {
                    'name': 'test-subnet',
                    'project_name': 'test-project',
                    'domain_name': 'Default',
                },
                'ip_address': '192.168.0.11',
            },
        ],
        'network_id': 'uuid-test-net',
        'network_ref': {
            'name': 'test-net',
            'project_name': 'test-project',
            'domain_name': 'Default',
        },
    }
    if kwargs.get('too_many_ips'):
        refs['fixed_ips'].append({
            'subnet_id': 'uuid-test-subnet',
            'ip_address': '192.168.0.12',
        })
        refs['fixed_ips_refs'].append({
            'subnet_ref': {
                'name': 'test-subnet',
                'project_name': 'test-project',
                'domain_name': 'Default',
            },
            'ip_address': '192.168.0.12',
        })
    return refs


# "Disconnected" variant of Network resource where we make sure not to
# make requests using `conn`.
class ServerPort(server_port.ServerPort):

    def _refs_from_ser(self, conn):
        too_many_ips = len(self.params()['fixed_ips_refs']) > 1
        return server_port_refs(too_many_ips=too_many_ips)

    @staticmethod
    def _refs_from_sdk(conn, sdk_res):
        too_many_ips = len(sdk_res['fixed_ips']) > 1
        return server_port_refs(too_many_ips=too_many_ips)


class TestServerPort(unittest.TestCase):

    def test_serialize_server_port(self):
        sp = ServerPort.from_sdk(None, sdk_server_port())
        params, info = sp.params_and_info()

        self.assertEqual(sp.type(), 'openstack.network.ServerPort')
        self.assertEqual(params['fixed_ips_refs'], [
            {
                'subnet_ref': {
                    'name': 'test-subnet',
                    'project_name': 'test-project',
                    'domain_name': 'Default',
                },
                'ip_address': '192.168.0.11',
            },
        ])
        self.assertEqual(params['network_ref']['name'], 'test-net')
        self.assertEqual(info['id'], 'uuid-test-server-port')

    def test_nova_sdk_params(self):
        sp = ServerPort.from_sdk(None, sdk_server_port())
        self.assertEqual(
            sp.nova_sdk_params(None),
            {
                'uuid': 'uuid-test-net',
                'fixed_ip': '192.168.0.11',
            },
        )

    def test_nova_sdk_params_too_many_ips(self):
        sp = ServerPort.from_sdk(None, sdk_server_port(too_many_ips=True))
        with self.assertRaises(exc.InconsistentState):
            sp.nova_sdk_params(None)

    def test_ports_sorted_by_nova_order(self):
        sdk_port_stubs = [
            {
                'fixed_ips': [{'ip_address': '192.168.22.11'}],
                'id': 'uuid-test-server-port-2',
            },
            {
                'fixed_ips': [{'ip_address': '192.168.3.11'}],
                'id': 'uuid-test-server-port-3',
            },
            {
                'fixed_ips': [{'ip_address': '192.168.111.11'}],
                'id': 'uuid-test-server-port-1',
            },
        ]
        sdk_server_stub = {
            'addresses': {
                'net-1': [
                    {'OS-EXT-IPS:type': 'fixed',
                     'addr': '192.168.111.11',
                     'version': 4},
                    {'OS-EXT-IPS:type': 'floating',
                     'addr': '10.19.2.50',
                     'version': 4},
                ],
                'net-2': [
                    {'OS-EXT-IPS:type': 'fixed',
                     'addr': '192.168.22.11',
                     'version': 4},
                ],
                'net-3': [
                    {'OS-EXT-IPS:type': 'fixed',
                     'addr': '192.168.3.11',
                     'version': 4},
                    {'OS-EXT-IPS:type': 'floating',
                     'addr': '10.19.2.51',
                     'version': 4},
                ],
            },
        }
        sorted_ports = server_port._ports_sorted_by_nova_order(sdk_server_stub, sdk_port_stubs)
        sorted_ids = list(map(lambda p: p['id'], sorted_ports))
        self.assertEqual(
            sorted_ids,
            ['uuid-test-server-port-1', 'uuid-test-server-port-2', 'uuid-test-server-port-3']
        )
