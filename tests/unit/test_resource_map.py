from __future__ import absolute_import, division, print_function

__metaclass__ = type

import unittest

from ansible_collections.os_migrate.os_migrate.plugins.module_utils import const
from ansible_collections.os_migrate.os_migrate.plugins.module_utils import resource_map
from ansible_collections.os_migrate.os_migrate.plugins.module_utils import (
    user_project_role_assignment,
)


def _const_resource_types():
    """Return all RES_TYPE_* values defined in const."""
    return {
        getattr(const, name)
        for name in dir(const)
        if name.startswith("RES_TYPE_")
    }


class TestResourceMap(unittest.TestCase):

    def test_all_const_resource_types_are_mapped(self):
        expected = _const_resource_types()
        mapped = set(resource_map.RESOURCE_MAP.keys())
        self.assertEqual(
            expected,
            mapped,
            "RESOURCE_MAP keys must match const.RES_TYPE_* exactly. "
            f"missing={sorted(expected - mapped)} "
            f"extra={sorted(mapped - expected)}",
        )

    def test_mapped_values_are_resource_classes(self):
        for res_type, cls in resource_map.RESOURCE_MAP.items():
            self.assertEqual(
                cls.resource_type,
                res_type,
                f"{cls.__name__}.resource_type does not match map key {res_type}",
            )

    def test_user_project_role_assignment_mapped(self):
        self.assertIs(
            resource_map.RESOURCE_MAP[const.RES_TYPE_USER_PROJECT_ROLE_ASSIGNMENT],
            user_project_role_assignment.UserProjectRoleAssignment,
        )

    def test_no_orphan_map_keys(self):
        """RESOURCE_MAP must not contain keys absent from const.RES_TYPE_*."""
        expected = _const_resource_types()
        mapped = set(resource_map.RESOURCE_MAP.keys())
        orphans = mapped - expected
        self.assertEqual(
            set(),
            orphans,
            f"Orphan RESOURCE_MAP keys with no const.RES_TYPE_*: {sorted(orphans)}",
        )
