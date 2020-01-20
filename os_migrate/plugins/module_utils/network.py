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

    params['availability_zone_hints'] = sorted(network['availability_zone_hints'])
    params['description'] = network['description']
    params['dns_domain'] = network['dns_domain']
    params['is_admin_state_up'] = network['is_admin_state_up']
    params['is_default'] = network['is_default']
    params['is_port_security_enabled'] = network['is_port_security_enabled']
    params['is_router_external'] = network['is_router_external']
    params['is_shared'] = network['is_shared']
    params['is_vlan_transparent'] = network['is_vlan_transparent']
    params['mtu'] = network['mtu']
    params['name'] = network['name']
    params['provider_network_type'] = network['provider_network_type']
    params['provider_physical_network'] = network['provider_physical_network']
    params['provider_segmentation_id'] = network['provider_segmentation_id']
    params['qos_policy_id'] = network['qos_policy_id']
    params['segments'] = network['segments']

    info['availability_zones'] = network['availability_zones']
    info['created_at'] = network['created_at']
    info['project_id'] = network['project_id']
    info['revision_number'] = network['revision_number']
    info['status'] = network['status']
    info['subnet_ids'] = sorted(network['subnet_ids'])
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
