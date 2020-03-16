from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

import openstack

from ansible_collections.os_migrate.os_migrate.plugins.module_utils \
    import const, reference, resource


def router_interfaces(conn, sdk_rtr):
    return filter(lambda p: p['device_owner'] == "network:router_interface",
                  router_ports(conn, sdk_rtr))


def router_ports(conn, sdk_rtr):
    return conn.network.ports(device_id=sdk_rtr['id'])


class RouterInterface(resource.Resource):

    resource_type = const.RES_TYPE_ROUTER_INTERFACE
    sdk_class = openstack.network.v2.port.Port

    info_from_sdk = [
        'id',
    ]
    params_from_refs = [
        'router_name',
        'fixed_ips_names',
    ]

    @classmethod
    def from_sdk(cls, conn, sdk_resource):
        obj = super(RouterInterface, cls).from_sdk(conn, sdk_resource)
        return obj

    @staticmethod
    def _refs_from_sdk(conn, sdk_res):
        refs = {}

        refs['fixed_ips'] = sdk_res['fixed_ips']
        refs['fixed_ips_names'] = []
        for fixed_ip in sdk_res['fixed_ips']:
            refs['fixed_ips_names'].append({
                'ip_address': fixed_ip['ip_address'],
                'subnet_name': reference.subnet_name(conn, fixed_ip['subnet_id']),
            })
        refs['router_id'] = sdk_res['device_id']
        refs['router_name'] = reference.router_name(conn, sdk_res['device_id'])

        return refs

    def _refs_from_ser(self, conn):
        return {}
