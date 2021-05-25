from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

import openstack
import unittest

from ansible_collections.os_migrate.os_migrate.plugins.module_utils \
    import const, keypair


def sdk_keypair():
    return openstack.compute.v2.keypair.Keypair(
        created_at='2020-01-06T15:50:55Z',
        id='uuid-test-keypair',
        user_id='uuid-test-user',
        name='test-keypair',
        is_deleted=False,
        fingerprint='TqiTXPRs4cBksWa5pnMTmbEXjgd7bfvuSX7y4sHeMo4',
        public_key='AAAAB3NzaC1yc2EAAAADAQABAAACAQDDnUe1aHYyJFK8vSw9qTgbZCHa==',
        type='ssh'
    )


def serialized_keypair():
    return {
        const.RES_PARAMS: {
            'name': 'test-keypair',
            'is_deleted': False,
            'fingerprint': 'TqiTXPRs4cBksWa5pnMTmbEXjgd7bfvuSX7y4sHeMo4',
            'public_key': 'AAAAB3NzaC1yc2EAAAADAQABAAACAQDDnUe1aHYyJFK8vSw9qTgbZCHa==',
            'type': 'ssh'
        },
        const.RES_INFO: {
            'created_at': '2020-01-06T15:50:55Z',
            'id': 'uuid-test-keypair',
            'user_id': 'uuid-test-user',
        },
        const.RES_TYPE: 'openstack.compute.Keypair',
    }


class TestKeypair(unittest.TestCase):

    def test_serialize_keypair(self):
        sdk_kp = sdk_keypair()
        kp = keypair.Keypair.from_sdk(None, sdk_kp)  # conn=None
        params, info = kp.params_and_info()

        self.assertEqual(kp.type(), 'openstack.compute.Keypair')
        self.assertEqual(params['name'], 'test-keypair')
        self.assertEqual(
            params['public_key'],
            'AAAAB3NzaC1yc2EAAAADAQABAAACAQDDnUe1aHYyJFK8vSw9qTgbZCHa==')
        self.assertEqual(params['type'], 'ssh')

        self.assertEqual(info['created_at'], '2020-01-06T15:50:55Z')
        # creating a new Keypair object sets the id to the name in openstacksdk
        self.assertEqual(info['id'], 'test-keypair')
        self.assertEqual(info['user_id'], 'uuid-test-user')
        self.assertEqual(info['is_deleted'], False)
        self.assertEqual(info['fingerprint'],
                         'TqiTXPRs4cBksWa5pnMTmbEXjgd7bfvuSX7y4sHeMo4')

    def test_keypair_sdk_params(self):
        kp = keypair.Keypair.from_data(serialized_keypair())
        sdk_params = kp._to_sdk_params(None)

        self.assertEqual(sdk_params['name'], 'test-keypair')
        self.assertEqual(sdk_params['type'], 'ssh')
        self.assertEqual(
            sdk_params['public_key'],
            'AAAAB3NzaC1yc2EAAAADAQABAAACAQDDnUe1aHYyJFK8vSw9qTgbZCHa==')

        # disallowed params when creating a keypair
        self.assertNotIn('is_deleted', sdk_params)
        self.assertNotIn('fingerprint', sdk_params)
