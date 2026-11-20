from __future__ import absolute_import, division, print_function

__metaclass__ = type

import unittest
from unittest import mock

from ansible_collections.os_migrate.os_migrate.plugins.module_utils import os_auth
from ansible_collections.os_migrate.os_migrate.plugins.module_utils.os_auth import (
    openstack_full_argument_spec,
)


class TestOpenstackFullArgumentSpec(unittest.TestCase):

    def test_default_keys(self):
        spec = openstack_full_argument_spec()
        expected_keys = {
            "cloud",
            "auth_type",
            "auth",
            "region_name",
            "validate_certs",
            "ca_cert",
            "client_cert",
            "client_key",
            "wait",
            "timeout",
            "api_timeout",
            "interface",
            "sdk_log_path",
            "sdk_log_level",
        }
        self.assertEqual(set(spec.keys()), expected_keys)

    def test_default_values(self):
        spec = openstack_full_argument_spec()
        self.assertEqual(spec["wait"], {"default": True, "type": "bool"})
        self.assertEqual(spec["timeout"], {"default": 180, "type": "int"})
        self.assertEqual(
            spec["interface"],
            {
                "default": "public",
                "choices": ["public", "internal", "admin"],
                "aliases": ["endpoint_type"],
            },
        )
        self.assertEqual(
            spec["sdk_log_level"],
            {"type": "str", "default": "INFO", "choices": ["INFO", "DEBUG"]},
        )
        self.assertTrue(spec["auth"]["no_log"])
        self.assertTrue(spec["client_key"]["no_log"])
        self.assertEqual(spec["validate_certs"]["aliases"], ["verify"])
        self.assertEqual(spec["ca_cert"]["aliases"], ["cacert"])
        self.assertEqual(spec["client_cert"]["aliases"], ["cert"])
        self.assertEqual(spec["client_key"]["aliases"], ["key"])

    def test_kwargs_merge_adds_custom_params(self):
        spec = openstack_full_argument_spec(
            name=dict(type="str", required=True),
            data=dict(type="dict"),
        )
        self.assertEqual(spec["name"], {"type": "str", "required": True})
        self.assertEqual(spec["data"], {"type": "dict"})
        self.assertIn("cloud", spec)
        self.assertIn("auth", spec)

    def test_kwargs_override_defaults(self):
        spec = openstack_full_argument_spec(
            wait=dict(default=False, type="bool"),
            timeout=dict(default=60, type="int"),
        )
        self.assertEqual(spec["wait"], {"default": False, "type": "bool"})
        self.assertEqual(spec["timeout"], {"default": 60, "type": "int"})


class TestGetConnection(unittest.TestCase):

    def _module(self, **params):
        module = mock.Mock()
        module.params = params
        module.fail_json.side_effect = SystemExit("fail_json")
        return module

    @mock.patch("importlib.import_module", side_effect=ImportError)
    def test_missing_openstacksdk(self, _import_module):
        module = self._module(cloud="devstack")
        with self.assertRaises(SystemExit):
            os_auth.get_connection(module)
        module.fail_json.assert_called_once()
        self.assertIn("openstacksdk", module.fail_json.call_args[1]["msg"])

    @mock.patch("importlib.import_module")
    def test_cloud_dict_conflicts_with_auth_param(self, import_module):
        sdk = mock.Mock()

        class FakeSDKError(Exception):
            pass

        sdk.exceptions.SDKException = FakeSDKError
        import_module.return_value = sdk
        module = self._module(
            cloud={"auth_url": "https://example"},
            auth={"username": "admin"},
        )
        with self.assertRaises(SystemExit):
            os_auth.get_connection(module)
        module.fail_json.assert_called_once()
        self.assertIn("auth", module.fail_json.call_args[1]["msg"])
        sdk.connect.assert_not_called()

    @mock.patch("importlib.import_module")
    def test_cloud_dict_connects(self, import_module):
        sdk = mock.Mock()
        sdk.connect.return_value = "conn"
        import_module.return_value = sdk
        cloud = {"auth_url": "https://example", "project_name": "demo"}
        module = self._module(
            cloud=cloud,
            auth=None,
            region_name=None,
            validate_certs=None,
            ca_cert=None,
            client_cert=None,
            client_key=None,
            api_timeout=None,
            auth_type=None,
        )
        self.assertEqual(os_auth.get_connection(module), "conn")
        sdk.connect.assert_called_once_with(**cloud)

    @mock.patch("importlib.import_module")
    def test_named_cloud_connects_with_params(self, import_module):
        sdk = mock.Mock()
        sdk.connect.return_value = "conn"
        import_module.return_value = sdk
        module = self._module(
            cloud="devstack",
            auth_type="password",
            auth={"username": "admin"},
            region_name="RegionOne",
            validate_certs=True,
            ca_cert="/path/ca.pem",
            client_key="/path/key.pem",
            client_cert="/path/cert.pem",
            api_timeout=30,
            interface="public",
        )
        self.assertEqual(os_auth.get_connection(module), "conn")
        sdk.connect.assert_called_once_with(
            cloud="devstack",
            auth_type="password",
            auth={"username": "admin"},
            region_name="RegionOne",
            verify=True,
            cacert="/path/ca.pem",
            key="/path/key.pem",
            cert="/path/cert.pem",
            api_timeout=30,
            interface="public",
        )

    @mock.patch("importlib.import_module")
    def test_sdk_exception_fails(self, import_module):
        sdk = mock.Mock()

        class FakeSDKError(Exception):
            pass

        sdk.exceptions.SDKException = FakeSDKError
        sdk.connect.side_effect = FakeSDKError("boom")
        import_module.return_value = sdk
        module = self._module(
            cloud="devstack",
            auth_type=None,
            auth=None,
            region_name=None,
            validate_certs=None,
            ca_cert=None,
            client_key=None,
            client_cert=None,
            api_timeout=None,
            interface="public",
        )
        with self.assertRaises(SystemExit):
            os_auth.get_connection(module)
        self.assertIn(
            "OpenStack Connection Error",
            module.fail_json.call_args[1]["msg"],
        )
