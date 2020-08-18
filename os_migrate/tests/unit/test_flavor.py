from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

import openstack
import unittest

from ansible_collections.os_migrate.os_migrate.plugins.module_utils \
    import const, flavor


def sdk_flavor():
    return openstack.compute.v2.flavor.Flavor(
        description='',
        disk=256,
        ephemeral=1,
        extra_specs={},
        id='uuid-test-flavor',
        is_disabled=False,
        is_public=True,
        name='test-flavor',
        ram=128,
        rxtx_factor=1.5,
        swap=64,
        vcpus=2,
        links=[
            {'rel': 'self',
             'href': 'http://192.168.122.85/compute/v2.1/flavors/d1'},
            {'rel': 'bookmark',
             'href': 'http://192.168.122.85/compute/flavors/d1'}],
    )


def serialized_flavor():
    return {
        const.RES_PARAMS: {
            'description': '',
            'disk': 256,
            'ephemeral': 1,
            'extra_specs': {},
            'is_disabled': False,
            'is_public': True,
            'links': [
                {'rel': 'self',
                 'href': 'http://192.168.122.85/compute/v2.1/flavors/d1'},
                {'rel': 'bookmark',
                 'href': 'http://192.168.122.85/compute/flavors/d1'}
            ],
            'name': 'test-flavor',
            'ram': 128,
            'rxtx_factor': 1.5,
            'swap': 64,
            'vcpus': 2,
        },
        const.RES_INFO: {
            'id': 'uuid-test-flavor',
        },
        const.RES_TYPE: 'openstack.compute.Flavor',
    }


class TestFlavor(unittest.TestCase):

    def test_serialize_flavor(self):
        sdk_net = sdk_flavor()
        flv = flavor.Flavor.from_sdk(None, sdk_net)  # conn=None
        params, info = flv.params_and_info()

        self.assertEqual(flv.type(), const.RES_TYPE_FLAVOR)
        self.assertEqual(params['description'], '')
        self.assertEqual(params['disk'], 256)
        self.assertEqual(params['ephemeral'], 1)
        self.assertEqual(params['extra_specs'], {})
        self.assertEqual(params['is_disabled'], False)
        self.assertEqual(params['is_public'], True)
        self.assertEqual(params['links'], [
            {'rel': 'self',
             'href': 'http://192.168.122.85/compute/v2.1/flavors/d1'},
            {'rel': 'bookmark',
             'href': 'http://192.168.122.85/compute/flavors/d1'}
        ],)
        self.assertEqual(params['name'], 'test-flavor')
        self.assertEqual(params['ram'], 128)
        self.assertEqual(params['rxtx_factor'], 1.5)
        self.assertEqual(params['swap'], 64)
        self.assertEqual(params['vcpus'], 2)

        self.assertEqual(info['id'], 'uuid-test-flavor')

    def test_flavor_sdk_params(self):
        flv = flavor.Flavor.from_data(serialized_flavor())
        sdk_params = flv._to_sdk_params(None)

        self.assertEqual(sdk_params['description'], '')
        self.assertEqual(sdk_params['disk'], 256)
        self.assertEqual(sdk_params['ephemeral'], 1)
        self.assertEqual(sdk_params['extra_specs'], {})
        self.assertEqual(sdk_params['is_disabled'], False)
        self.assertEqual(sdk_params['is_public'], True)
        self.assertEqual(sdk_params['links'], [
            {'rel': 'self',
             'href': 'http://192.168.122.85/compute/v2.1/flavors/d1'},
            {'rel': 'bookmark',
             'href': 'http://192.168.122.85/compute/flavors/d1'}
        ],)
        self.assertEqual(sdk_params['name'], 'test-flavor')
        self.assertEqual(sdk_params['ram'], 128)
        self.assertEqual(sdk_params['rxtx_factor'], 1.5)
        self.assertEqual(sdk_params['swap'], 64)
        self.assertEqual(sdk_params['vcpus'], 2)

        # disallowed params when creating a flavor
        self.assertNotIn('id', sdk_params)
