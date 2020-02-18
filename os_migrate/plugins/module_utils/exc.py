from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

from ansible_collections.os_migrate.os_migrate.plugins.module_utils import const


class UnexpectedResourceType(Exception):
    """Unexpected resource type."""

    msg_format = "Expected resource type '{}' but got '{}'."

    def __init__(self, expected_type, got_type):
        message = self.msg_format.format(expected_type, got_type)
        super(UnexpectedResourceType, self).__init__(message)


class DataVersionMismatch(Exception):
    """Data version does not match OS-Migrate version."""

    msg_format = "Expected data with os_migrate_version '{}' but got '{}'."

    def __init__(self, got_version):
        message = self.msg_format.format(const.OS_MIGRATE_VERSION, got_version)
        super(DataVersionMismatch, self).__init__(message)
