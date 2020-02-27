from __future__ import (absolute_import, division, print_function)
from enum import Enum
__metaclass__ = type


OS_MIGRATE_VERSION = '0.1.0'  # updated by build.sh

# Main serialization sections
RES_PARAMS = 'params'
RES_TYPE = 'type'
RES_INFO = '_info'

# Supported resource types
RES_TYPE_NETWORK = 'openstack.network.Network'
RES_TYPE_SECURITYGROUPRULE = 'openstack.network.SecurityGroupRule'
RES_TYPE_SECURITYGROUP = 'openstack.network.SecurityGroup'
RES_TYPE_SUBNET = 'openstack.subnet.Subnet'


# NOTE: OOP
# enums to replace the const values above.  Still provides . access to values
# but easier to read IMO.  The tradeoff that I see is when you want access to
# the string value under the type, you have to call .value
# const.RES_TYPE_NETWORK vs ResourceType.NETWORK
class ResourceType(Enum):
    NETWORK = 'openstack.network.Network'
    SECURITY_GROUP_RULE = 'openstack.network.SecurityGroupRule'
    SECURITY_GROUP = 'openstack.network.SecurityGroup'
    SUBNET = 'openstack.subnet.Subnet'


class Sections(Enum):
    PARAMS = 'params'
    TYPE = 'type'
    INFO = '_info'
