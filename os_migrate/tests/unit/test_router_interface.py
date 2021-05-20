from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

import openstack
import unittest

from ansible_collections.os_migrate.os_migrate.plugins.module_utils \
    import router_interface


def sdk_router_interface():
    return openstack.network.v2.port.Port(**{
        'allowed_address_pairs': [],
        'binding_host_id': None,
        'binding_profile': None,
        'binding_vif_details': None,
        'binding_vif_type': None,
        'binding_vnic_type': 'normal',
        'created_at': '2020-02-24T17:01:49Z',
        'data_plane_status': None,
        'description': '',
        'device_id': 'uuid-test-router',
        'device_owner': 'network:router_interface',
        'dns_assignment': None,
        'dns_domain': None,
        'dns_name': None,
        'extra_dhcp_opts': [],
        'fixed_ips': [
            {
                'subnet_id': 'uuid-test-subnet',
                'ip_address': '192.168.0.10',
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
        'id': 'uuid-test-router-interface',
        'tags': [],
    })


def router_interface_refs():
    return {
        'device_id': 'uuid-test-router',
        'device_ref': {
            'name': 'test-router',
            'project_name': 'test-project',
            'domain_name': 'Default',
        },
        'fixed_ips': [
            {
                'subnet_id': 'uuid-test-subnet',
                'ip_address': '192.168.0.10',
            },
        ],
        'fixed_ips_refs': [
            {
                'subnet_ref': {
                    'name': 'test-subnet',
                    'project_name': 'test-project',
                    'domain_name': 'Default',
                },
                'ip_address': '192.168.0.10',
            },
        ],
        'network_id': 'uuid-test-net',
        'network_ref': {
            'name': 'test-net',
            'project_name': 'test-project',
            'domain_name': 'Default',
        },
    }


# "Disconnected" variant of Network resource where we make sure not to
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

        self.assertEqual(rtr.type(), 'openstack.network.RouterInterface')
        self.assertEqual(params['device_ref']['name'], 'test-router')
        self.assertEqual(params['device_owner'], 'network:router_interface')
        self.assertEqual(params['fixed_ips_refs'], [
            {
                'subnet_ref': {
                    'name': 'test-subnet',
                    'project_name': 'test-project',
                    'domain_name': 'Default',
                },
                'ip_address': '192.168.0.10',
            },
        ])
        self.assertEqual(params['network_ref']['name'], 'test-net')

        self.assertEqual(info['id'], 'uuid-test-router-interface')

    def test_serialize_router_interface_distributed(self):
        sdk_rtr = sdk_router_interface()
        sdk_rtr['device_owner'] = 'network:router_interface_distributed'
        rtr = RouterInterface.from_sdk(None, sdk_rtr)
        params, info = rtr.params_and_info()

        self.assertEqual(rtr.type(), 'openstack.network.RouterInterface')
        self.assertEqual(params['device_ref']['name'], 'test-router')
        self.assertEqual(params['device_owner'], 'network:router_interface_distributed')
        self.assertEqual(params['fixed_ips_refs'], [
            {
                'subnet_ref': {
                    'name': 'test-subnet',
                    'project_name': 'test-project',
                    'domain_name': 'Default',
                },
                'ip_address': '192.168.0.10',
            },
        ])
        self.assertEqual(params['network_ref']['name'], 'test-net')

        self.assertEqual(info['id'], 'uuid-test-router-interface')
