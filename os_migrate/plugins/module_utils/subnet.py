from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

import openstack

from ansible_collections.os_migrate.os_migrate.plugins.module_utils import const
from ansible_collections.os_migrate.os_migrate.plugins.module_utils import exc
from ansible_collections.os_migrate.os_migrate.plugins.module_utils.serialization \
    import set_sdk_params_same_name, set_ser_params_same_name


def serialize_subnet(sdk_subnet):
    """Serialize OpenStack SDK network `sdk_net` into OS-Migrate
    format. Use `net_refs` for id-to-name mappings.

    Returns: Dict - OS-Migrate structure for Network
    """
    expected_type = openstack.network.v2.subnet.Subnet
    if type(sdk_subnet) != expected_type:
        raise exc.UnexpectedResourceType(expected_type, type(sdk_subnet))

    resource = {}
    params = {}
    info = {}
    resource[const.RES_PARAMS] = params
    resource[const.RES_INFO] = info
    resource[const.RES_TYPE] = const.RES_TYPE_SUBNET

    # FIXME: We will need to eventually add network_name, subnet_pool_name
    # and segment_name into params.  See issue #88.
    set_ser_params_same_name(params, sdk_subnet, [
        'allocation_pools',
        'cidr',
        'description',
        'dns_nameservers',
        'gateway_ip',
        'host_routes',
        'ip_version',
        'ipv6_address_mode',
        'ipv6_ra_mode',
        'is_dhcp_enabled',
        'name',
        'service_types',
        'tags',
        'use_default_subnet_pool'
    ])

    set_ser_params_same_name(info, sdk_subnet, [
        'created_at',
        'id',
        'network_id',
        'prefix_length',
        'project_id',
        'revision_number',
        'segment_id',
        'subnet_pool_id',
        'updated_at',
    ])

    return resource
