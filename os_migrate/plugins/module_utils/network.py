from __future__ import (absolute_import, division, print_function)
__metaclass__ = type


from ansible_collections.os_migrate.os_migrate.plugins.module_utils import exc
from ansible_collections.os_migrate.os_migrate.plugins.module_utils.serialization \
    import set_sdk_params_same_name


def serialize_network(network):
    resource = {}
    params = {}
    info = {}
    resource['params'] = params
    resource['info'] = info
    resource['type'] = 'openstack.network'

    params['availability_zone_hints'] = network['availability_zone_hints']
    params['description'] = network['description']
    params['dns_domain'] = network.get('dns_domain', None)
    params['is_admin_state_up'] = network.get(
        'admin_state_up', network.get('is_admin_state_up', None))
    params['is_default'] = network.get('is_default', None)
    params['is_port_security_enabled'] = network.get(
        'port_security_enabled', network.get('is_port_security_enabled', None))
    params['is_router_external'] = network.get(
        'is_router_external', network.get('router:external', None))
    params['is_shared'] = network.get('shared', network.get('is_shared', None))
    params['is_vlan_transparent'] = network.get('is_vlan_transparent', None)
    params['mtu'] = network['mtu']
    params['name'] = network['name']
    params['provider_network_type'] = network.get('provider_network_type', None)
    params['provider_physical_network'] = network.get('provider_physical_network', None)
    params['provider_segmentation_id'] = network.get('provider_segmentation_id', None)
    params['qos_policy_id'] = network.get('qos_policy_id', None)
    params['segments'] = network.get('segments', None)

    info['availability_zones'] = network['availability_zones']
    info['created_at'] = network['created_at']
    info['project_id'] = network['project_id']
    info['revision_number'] = network['revision_number']
    info['status'] = network['status']
    info['subnet_ids'] = network.get(
        'subnets', network.get('subnet_ids', None))
    info['updated_at'] = network['updated_at']

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
