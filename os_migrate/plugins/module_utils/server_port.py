from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

import openstack

from ansible_collections.os_migrate.os_migrate.plugins.module_utils \
    import exc, const, reference, resource


def server_ports(conn, sdk_ser):
    # the device_owner part after the colon varies - it is the availability zone
    return filter(lambda p: p.get('device_owner', '').startswith('compute:'),
                  conn.network.ports(device_id=sdk_ser['id']))


class ServerPort(resource.Resource):

    resource_type = const.RES_TYPE_SERVER_PORT
    sdk_class = openstack.network.v2.port.Port

    info_from_sdk = [
        'id',
        'device_owner',
        'device_id',
    ]
    params_from_refs = [
        'fixed_ips_refs',
        'network_ref',
    ]
    sdk_params_from_params = []
    sdk_params_from_refs = [
        'fixed_ips',
        'network_id',
    ]

    @classmethod
    def from_sdk(cls, conn, sdk_resource):
        obj = super(ServerPort, cls).from_sdk(conn, sdk_resource)
        # the part after the colon varies - it is the availability zone
        if not sdk_resource['device_owner'].startswith('compute:'):
            raise exc.UnexpectedValue(
                'device_owner', 'compute:*', sdk_resource['device_owner'])
        return obj

    def create_or_update(self, conn, filters=None):
        raise exc.Unsupported("Direct ServerPort.create_or_update call is unsupported.")

    def nova_sdk_params(self, conn):
        refs = self._refs_from_ser(conn)

        if len(refs['fixed_ips']) != 1:
            message = (
                "Using simple port creation via Nova is only supported for a single "
                f"IP address per port, but on network '{refs['network_ref'].get('name', '')}' "
                f"it has these addresses: {refs['fixed_ips_refs']}."
            )
            raise exc.InconsistentState(message)

        return {
            "uuid": refs['network_id'],
            "fixed_ip": refs['fixed_ips'][0]['ip_address'],
        }

    @staticmethod
    def _refs_from_sdk(conn, sdk_res):
        refs = {}

        refs['fixed_ips'] = sdk_res['fixed_ips']
        refs['fixed_ips_refs'] = []
        for fixed_ip in sdk_res['fixed_ips']:
            refs['fixed_ips_refs'].append({
                'ip_address': fixed_ip['ip_address'],
                'subnet_ref': reference.subnet_ref(conn, fixed_ip['subnet_id']),
            })
        refs['network_id'] = sdk_res['network_id']
        refs['network_ref'] = reference.network_ref(conn, sdk_res['network_id'])

        return refs

    def _refs_from_ser(self, conn, filters=None):
        refs = {}
        params = self.params()

        refs['fixed_ips_refs'] = params['fixed_ips_refs']
        refs['fixed_ips'] = []
        for fixed_ip in params['fixed_ips_refs']:
            refs['fixed_ips'].append({
                'ip_address': fixed_ip['ip_address'],
                'subnet_id': reference.subnet_id(conn, fixed_ip['subnet_ref']),
            })
        refs['network_ref'] = params['network_ref']
        refs['network_id'] = reference.network_id(conn, params['network_ref'])

        return refs
