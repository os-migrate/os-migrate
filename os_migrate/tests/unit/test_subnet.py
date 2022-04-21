from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

import openstack
import unittest

from ansible_collections.os_migrate.os_migrate.plugins.module_utils \
    import const, subnet


def sdk_subnet():
    return openstack.network.v2.subnet.Subnet(
        id='uuid-test-subnet1',
        name='test-subnet1',
        tenant_id='uuid-tenant',
        network_id='uuid-test-net',
        ip_version=4,
        enable_dhcp=True,
        gateway_ip='10.10.10.1',
        host_routes=[
            {'destination': '0.0.0.0/0', 'nexthop': '12.34.56.78'},
            {'destination': '192.168.10.0/24', 'nexthop': '87.65.43.21'},
        ],
        cidr='10.10.10.0/24',
        allocation_pools=[
            {
                'start': '10.10.10.10',
                'end': '10.10.10.50',
            },
            {
                'start': '10.10.10.80',
                'end': '10.10.10.90',
            }
        ],
        description='test-subnet',
        created_at='2020-02-21T17:34:54Z',
        revision_number=0,
        segment_id='uuid-test-segment',
        subnet_pool_id='uuid-test-subnet-pool',
        dns_nameservers=[],
    )


def serialized_subnet():
    return {
        const.RES_PARAMS: {
            'allocation_pools': [
                {'start': '10.10.10.10', 'end': '10.10.10.50'},
                {'start': '10.10.10.80', 'end': '10.10.10.90'},
            ],
            'cidr': '10.10.10.0/24',
            'description': 'test-subnet',
            'dns_nameservers': None,
            'gateway_ip': '10.10.10.1',
            'host_routes': [
                {'destination': '0.0.0.0/0', 'nexthop': '12.34.56.78'},
            ],
            'ip_version': 4,
            'ipv6_address_mode': None,
            'ipv6_ra_mode': None,
            'is_dhcp_enabled': True,
            'name': 'test-subnet1',
            'network_ref': {
                'name': 'test-net',
                'project_name': 'test-project',
                'domain_name': 'Default',
            },
            'segment_ref': {
                'name': 'test-segment',
                'project_name': 'test-project',
                'domain_name': 'Default',
            },
            'service_types': None,
            'subnet_pool_ref': {
                'name': 'test-subnet-pool',
                'project_name': 'test-project',
                'domain_name': 'Default',
            },
            'tags': [],
            'use_default_subnet_pool': None,
        },
        const.RES_INFO: {
            'created_at': '2020-02-21T17:34:54Z',
            'id': 'uuid-test-subnet1',
            'network_id': 'uuid-test-net',
            'prefix_length': None,
            'project_id': 'uuid-tenant',
            'revision_number': 0,
            'segment_id': 'uuid-test-segment',
            'subnet_pool_id': 'uuid-test-subnet-pool',
            'updated_at': None,
        },
        const.RES_TYPE: 'openstack.subnet.Subnet',
    }


def subnet_refs():
    return {
        'network_id': 'uuid-test-net',
        'network_ref': {
            'name': 'test-net',
            'project_name': 'test-project',
            'domain_name': 'Default',
        },
        'segment_id': 'uuid-test-segment',
        'segment_ref': {
            'name': 'test-segment',
            'project_name': 'test-project',
            'domain_name': 'Default',
        },
        'subnet_pool_id': 'uuid-test-subnet-pool',
        'subnet_pool_ref': {
            'name': 'test-subnet-pool',
            'project_name': 'test-project',
            'domain_name': 'Default',
        },
    }


# "Disconnected" variant of Network resource where we make sure not to
# make requests using `conn`.
class Subnet(subnet.Subnet):

    def _refs_from_ser(self, conn):
        return subnet_refs()

    @staticmethod
    def _refs_from_sdk(conn, sdk_res):
        return subnet_refs()


