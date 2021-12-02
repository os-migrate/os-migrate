from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

from ansible_collections.os_migrate.os_migrate.plugins.module_utils import const


class CannotConverge(Exception):
    """State is incorrect and cannot be auto-converged.
    Operator intervention is required.
    """

    def __init__(self, message):
        super().__init__(message)


class DataVersionMismatch(Exception):
    """Data file version does not match OS Migrate runtime version."""

    msg_format = (
        "OS Migrate runtime is version '{}', but tried to parse data "
        "file '{}' with os_migrate_version field set to '{}'. "
        "(Exported data is not guaranteed to be compatible across versions. "
        "After upgrading OS Migrate, make sure to remove the old "
        "YAML exports from the data directory.)"
    )

    def __init__(self, file_path, got_version):
        message = self.msg_format.format(const.OS_MIGRATE_VERSION, file_path, got_version)
        super().__init__(message)


class InconsistentState(Exception):
    """Inconsistent state in data."""

    msg_format = "Inconsistent state: '{}'."

    def __init__(self, msg):
        message = self.msg_format.format(msg)
        super().__init__(message)


class UnexpectedResourceType(Exception):
    """Unexpected resource type."""

    msg_format = "Expected resource type '{}' but got '{}'."

    def __init__(self, expected_type, got_type):
        message = self.msg_format.format(expected_type, got_type)
        super().__init__(message)


class UnexpectedValue(Exception):
    """Unexpected value of a variable."""

    msg_format = "Unexpected value of '{}': expected '{}' but got '{}'."

    def __init__(self, var, expected, got):
        message = self.msg_format.format(var, expected, got)
        super().__init__(message)


class UnexpectedChoice(Exception):
    """Unexpected value of a variable which should be chosen from a list."""

    msg_format = "Unexpected value of '{}': expected one of {} but got '{}'."

    def __init__(self, var, choice_list, got):
        message = self.msg_format.format(var, choice_list, got)
        super().__init__(message)


class Unsupported(Exception):
    """Unsupported action."""

    msg_format = "Unsupported: '{}'."

    def __init__(self, msg):
        message = self.msg_format.format(msg)
        super().__init__(message)
