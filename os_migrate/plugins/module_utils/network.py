from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

import openstack

from ansible_collections.os_migrate.os_migrate.plugins.module_utils import exc
from ansible_collections.os_migrate.os_migrate.plugins.module_utils.serialization \
    import set_sdk_params_same_name, set_ser_params_same_name


def serialize_network(sdk_net, net_refs):
    expected_type = openstack.network.v2.network.Network
    if type(sdk_net) != expected_type:
        raise exc.UnexpectedResourceType(expected_type, type(sdk_net))

    resource = {}
    params = {}
    info = {}
    resource['params'] = params
    resource['info'] = info
    resource['type'] = 'openstack.network'

    params['availability_zone_hints'] = sorted(sdk_net['availability_zone_hints'])
    set_ser_params_same_name(params, sdk_net, [
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
        'segments',
    ])
    set_ser_params_same_name(params, net_refs, [
        'qos_policy_name',
    ])

    info['subnet_ids'] = sorted(sdk_net['subnet_ids'])
    set_ser_params_same_name(info, sdk_net, [
        'availability_zones',
        'created_at',
        'project_id',
        'qos_policy_id',
        'revision_number',
        'status',
        'updated_at',
    ])

    return resource


def network_sdk_params(ser_net, net_refs):
    res_type = ser_net.get('type', None)
    if res_type != 'openstack.network':
        raise exc.UnexpectedResourceType('openstack.network', res_type)

    ser_params = ser_net['params']
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
        'segments',
    ])
    set_sdk_params_same_name(net_refs, sdk_params, [
        'qos_policy_id',
    ])

    return sdk_params


def network_needs_update(sdk_net, net_refs, target_ser_net):
    current_params = serialize_network(sdk_net, net_refs)['params']
    target_params = target_ser_net['params']
    return current_params != target_params


def network_refs_from_sdk(conn, sdk_net):
    expected_type = openstack.network.v2.network.Network
    if type(sdk_net) != expected_type:
        raise exc.UnexpectedResourceType(expected_type, type(sdk_net))
    refs = {}

    # when creating refs from SDK Network object, we copy IDs and
    # query the cloud for names

    # TODO: consider adding project_name and subnet_names. They aren't
    # required for import but may be interesting for the transform
    # phase.
    for field in ['project_id', 'qos_policy_id', 'subnet_ids']:
        refs[field] = sdk_net[field]
    for field in ['project_name', 'qos_policy_name', 'subnet_names']:
        refs[field] = None

    if sdk_net['qos_policy_id']:
        refs['qos_policy_name'] = conn.network.get_qos_policy(
            sdk_net['qos_policy_id'])['name']

    return refs


def network_refs_from_ser(conn, ser_net):
    if ser_net['type'] != 'openstack.network':
        raise exc.UnexpectedResourceType('openstack.network', ser_net['type'])
    ser_params = ser_net['params']
    refs = {}

    # when creating refs from serialized Network, we copy names and
    # query the cloud for IDs

    # TODO: consider adding project_name and subnet_names. They aren't
    # required for import but may be interesting for the transform
    # phase.
    for field in ['qos_policy_id']:
        refs[field] = None
    for field in ['qos_policy_name']:
        refs[field] = ser_params[field]

    if ser_params['qos_policy_name']:
        refs['qos_policy_id'] = conn.network.get_qos_policy(
            ser_params['qos_policy_name'])['id']

    return refs
