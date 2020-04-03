from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

import unittest
from unittest import mock

from ansible_collections.os_migrate.os_migrate.plugins.module_utils import exc
from ansible_collections.os_migrate.os_migrate.plugins.module_utils \
    import resource


class FakeResource(resource.Resource):

    resource_type = 'some.FakeResource'
    sdk_class = dict

    info_from_sdk = ['info1', 'info2']
    params_from_sdk = ['name', 'param1', 'readonly_param']
    info_from_refs = ['param3id', 'param4id']
    params_from_refs = ['param3name', 'param4name']
    sdk_params_from_refs = ['param3id', 'param4id']
    readonly_sdk_params = ['readonly_param']

    @staticmethod
    def _create_sdk_res(conn, sdk_params):
        return valid_fakeresource_sdk()

    @staticmethod
    def _find_sdk_res(conn, name_or_id):
        return valid_fakeresource_sdk()

    def _refs_from_ser(self, conn):
        return {
            'param3name': 'param3nameval',
            'param4name': 'param4nameval',
            'param3id': 'param3idval',
            'param4id': 'param4idval',
        }

    @staticmethod
    def _refs_from_sdk(conn, sdk_res):
        return {
            'param3name': 'param3nameval',
            'param4name': 'param4nameval',
            'param3id': 'param3idval',
            'param4id': 'param4idval',
        }

    @staticmethod
    def _update_sdk_res(conn, name_or_id, sdk_params):
        return valid_fakeresource_sdk()


def valid_fakeresource_sdk():
    return {
        'name': 'nameval',
        'param1': 'param1val',
        'readonly_param': 'no_can_change',
        'param3id': 'param3idval',
        'param4id': 'param4idval',
        'info1': 'info1val',
        'info2': 'info2val',
    }


def valid_fakeresource_sdk_creation_params():
    return {
        'name': 'nameval',
        'param1': 'param1val',
        'readonly_param': 'no_can_change',
        'param3id': 'param3idval',
        'param4id': 'param4idval',
    }


def valid_fakeresource_data():
    return {
        'type': 'some.FakeResource',
        'params': {
            'name': 'nameval',
            'param1': 'param1val',
            'readonly_param': 'no_can_change',
            'param3name': 'param3nameval',
            'param4name': 'param4nameval',
        },
        '_info': {
            'info1': 'info1val',
            'info2': 'info2val',
            'param3id': 'param3idval',
            'param4id': 'param4idval',
        },
    }


class TestResource(unittest.TestCase):

    def test_from_data(self):
        data = valid_fakeresource_data()
        res = FakeResource.from_data(data)
        self.assertEqual(res.data, data)

    def test_from_data_invalid(self):
        data = valid_fakeresource_data()
        data['type'] = 'some.InvalidType'
        with self.assertRaises(exc.UnexpectedResourceType):
            FakeResource.from_data(data)

    def test_from_sdk(self):
        sdk = valid_fakeresource_sdk()
        # conn=None because the fake _refs_from_* methods don't need it
        res = FakeResource.from_sdk(None, sdk)
        self.assertEqual(res.data, valid_fakeresource_data())

    def test_to_sdk_params(self):
        res = FakeResource.from_data(valid_fakeresource_data())
        # conn=None because the fake _refs_from_* methods don't need it
        refs = res._refs_from_ser(None)
        sdk_params = res._to_sdk_params(refs)
        self.assertEqual(sdk_params, valid_fakeresource_sdk_creation_params())

    def test_needs_update(self):
        res1 = FakeResource.from_data(valid_fakeresource_data())
        res2 = FakeResource.from_data(valid_fakeresource_data())
        res2.info()['info1'] = 'changed'
        self.assertFalse(res1._needs_update(res2))
        res2.params()['param1'] = 'changed'
        self.assertTrue(res1._needs_update(res2))

    def test_remove_readonly_param(self):
        res1 = FakeResource.from_data(valid_fakeresource_data())
        res1._remove_readonly_params(res1.params())
        self.assertFalse('readonly_param' in res1.params())

    def test_create_and_update_all_ok(self):
        res = FakeResource.from_data(valid_fakeresource_data())
        # _find_sdk_res returns up-to-date resource
        res._create_sdk_res = mock.Mock()
        res._update_sdk_res = mock.Mock()
        self.assertFalse(res.create_or_update(None))
        res._create_sdk_res.assert_not_called()
        res._update_sdk_res.assert_not_called()

    def test_create_and_update_needs_update(self):
        res = FakeResource.from_data(valid_fakeresource_data())
        stale = valid_fakeresource_sdk()
        stale['param1'] = 'stale'
        # _find_sdk_res returns stale resource
        res._find_sdk_res = mock.Mock(return_value=stale)
        res._create_sdk_res = mock.Mock()
        res._update_sdk_res = mock.Mock()
        self.assertTrue(res.create_or_update(None))
        res._create_sdk_res.assert_not_called()
        res._update_sdk_res.assert_called_once()

    def test_create_and_update_needs_create(self):
        res = FakeResource.from_data(valid_fakeresource_data())
        # _find_sdk_res returns None - not found
        res._find_sdk_res = mock.Mock(return_value=None)
        res._create_sdk_res = mock.Mock()
        res._update_sdk_res = mock.Mock()
        self.assertTrue(res.create_or_update(None))
        res._create_sdk_res.assert_called_once()
        res._update_sdk_res.assert_not_called()
