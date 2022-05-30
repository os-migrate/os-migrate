from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

import openstack
import unittest

from ansible_collections.os_migrate.os_migrate.plugins.module_utils \
    import const, user_project_role_assignment


def role_assignment_refs():
    return {
        'project_id': 'uuid-test-project',
        'project_ref': {
            'name': 'test-project',
            'project_name': None,
            'domain_name': 'test-domain',
        },
        'role_id': 'uuid-test-role',
        'role_ref': {
            'name': 'test-role',
            'project_name': None,
            'domain_name': 'test-domain',
        },
        'user_id': 'uuid-test-user',
        'user_ref': {
            'name': 'test-user',
            'project_name': None,
            'domain_name': 'test-domain',
        },
    }


def sdk_role_assignment():
    return openstack.identity.v3.role_assignment.RoleAssignment(
        id='uuid-test-user-project-role-assignment',
        user_id='uuid-test-user',
        role_id='uuid-test-role',
        project_id='uuid-test-project',
    )


def serialized_role_assignment():
    return {
        const.RES_PARAMS: {
            'project_ref': {
                'name': 'test-project',
                'project_name': None,
                'domain_name': 'test-domain',
            },
            'role_ref': {
                'name': 'test-role',
                'project_name': None,
                'domain_name': 'test-domain',
            },
            'user_ref': {
                'name': 'test-user',
                'project_name': None,
                'domain_name': 'test-domain',
            },
        },
        const.RES_INFO: {
            'project_id': 'uuid-test-project',
            'role_id': 'uuid-test-role',
            'user_id': 'uuid-test-user',
            'id': 'uuid-test-user-project-role-assignment'
        },
        const.RES_TYPE: 'openstack.identity.UserProjectRoleAssignment'
    }


class Assignment(user_project_role_assignment.UserProjectRoleAssignment):
    def _refs_from_ser(self, conn):
        return role_assignment_refs()

    @staticmethod
    def _refs_from_sdk(conn, sdk_res):
        return role_assignment_refs()


class RoleAssignment(unittest.TestCase):

    def test_serialize_assignment(self):
        sdk_role = sdk_role_assignment()
        assignment = Assignment.from_sdk(None, sdk_role)
        params, info = assignment.params_and_info()
        self.assertEqual(assignment.type(), 'openstack.identity.UserProjectRoleAssignment')
        self.assertEqual(params['project_ref'], {
            'name': 'test-project',
            'project_name': None,
            'domain_name': 'test-domain',
        })
        self.assertEqual(params['role_ref'], {
            'name': 'test-role',
            'project_name': None,
            'domain_name': 'test-domain',
        })
        self.assertEqual(params['user_ref'], {
            'name': 'test-user',
            'project_name': None,
            'domain_name': 'test-domain',
        })

        self.assertEqual(info['project_id'], 'uuid-test-project')
        self.assertEqual(info['role_id'], 'uuid-test-role')

    def test_assignment_sdk_params(self):
        assignment = Assignment.from_data(serialized_role_assignment())
        refs = assignment._refs_from_ser(None)
        sdk_params = assignment._to_sdk_params(refs)

        self.assertEqual(sdk_params['project_id'], 'uuid-test-project')
        self.assertEqual(sdk_params['role_id'], 'uuid-test-role')
        self.assertEqual(sdk_params['user_id'], 'uuid-test-user')
