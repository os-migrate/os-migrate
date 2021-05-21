from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

import openstack
import unittest

from ansible_collections.os_migrate.os_migrate.plugins.module_utils \
    import const, user


def user_refs():
    return {
        'id': 'uuid-test-user',
        'default_project_id': 'uuid-test-project',
        'default_project_ref': {
            'name': 'test-project',
            'project_name': None,
            'domain_name': 'test-domain',
        },
        'domain_id': 'uuid-test-domain',
        'domain_ref': {
            'domain_name': None,
            'name': 'test-domain',
            'project_name': None,
        },
    }


def sdk_user():
    return openstack.identity.v3.user.User(
        id='uuid-test-user',
        domain_id='uuid-test-domain',
        default_project_id='uuid-test-project',
        name='test-user',
        description='test-user-description',
        email='test-user@domain.com',
        is_enabled=True,
    )


def serialized_user():
    return {
        const.RES_PARAMS: {
            'name': 'test-user',
            'description': 'test-user-description',
            'email': 'test-user@domain.com',
            'is_enabled': True,
            'default_project_ref': {
                'name': 'test-project',
                'project_name': None,
                'domain_name': 'test-domain',
            },
            'domain_ref': {
                'domain_name': None,
                'name': 'test-domain',
                'project_name': None,
            },
        },
        const.RES_INFO: {
            'id': 'uuid-test-user',
            'domain_id': 'uuid-test-domain',
            'default_project_id': 'uuid-test-project',
        },
        const.RES_TYPE: 'openstack.user.User',
    }


class User(user.User):

    def _refs_from_ser(self, conn):
        return user_refs()

    @staticmethod
    def _refs_from_sdk(conn, sdk_res):
        return user_refs()


class TestUser(unittest.TestCase):

    def test_serialize_user(self):
        sdk_usr = sdk_user()
        usr = User.from_sdk(None, sdk_usr)
        params, info = usr.params_and_info()

        self.assertEqual(usr.type(), 'openstack.user.User')
        self.assertEqual(params['name'], 'test-user')
        self.assertEqual(params['description'], 'test-user-description')
        self.assertEqual(params['email'], 'test-user@domain.com')
        self.assertEqual(params['is_enabled'], True)
        self.assertEqual(params['domain_ref'], {
            'domain_name': None,
            'name': 'test-domain',
            'project_name': None,
        })
        self.assertEqual(params['default_project_ref'], {
            'domain_name': 'test-domain',
            'name': 'test-project',
            'project_name': None,
        })

        self.assertEqual(info['id'], 'uuid-test-user')
        self.assertEqual(info['domain_id'], 'uuid-test-domain')
        self.assertEqual(info['default_project_id'], 'uuid-test-project')

    def test_user_sdk_params(self):
        usr = User.from_data(serialized_user())
        refs = usr._refs_from_ser(None)
        sdk_params = usr._to_sdk_params(refs)

        self.assertEqual(sdk_params['name'], 'test-user')
        self.assertEqual(sdk_params['description'], 'test-user-description')
        self.assertEqual(sdk_params['email'], 'test-user@domain.com')
        self.assertEqual(sdk_params['is_enabled'], True)
        self.assertEqual(sdk_params['domain_id'], 'uuid-test-domain')
