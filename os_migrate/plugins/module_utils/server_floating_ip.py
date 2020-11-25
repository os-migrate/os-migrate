from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

import openstack

from ansible_collections.os_migrate.os_migrate.plugins.module_utils \
    import exc, const, resource


def server_floating_ips(conn, server_ports):
    sdk_fips = []

    # Typically a server will have one or a few ports, while there can
    # be many listable FIPs. It is expected to be better to query FIPs
    # attached to a given port, rather than to query all FIPs visible
    # to the user and filter them on client side.
    for port in server_ports:
        port_fips = list(conn.network.ips(port_id=port.info()['id']))
        sdk_fips.extend(port_fips)

    return sdk_fips


class ServerFloatingIP(resource.Resource):

    resource_type = const.RES_TYPE_SERVER_FLOATING_IP
    sdk_class = openstack.network.v2.floating_ip.FloatingIP

    info_from_sdk = [
        'created_at',
        'floating_network_id',
        'id',
        'port_id',
        'router_id',
        'updated_at',
    ]
    params_from_sdk = [
        'fixed_ip_address',
        'floating_ip_address',
        'tags',
    ]
    params_from_refs = [
    ]
    sdk_params_from_params = [
        'fixed_ip_address',
        'tags',
    ]
    sdk_params_from_refs = []

    def create_or_update(self, conn, filters=None):
        raise exc.Unsupported("Direct ServerFloatingIP.create_or_update call is unsupported.")

    @staticmethod
    def _refs_from_sdk(conn, sdk_res):
        refs = {}
        return refs

    def _refs_from_ser(self, conn, filters=None):
        refs = {}
        return refs
