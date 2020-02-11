from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

import unittest

import ansible

from ansible_collections.os_migrate.os_migrate.plugins.filter.stringfilter \
    import stringfilter


class TestStringfilter(unittest.TestCase):

    def test_stringfilter(self):
        strings = [
            'one',
            'two',
            'three',
            'prefixed-one',
            'prefixed-two',
            'prefixed-three',
            'one-suffixed',
            'two-suffixed',
            'three-suffixed',
        ]

        self.assertEqual(
            stringfilter(strings, ['one', 'prefixed']),
            ['one'],
        )

        self.assertEqual(
            stringfilter(strings, ['one', {'regex': '^prefixed'}]),
            ['one', 'prefixed-one', 'prefixed-two', 'prefixed-three'],
        )

        self.assertEqual(
            stringfilter(strings, [{'regex': 'xed$'}]),
            ['one-suffixed', 'two-suffixed', 'three-suffixed'],
        )

        self.assertEqual(
            stringfilter(strings, [{'regex': 'one'}]),
            ['one', 'prefixed-one', 'one-suffixed'],
        )

        self.assertEqual(
            stringfilter(strings, []),
            [],
        )

        with self.assertRaises(TypeError):
            stringfilter(None, [])

        with self.assertRaises(TypeError):
            stringfilter(strings, None)

        with self.assertRaises(ansible.errors.AnsibleFilterError):
            stringfilter(strings, [{'regexp': 'one'}])