class TestSubnet(unittest.TestCase):

    def test_serialize_subnet(self):
        subnet_data = sdk_subnet()
        serialized = Subnet.from_sdk(None, subnet_data)
        params, info = serialized.params_and_info()

        self.assertEqual(serialized.type(), 'openstack.subnet.Subnet')
        self.assertEqual(params['allocation_pools'], [
            {'start': '10.10.10.10', 'end': '10.10.10.50'},
            {'start': '10.10.10.80', 'end': '10.10.10.90'},
        ])
        self.assertEqual(params['cidr'], '10.10.10.0/24')
        self.assertEqual(params['description'], 'test-subnet')
        self.assertEqual(params['dns_nameservers'], [])
        self.assertEqual(params['gateway_ip'], '10.10.10.1')
        self.assertEqual(params['host_routes'], [
            {'destination': '0.0.0.0/0', 'nexthop': '12.34.56.78'},
            {'destination': '192.168.10.0/24', 'nexthop': '87.65.43.21'},
        ])
        self.assertEqual(params['ip_version'], 4)
        self.assertEqual(params['ipv6_address_mode'], None)
        self.assertEqual(params['ipv6_ra_mode'], None)
        self.assertEqual(params['is_dhcp_enabled'], True)
        self.assertEqual(params['name'], 'test-subnet1')
        self.assertEqual(params['network_ref']['name'], 'test-net')
        self.assertEqual(params['network_ref']['project_name'], 'test-project')
        self.assertEqual(params['network_ref']['domain_name'], 'Default')
        self.assertEqual(params['segment_ref']['name'], 'test-segment')
        self.assertEqual(params['segment_ref']['project_name'], 'test-project')
        self.assertEqual(params['segment_ref']['domain_name'], 'Default')
        self.assertEqual(params['service_types'], None)
        self.assertEqual(params['subnet_pool_ref']['name'], 'test-subnet-pool')
        self.assertEqual(params['subnet_pool_ref']['project_name'], 'test-project')
        self.assertEqual(params['subnet_pool_ref']['domain_name'], 'Default')
        self.assertEqual(params['tags'], [])
        self.assertEqual(params['use_default_subnet_pool'], None)

        self.assertEqual(info['created_at'], '2020-02-21T17:34:54Z')
        self.assertEqual(info['id'], 'uuid-test-subnet1')
        self.assertEqual(info['network_id'], 'uuid-test-net')
        self.assertEqual(info['prefix_length'], None)
        self.assertEqual(info['project_id'], 'uuid-tenant')
        self.assertEqual(info['revision_number'], 0)
        self.assertEqual(info['segment_id'], 'uuid-test-segment')
        self.assertEqual(info['subnet_pool_id'], 'uuid-test-subnet-pool')
        self.assertEqual(info['updated_at'], None)

    def test_deserialize_subnet(self):
        sub = Subnet.from_data(serialized_subnet())
        refs = sub._refs_from_ser(None)  # conn=None
        sdk_params = sub._to_sdk_params(refs)

        self.assertEqual(sdk_params['allocation_pools'], [
            {'start': '10.10.10.10', 'end': '10.10.10.50'},
            {'start': '10.10.10.80', 'end': '10.10.10.90'},
        ])
        self.assertEqual(sdk_params['cidr'], '10.10.10.0/24')
        self.assertEqual(sdk_params['description'], 'test-subnet')
        self.assertEqual(sdk_params['gateway_ip'], '10.10.10.1')
        self.assertEqual(sdk_params['ip_version'], 4)
        self.assertEqual(sdk_params['is_dhcp_enabled'], True)
        self.assertEqual(sdk_params['name'], 'test-subnet1')
        self.assertEqual(sdk_params['network_id'], 'uuid-test-net')
        self.assertEqual(sdk_params['segment_id'], 'uuid-test-segment')
        self.assertEqual(sdk_params['subnet_pool_id'], 'uuid-test-subnet-pool')
