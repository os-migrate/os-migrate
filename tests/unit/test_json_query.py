from __future__ import absolute_import, division, print_function

__metaclass__ = type

import unittest

from ansible import errors

from ansible_collections.os_migrate.os_migrate.plugins.filter import json_query as json_query_mod
from ansible_collections.os_migrate.os_migrate.plugins.filter.json_query import (
    json_query,
)


class TestJsonQuery(unittest.TestCase):

    def test_select_attribute(self):
        data = {"name": "net1", "id": "uuid-1", "status": "ACTIVE"}
        self.assertEqual(json_query(data, "name"), "net1")

    def test_filter_list(self):
        data = [
            {"name": "one", "status": "active"},
            {"name": "two", "status": "down"},
            {"name": "three", "status": "active"},
        ]
        self.assertEqual(
            json_query(data, "[?status=='active'].name"),
            ["one", "three"],
        )

    def test_projection(self):
        data = [
            {"name": "a", "id": "1", "extra": "x"},
            {"name": "b", "id": "2", "extra": "y"},
        ]
        self.assertEqual(
            json_query(data, "[*].{name: name, id: id}"),
            [{"name": "a", "id": "1"}, {"name": "b", "id": "2"}],
        )

    def test_invalid_expression(self):
        with self.assertRaises(errors.AnsibleFilterError) as ctx:
            json_query({"a": 1}, "[")
        self.assertIn("invalid JMESPath expression", str(ctx.exception))

    def test_missing_jmespath(self):
        original = json_query_mod.HAS_JMESPATH
        try:
            json_query_mod.HAS_JMESPATH = False
            with self.assertRaises(errors.AnsibleFilterError) as ctx:
                json_query({"a": 1}, "a")
            self.assertIn("jmespath", str(ctx.exception).lower())
        finally:
            json_query_mod.HAS_JMESPATH = original

    def test_filter_module_registration(self):
        filters = json_query_mod.FilterModule().filters()
        self.assertIn("json_query", filters)
        self.assertIs(filters["json_query"], json_query)
