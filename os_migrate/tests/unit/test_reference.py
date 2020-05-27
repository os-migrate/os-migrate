from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

import unittest

from ansible_collections.os_migrate.os_migrate.plugins.module_utils import reference


class TestReference(unittest.TestCase):

    def test_fetch_name(self):
        self.assertEqual(
            reference._fetch_name(_mock_get_method, 'someid'),
            'name-of-someid',
        )
        self.assertEqual(
            reference._fetch_name(_mock_get_method, None),
            None,
        )

    def test_fetch_id_simple(self):
        self.assertEqual(
            reference._fetch_id_simple(_mock_get_method, 'somename'),
            'id-of-somename',
        )
        self.assertEqual(
            reference._fetch_id_simple(_mock_get_method, None),
            None,
        )


def _mock_get_method(id_or_name, ignore_missing=True):
    return {
        'id': 'id-of-{0}'.format(id_or_name),
        'name': 'name-of-{0}'.format(id_or_name),
    }
