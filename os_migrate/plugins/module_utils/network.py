from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

import openstack

from ansible_collections.os_migrate.os_migrate.plugins.module_utils import exc
from ansible_collections.os_migrate.os_migrate.plugins.module_utils.serialization \
    import set_sdk_params_same_name, set_ser_params_same_name


def serialize_network(network):
    expected_type = openstack.network.v2.network.Network
    if type(network) != expected_type:
        raise exc.UnexpectedResourceType(expected_type, type(network))

    resource = {}
    params = {}
    info = {}
    resource['params'] = params
    resource['info'] = info
    resource['type'] = 'openstack.network'

    params['availability_zone_hints'] = sorted(network['availability_zone_hints'])
    set_ser_params_same_name(params, network, [
        'description',
        'dns_domain',
        'is_admin_state_up',
        'is_default',
        'is_port_security_enabled',
        'is_router_external',
        'is_shared',
        'is_vlan_transparent',
        'mtu',
        'name',
        'provider_network_type',
        'provider_physical_network',
        'provider_segmentation_id',
        'qos_policy_id',
        'segments',
    ])

    info['subnet_ids'] = sorted(network['subnet_ids'])
    set_ser_params_same_name(info, network, [
        'availability_zones',
        'created_at',
        'project_id',
        'revision_number',
        'status',
        'updated_at',
    ])

    # TODO: Add a (cached?) lookup for names of id-like properties.
    #     params['qos_policy_name']
    #     info['project_name']
    #     info['subnet_names']

    return resource


def network_sdk_params(serialized):
    res_type = serialized.get('type', None)
    if res_type != 'openstack.network':
        raise exc.UnexpectedResourceType('openstack.network', res_type)

    ser_params = serialized['params']
    sdk_params = {}

    set_sdk_params_same_name(ser_params, sdk_params, [
        'availability_zone_hints',
        'description',
        'dns_domain',
        'is_admin_state_up',
        'is_default',
        'is_port_security_enabled',
        'is_router_external',
        'is_shared',
        'is_vlan_transparent',
        'mtu',
        'name',
        'provider_network_type',
        'provider_physical_network',
        'provider_segmentation_id',
        'qos_policy_id',
        'segments',
    ])

    return sdk_params


def network_needs_update(sdk_network, target_serialized_state):
    current_params = serialize_network(sdk_network)['params']
    target_params = target_serialized_state['params']
    return current_params != target_params
