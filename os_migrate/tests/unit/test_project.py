from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

import openstack
import unittest

from ansible_collections.os_migrate.os_migrate.plugins.module_utils \
    import const, project


def sdk_project():
    return openstack.identity.v3.project.Project(
        domain_id=None,
        is_enabled=True,
        parent_id=None,
        description='',
        is_domain=False,
        name='test-project',
    )


def serialized_project():
    return {
        const.RES_PARAMS: {
            'description': '',
            'is_domain': False,
            'is_enabled': True,
            'name': 'test-project',
        },
        const.RES_INFO: {
            'domain_id': None,
            'parent_id': None,
        },
        const.RES_TYPE: 'openstack.identity.Project',
    }


class TestProject(unittest.TestCase):

    def test_serialize_project(self):
        sdk_proj = sdk_project()
        proj = project.Project.from_sdk(None, sdk_proj)  # conn=None
        params, info = proj.params_and_info()

        self.assertEqual(proj.type(), 'openstack.identity.Project')
        self.assertEqual(params['description'], '')
        self.assertEqual(params['is_domain'], False)
        self.assertEqual(params['is_enabled'], True)
        self.assertEqual(params['name'], 'test-project')

        self.assertEqual(info['domain_id'], None)
        self.assertEqual(info['parent_id'], None)

    def test_project_sdk_params(self):
        proj = project.Project.from_data(serialized_project())
        sdk_params = proj._to_sdk_params(None)

        self.assertEqual(sdk_params['description'], '')
        self.assertEqual(sdk_params['is_domain'], False)
        self.assertEqual(sdk_params['is_enabled'], True)
        self.assertEqual(sdk_params['name'], 'test-project')
