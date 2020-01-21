from __future__ import (absolute_import, division, print_function)
__metaclass__ = type


class UnexpectedResourceType(Exception):
    """Unexpected resource type."""

    msg_format = "Expected resource type '{}' but got '{}'."

    def __init__(self, expected_type, got_type):
        message = self.msg_format.format(expected_type, got_type)
        super(UnexpectedResourceType, self).__init__(message)
