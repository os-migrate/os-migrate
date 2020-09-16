from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

import openstack
import unittest

from ansible_collections.os_migrate.os_migrate.plugins.module_utils \
    import const, user


def sdk_user():
    return openstack.identity.v3.user.User(
        domain_id=None,
        is_enabled=True,
        name='test-user',
        password='test-user-password',
    )


def serialized_user():
    return {
        const.RES_PARAMS: {
            'name': 'test-user',
            'password': 'test-user-password',
        },
        const.RES_INFO: {
            'domain_id': None,
            'is_enabled': True,
        },
        const.RES_TYPE: 'openstack.user.User',
    }


class TestUser(unittest.TestCase):

    def test_serialize_user(self):
        sdk_usr = sdk_user()
        usr = user.User.from_sdk(None, sdk_usr)  # conn=None
        params, info = usr.params_and_info()

        self.assertEqual(usr.type(), 'openstack.user.User')
        self.assertEqual(params['name'], 'test-user')
        self.assertEqual(params['password'], 'test-user-password')

        self.assertEqual(info['domain_id'], None)
        self.assertEqual(info['is_enabled'], True)

    def test_user_sdk_params(self):
        usr = user.User.from_data(serialized_user())
        sdk_params = usr._to_sdk_params(None)

        self.assertEqual(sdk_params['name'], 'test-user')
        self.assertEqual(sdk_params['password'], 'test-user-password')
