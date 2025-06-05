from __future__ import absolute_import, division, print_function

__metaclass__ = type

import unittest

import ansible

from ansible_collections.os_migrate.os_migrate.plugins.filter.stringfilter import (
    stringfilter,
)


class TestStringfilter(unittest.TestCase):

    def test_stringfilter_strings(self):
        strings = [
            "one",
            "two",
            "three",
            "prefixed-one",
            "prefixed-two",
            "prefixed-three",
            "one-suffixed",
            "two-suffixed",
            "three-suffixed",
        ]

        self.assertEqual(
            stringfilter(strings, ["one", "prefixed"]),
            ["one"],
        )

        self.assertEqual(
            stringfilter(strings, ["one", {"regex": "^prefixed"}]),
            ["one", "prefixed-one", "prefixed-two", "prefixed-three"],
        )

        self.assertEqual(
            stringfilter(strings, [{"regex": "xed$"}]),
            ["one-suffixed", "two-suffixed", "three-suffixed"],
        )

        self.assertEqual(
            stringfilter(strings, [{"regex": "one"}]),
            ["one", "prefixed-one", "one-suffixed"],
        )

        self.assertEqual(
            stringfilter(strings, []),
            [],
        )

    def test_stringfilter_problems(self):
        with self.assertRaises(TypeError):
            stringfilter(None, [])

        with self.assertRaises(TypeError):
            stringfilter(["one"], None)

        # 'regexp' instead of 'regex'
        with self.assertRaises(ansible.errors.AnsibleFilterError):
            stringfilter(["one"], [{"regexp": "one"}])

        # value not a string
        with self.assertRaises(ansible.errors.AnsibleFilterError):
            stringfilter(["one", 1], [{"regexp": "one"}])

    def test_stringfilter_dicts(self):
        items = [
            {"a": "one", "b": "another one"},
            {"a": "two", "b": "another two"},
            {"a": "three", "b": "another three"},
            {"a": "prefixed-one", "b": "another prefixed-one"},
            {"a": "prefixed-two", "b": "another prefixed-two"},
            {"a": "prefixed-three", "b": "another prefixed-three"},
            {"a": "one-suffixed", "b": "another one-suffixed"},
            {"a": "two-suffixed", "b": "another two-suffixed"},
            {"a": "three-suffixed", "b": "another three-suffixed"},
        ]

        self.assertEqual(
            stringfilter(items, ["one", "prefixed"], attribute="a"),
            [{"a": "one", "b": "another one"}],
        )

        self.assertEqual(
            stringfilter(items, ["one", {"regex": "^prefixed"}], attribute="a"),
            [
                {"a": "one", "b": "another one"},
                {"a": "prefixed-one", "b": "another prefixed-one"},
                {"a": "prefixed-two", "b": "another prefixed-two"},
                {"a": "prefixed-three", "b": "another prefixed-three"},
            ],
        )

        self.assertEqual(
            stringfilter(items, [{"regex": "xed$"}], attribute="a"),
            [
                {"a": "one-suffixed", "b": "another one-suffixed"},
                {"a": "two-suffixed", "b": "another two-suffixed"},
                {"a": "three-suffixed", "b": "another three-suffixed"},
            ],
        )

        self.assertEqual(
            stringfilter(items, [{"regex": "one"}], attribute="a"),
            [
                {"a": "one", "b": "another one"},
                {"a": "prefixed-one", "b": "another prefixed-one"},
                {"a": "one-suffixed", "b": "another one-suffixed"},
            ],
        )

        self.assertEqual(
            stringfilter(items, [], attribute="a"),
            [],
        )

        # no 'attribute' provided but iterating over dicts
        with self.assertRaises(ansible.errors.AnsibleFilterError):
            stringfilter(items, [{"regexp": "one"}])

    def test_stringfilter_nested_dicts(self):
        items = [
            {"outer": {"a": "one", "b": "another one"}},
            {"outer": {"a": "two", "b": "another two"}},
            {"outer": {"a": "three", "b": "another three"}},
            {"outer": {"a": "prefixed-one", "b": "another prefixed-one"}},
            {"outer": {"a": "prefixed-two", "b": "another prefixed-two"}},
            {"outer": {"a": "prefixed-three", "b": "another prefixed-three"}},
            {"outer": {"a": "one-suffixed", "b": "another one-suffixed"}},
            {"outer": {"a": "two-suffixed", "b": "another two-suffixed"}},
            {"outer": {"a": "three-suffixed", "b": "another three-suffixed"}},
        ]

        self.assertEqual(
            stringfilter(items, ["one", "prefixed"], attribute="outer.a"),
            [{"outer": {"a": "one", "b": "another one"}}],
        )

        self.assertEqual(
            stringfilter(items, ["one", {"regex": "^prefixed"}], attribute="outer.a"),
            [
                {"outer": {"a": "one", "b": "another one"}},
                {"outer": {"a": "prefixed-one", "b": "another prefixed-one"}},
                {"outer": {"a": "prefixed-two", "b": "another prefixed-two"}},
                {"outer": {"a": "prefixed-three", "b": "another prefixed-three"}},
            ],
        )

        self.assertEqual(
            stringfilter(items, [{"regex": "xed$"}], attribute="outer.a"),
            [
                {"outer": {"a": "one-suffixed", "b": "another one-suffixed"}},
                {"outer": {"a": "two-suffixed", "b": "another two-suffixed"}},
                {"outer": {"a": "three-suffixed", "b": "another three-suffixed"}},
            ],
        )

        self.assertEqual(
            stringfilter(items, [{"regex": "one"}], attribute="outer.a"),
            [
                {"outer": {"a": "one", "b": "another one"}},
                {"outer": {"a": "prefixed-one", "b": "another prefixed-one"}},
                {"outer": {"a": "one-suffixed", "b": "another one-suffixed"}},
            ],
        )

        self.assertEqual(
            stringfilter(items, [], attribute="outer.a"),
            [],
        )

    def test_stringfilter_nested_dict_problems(self):
        # invalid attribute path
        with self.assertRaises(ansible.errors.AnsibleFilterError):
            stringfilter(
                [{"outer": {"b": 'no "a" in here'}}],
                [{"regexp": "one"}],
                attribute="outer.a",
            )

        # value not a string
        with self.assertRaises(ansible.errors.AnsibleFilterError):
            stringfilter(
                [{"outer": {"a": 1}}], [{"regexp": "one"}], attribute="outer.a"
            )
