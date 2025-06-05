from __future__ import absolute_import, division, print_function

__metaclass__ = type

import unittest
from unittest import mock

from ansible_collections.os_migrate.os_migrate.plugins.module_utils import reference


class TestReference(unittest.TestCase):

    def test_user_id_with_auth(self):
        ref = {
            "project_name": None,
            "name": "%auth%",
            "domain_name": "%auth%",
        }
        conn = mock.Mock()
        conn.current_user_id = "current_user_id"
        self.assertEqual(reference.user_id(conn, ref), "current_user_id")
        self.assertEqual(reference.user_id(conn, ref, none_if_auth=True), None)

    def test_user_ref_with_auth(self):
        expected_ref = {
            "project_name": None,
            "name": "%auth%",
            "domain_name": "%auth%",
        }
        conn = mock.Mock()
        conn.current_user_id = "current_user_id"
        self.assertEqual(reference.user_ref(conn, "current_user_id"), expected_ref)
