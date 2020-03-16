from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

import openstack

from ansible_collections.os_migrate.os_migrate.plugins.module_utils \
    import const, reference, resource


class Network(resource.Resource):

    resource_type = const.RES_TYPE_NETWORK
    sdk_class = openstack.network.v2.network.Network

    info_from_sdk = [
        'availability_zones',
        'created_at',
        'id',
        'project_id',
        'qos_policy_id',
        'revision_number',
        'status',
        'subnet_ids',
        'updated_at',
    ]
    params_from_sdk = [
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
    ]
    params_from_refs = [
        'qos_policy_name',
    ]
    sdk_params_from_refs = [
        'qos_policy_id',
    ]

    @classmethod
    def from_sdk(cls, conn, sdk_resource):
        obj = super(Network, cls).from_sdk(conn, sdk_resource)
        obj._sort_param('availability_zone_hints')
        obj._sort_info('subnet_ids')
        return obj

    @staticmethod
    def _create_sdk_res(conn, sdk_params):
        return conn.network.create_network(**sdk_params)

    @staticmethod
    def _find_sdk_res(conn, name_or_id):
        return conn.network.find_network(name_or_id)

    @staticmethod
    def _refs_from_sdk(conn, sdk_res):
        refs = {}
        refs['qos_policy_id'] = sdk_res['qos_policy_id']
        refs['qos_policy_name'] = reference.qos_policy_name(
            conn, sdk_res['qos_policy_id'])
        return refs

    def _refs_from_ser(self, conn):
        refs = {}
        refs['qos_policy_name'] = self.params()['qos_policy_name']
        refs['qos_policy_id'] = reference.qos_policy_id(
            conn, self.params()['qos_policy_name'])
        return refs

    @staticmethod
    def _update_sdk_res(conn, name_or_id, sdk_params):
        return conn.network.update_network(name_or_id, **sdk_params)
