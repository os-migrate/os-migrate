from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

import unittest
from unittest import mock

from openstack.exceptions import ResourceFailure
from ansible_collections.os_migrate.os_migrate.plugins.module_utils import exc
from ansible_collections.os_migrate.os_migrate.plugins.module_utils \
    import resource


class FakeResource(resource.Resource):

    resource_type = 'some.FakeResource'
    sdk_class = dict

    info_from_sdk = ['id', 'info1', 'info2']
    params_from_sdk = ['name', 'param1', 'readonly_param', 'skip_falsey']
    info_from_refs = ['param3id', 'param4id']
    params_from_refs = ['param3name', 'param4name']
    sdk_params_from_refs = ['param3id', 'param4id']
    readonly_sdk_params = ['readonly_param']
    skip_falsey_sdk_params = ['skip_falsey']
    migration_param_defaults = {
        'migparam1': 'migval1',
    }

    @staticmethod
    def _create_sdk_res(conn, sdk_params):
        return valid_fakeresource_sdk()

    @staticmethod
    def _find_sdk_res(conn, name_or_id, filters=None):
        return valid_fakeresource_sdk()

    def _refs_from_ser(self, conn, filters=None):
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
        'skip_falsey': ['truthy'],
        'param3id': 'param3idval',
        'param4id': 'param4idval',
        'id': 'idval',
        'info1': 'info1val',
        'info2': 'info2val',
    }


def valid_fakeresource_sdk_creation_params():
    return {
        'name': 'nameval',
        'param1': 'param1val',
        'readonly_param': 'no_can_change',
        'skip_falsey': ['truthy'],
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
            'skip_falsey': ['truthy'],
            'param3name': 'param3nameval',
            'param4name': 'param4nameval',
        },
        '_migration_params': {
            'migparam1': 'migval1',
        },
        '_info': {
            'id': 'idval',
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

    def test_to_sdk_params_skip_falsey(self):
        res = FakeResource.from_data(valid_fakeresource_data())
        res.params()['skip_falsey'] = []
        # conn=None because the fake _refs_from_* methods don't need it
        refs = res._refs_from_ser(None)
        sdk_params = res._to_sdk_params(refs)
        expected = valid_fakeresource_sdk_creation_params()
        del expected['skip_falsey']
        self.assertEqual(sdk_params, expected)

    def test_update_migration_params(self):
        res = FakeResource.from_data(valid_fakeresource_data())
        res.update_migration_params({'migparam1': 'val1'})
        res.update_migration_params({'migparam2': 'val2'})
        self.assertEqual(res.migration_params(), {'migparam1': 'val1', 'migparam2': 'val2'})
        res.update_migration_params({'migparam3': None, 'migparam4': 'val4'})
        self.assertEqual(res.migration_params(),
                         {'migparam1': 'val1', 'migparam2': 'val2', 'migparam4': 'val4'})

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
        res._update_sdk_res = mock.Mock(return_value='mock resource')
        res._hook_after_update = mock.Mock()
        self.assertTrue(res.create_or_update(None))
        res._create_sdk_res.assert_not_called()
        res._update_sdk_res.assert_called_once()
        res._hook_after_update.assert_called_once_with(None, 'mock resource', False)

    def test_create_and_update_needs_create(self):
        res = FakeResource.from_data(valid_fakeresource_data())
        # _find_sdk_res returns None - not found
        res._find_sdk_res = mock.Mock(return_value=None)
        res._create_sdk_res = mock.Mock(return_value='mock resource')
        res._update_sdk_res = mock.Mock()
        res._hook_after_update = mock.Mock()
        self.assertTrue(res.create_or_update(None))
        res._create_sdk_res.assert_called_once()
        res._update_sdk_res.assert_not_called()
        res._hook_after_update.assert_called_once_with(None, 'mock resource', True)

    def test_is_same_resource(self):
        r1 = FakeResource.from_data(valid_fakeresource_data())
        r2 = FakeResource.from_data(valid_fakeresource_data())
        self.assertTrue(r1.is_same_resource(r2))

        # test that it can be called with data dict
        r2 = valid_fakeresource_data()
        self.assertTrue(r1.is_same_resource(r2))

        r2['params']['description'] = 'different description'
        self.assertTrue(r1.is_same_resource(r2))

        r2['params']['name'] = 'different-name'
        self.assertTrue(r1.is_same_resource(r2))

        r2['_info']['id'] = 'different-id'
        self.assertFalse(r1.is_same_resource(r2))

        # reset to sameness
        r1 = FakeResource.from_data(valid_fakeresource_data())
        r2 = valid_fakeresource_data()

        r2['type'] = 'different.type'
        self.assertFalse(r1.is_same_resource(r2))

        del r2['type']
        self.assertFalse(r1.is_same_resource(r2))

        # reset to sameness
        r1 = FakeResource.from_data(valid_fakeresource_data())
        r2 = valid_fakeresource_data()

        del r1.info()['id']
        del r2['_info']['id']
        self.assertFalse(r1.is_same_resource(r2))

    def test_data_validation(self):
        res = FakeResource.from_data(valid_fakeresource_data())
        self.assertTrue(res.is_data_valid())
        self.assertEqual(res.data_errors(), [])

        data = valid_fakeresource_data()
        del data['_info']['id']
        res = FakeResource.from_data(data)
        self.assertFalse(res.is_data_valid())
        self.assertEqual(res.data_errors(), ["Missing _info.id."])

        data = valid_fakeresource_data()
        del data['_info']['id']
        del data['params']['param1']
        res = FakeResource.from_data(data)
        self.assertFalse(res.is_data_valid())
        self.assertEqual(res.data_errors(), ["Missing _info.id.", "Missing params.param1."])

        data = valid_fakeresource_data()
        del data['_migration_params']['migparam1']
        res = FakeResource.from_data(data)
        self.assertFalse(res.is_data_valid())
        self.assertEqual(res.data_errors(), ["Missing _migration_params.migparam1."])

    def test_debug_id(self):
        res = FakeResource.from_data(valid_fakeresource_data())
        self.assertEqual(res.debug_id(), "some.FakeResource:nameval:idval")

        # do not crash on missing data
        data = valid_fakeresource_data()
        del data['_info']['id']
        del data['params']['name']
        res = FakeResource.from_data(data)
        self.assertEqual(res.debug_id(), "some.FakeResource::")

    def test_dst_prerequisites_errors(self):
        res = FakeResource.from_data(valid_fakeresource_data())
        self.assertEqual(res.dst_prerequisites_errors(None), [])

        def exception_refs_from_ser(_self, conn, filters=None):
            raise ResourceFailure("Image 'asdf' not found.")
        res._refs_from_ser = exception_refs_from_ser
        self.assertEqual(res.dst_prerequisites_errors(None),
                         ["Destination prerequisites not met: Image 'asdf' not found."])
