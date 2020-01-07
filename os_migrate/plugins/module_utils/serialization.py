from __future__ import (absolute_import, division, print_function)
__metaclass__ = type


def serialize_network(network):
    resource = {}
    params = {}
    info = {}
    resource['params'] = params
    resource['info'] = info
    resource['type'] = 'openstack.network'

    params['availability_zone_hints'] = network['availability_zone_hints']
    params['availability_zones'] = network['availability_zones']
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
    params['revision_number'] = network['revision_number']
    params['segments'] = network['segments']

    info['created_at'] = network['created_at']
    info['project_id'] = network['project_id']
    info['status'] = network['status']
    info['subnet_ids'] = network['subnet_ids']
    info['updated_at'] = network['updated_at']

    # TODO: Add a (cached?) lookup for names of id-like properties.
    #     params['qos_policy_name']
    #     info['project_name']
    #     info['subnet_names']

    return resource
