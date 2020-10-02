from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

import openstack

from ansible_collections.os_migrate.os_migrate.plugins.module_utils \
    import const, reference, resource


class Server(resource.Resource):

    resource_type = const.RES_TYPE_SERVER
    sdk_class = openstack.compute.v2.server.Server

    info_from_sdk = [
        'created_at',
        'id',
        'status',
        'updated_at',
    ]
    info_from_refs = [
        'flavor_id',
        'security_group_ids',
    ]
    params_from_sdk = [
        'description',
        'name',
    ]
    params_from_refs = [
        'addresses_refs',
        'flavor_ref',
        'security_group_refs',
    ]
    sdk_params_from_refs = [
        'flavor_id',
    ]

    migration_param_defaults = {
        'boot_disk_copy': True,
    }

    @classmethod
    def from_sdk(cls, conn, sdk_resource):
        obj = super(Server, cls).from_sdk(conn, sdk_resource)
        return obj

    def create(self, conn, block_device_mapping):
        sdk_params = self.sdk_params(conn)
        sdk_params['block_device_mapping'] = block_device_mapping
        return conn.compute.create_server(**sdk_params)

    def sdk_params(self, conn):
        refs = self._refs_from_ser(conn)
        sdk_params = self._to_sdk_params(refs)

        # Nova requires security groups by name
        sdk_params['security_groups'] = list(map(
            lambda ref: {'name': ref['name']},
            refs['security_group_refs'],
        ))

        sdk_params['networks'] = []
        addresses = refs['addresses_ids']
        for net_id, net_ports in addresses.items():
            for port in net_ports:
                if port['OS-EXT-IPS:type'] == 'fixed':
                    sdk_params['networks'].append({
                        "uuid": net_id,
                        "fixed_ip": port['addr'],
                    })

        return sdk_params

    @staticmethod
    def _find_sdk_res(conn, name_or_id, filters=None):
        return conn.compute.find_server(name_or_id, **(filters or {}))

    @staticmethod
    def _refs_from_sdk(conn, sdk_res):
        refs = {}

        # Nova only returns network names in response, not IDs. This
        # can be insufficient in edge cases. We have to hope that
        # private/public network names don't collide, and do a lookup
        # without project scope.
        refs['addresses_refs'] = sdk_res['addresses']
        refs['addresses_ids'] = {}
        for net_name, net_addrs in sdk_res['addresses'].items():
            net_id = reference.network_id(conn, {
                'name': net_name,
                'project_name': None,
                'domain_name': None,
            })
            refs['addresses_ids'][net_id] = net_addrs

        # There are multiple representations of server in SDK, some of
        # them don't have flavor ID info.
        flavor_id = sdk_res['flavor'].get('id')
        if flavor_id is None:
            flavor_id = conn.get_server_by_id(sdk_res['id'])['flavor']['id']

        refs['flavor_id'] = flavor_id
        refs['flavor_ref'] = reference.flavor_ref(
            conn, flavor_id)

        sec_groups = list(conn.compute.fetch_server_security_groups(sdk_res)
                          .security_groups)
        refs['security_group_ids'] = [
            sec_group['id']
            for sec_group in sec_groups]
        refs['security_group_refs'] = [
            reference.security_group_ref(conn, sec_group['id'])
            for sec_group in sec_groups]
        return refs

    def _refs_from_ser(self, conn, filters=None):
        refs = {}

        # Nova only returns network names in response, not IDs. This
        # can be insufficient in edge cases. We have to hope that
        # private/public network names don't collide, and do a lookup
        # without project scope.
        refs['addresses_refs'] = self.params()['addresses_refs']
        refs['addresses_ids'] = {}
        for net_name, net_addrs in refs['addresses_refs'].items():
            net_id = reference.network_id(conn, {
                'name': net_name,
                'project_name': None,
                'domain_name': None,
            })
            refs['addresses_ids'][net_id] = net_addrs

        refs['flavor_id'] = reference.flavor_id(
            conn, self.params()['flavor_ref'])
        refs['flavor_ref'] = self.params()['flavor_ref']

        refs['security_group_refs'] = self.params()['security_group_refs']
        refs['security_group_ids'] = [
            reference.security_group_id(conn, sec_group_ref)
            for sec_group_ref in self.params()['security_group_refs']]

        return refs
