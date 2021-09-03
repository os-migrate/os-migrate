from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

from copy import deepcopy

import openstack

from ansible_collections.os_migrate.os_migrate.plugins.module_utils \
    import const, exc, reference, resource
from ansible_collections.os_migrate.os_migrate.plugins.module_utils.server_floating_ip \
    import server_floating_ips, ServerFloatingIP
from ansible_collections.os_migrate.os_migrate.plugins.module_utils.server_port \
    import server_ports, ServerPort
from ansible_collections.os_migrate.os_migrate.plugins.module_utils.server_volume \
    import server_volumes, ServerVolume


class Server(resource.Resource):

    resource_type = const.RES_TYPE_SERVER
    sdk_class = openstack.compute.v2.server.Server

    info_from_sdk = [
        'created_at',
        'id',
        'launched_at',
        'project_id',
        'status',
        'updated_at',
        'user_id',
    ]
    info_from_refs = [
        'flavor_id',
        'security_group_ids',
    ]
    params_from_sdk = [
        'availability_zone',
        'config_drive',
        'description',
        'disk_config',
        'key_name',
        'metadata',
        'name',
        'user_data',
        'scheduler_hints',
        'tags',
    ]
    params_from_refs = [
        'ports',
        'flavor_ref',
        'floating_ips',
        'image_ref',
        'security_group_refs',
        'volumes',
    ]
    sdk_params_from_refs = [
        'flavor_id',
        'image_id',
    ]

    migration_param_defaults = {
        'boot_disk_copy': False,
        'boot_volume_params': {
            'availability_zone': None,
            'name': None,
            'description': None,
            'volume_type': None,
        },
        'floating_ip_mode': 'auto',
    }

    @classmethod
    def from_sdk(cls, conn, sdk_resource):
        obj = super(Server, cls).from_sdk(conn, sdk_resource)
        params = obj.params()
        migration_params = obj.migration_params()

        # boot-from-volume servers must copy boot disk
        if params.get('image_ref') is None:
            migration_params['boot_disk_copy'] = True

        # config_drive can be returned as empty string but it cannot
        # be fed that way into create_server
        if params.get('config_drive') == '':
            params['config_drive'] = None

        return obj

    def create(self, conn, block_device_mapping):
        sdk_params = self.sdk_params(conn)

        # Simple port creation via Nova. Subsequently we may add
        # support for advanced port creation via Neutron.
        self.update_sdk_params_networks_simple(conn, sdk_params)

        self.update_sdk_params_block_device_mapping(sdk_params, block_device_mapping)
        sdk_srv = conn.compute.create_server(**sdk_params)
        self._create_floating_ips(conn, sdk_srv)
        return sdk_srv

    def sdk_params(self, conn):
        refs = self._refs_from_ser(conn)
        sdk_params = self._to_sdk_params(refs)

        # Nova requires security groups by name
        sdk_params['security_groups'] = list(map(
            lambda ref: {'name': ref['name']},
            refs['security_group_refs'],
        ))

        return sdk_params

    def _create_floating_ips(self, conn, sdk_srv):
        floating_ip_mode = self.migration_params()['floating_ip_mode']
        for fip_data in self.params()['floating_ips']:
            fip = ServerFloatingIP.from_data(fip_data)
            fip.create(conn, sdk_srv, floating_ip_mode)

    def update_migration_params(self, params_dict):
        if 'floating_ip_mode' in params_dict:
            value = params_dict['floating_ip_mode']
            choices = ['auto', 'skip']
            if value not in choices:
                raise exc.UnexpectedChoice('floating_ip_mode', choices, value)

        return super().update_migration_params(params_dict)

    def update_sdk_params_block_device_mapping(self, sdk_params, block_device_mapping):
        params, info = self.params_and_info()
        migration_params = self.migration_params()
        sdk_params['block_device_mapping'] = deepcopy(block_device_mapping)
        # shadowing to make sure we don't modify the function argument
        block_device_mapping = sdk_params['block_device_mapping']

        has_boot_volume = len(list(filter(
            lambda mapping: str(mapping['boot_index']) != '-1', block_device_mapping))) > 0
        if migration_params['boot_disk_copy'] and not has_boot_volume:
            raise exc.InconsistentState(
                ("Instance '{0}' ({1}) has boot_disk_copy enabled but block device mapping "
                 "has no boot volume: {2}").format(
                     params['name'], info['id'], block_device_mapping),
            )
        if not migration_params['boot_disk_copy'] and has_boot_volume:
            raise exc.InconsistentState(
                ("Instance '{0}' ({1}) has boot_disk_copy disabled but block device mapping "
                 "has a boot volume: {2}").format(
                     params['name'], info['id'], block_device_mapping)
            )

        image_id = sdk_params.get('image_id', None)
        if not has_boot_volume:
            if image_id is not None:
                block_device_mapping.insert(0, {
                    'boot_index': 0,
                    'delete_on_termination': True,
                    'destination_type': 'local',
                    'source_type': 'image',
                    'uuid': image_id,
                })
            else:
                raise exc.InconsistentState(
                    ("Instance '{0}' ({1}) has neither boot volume nor image reference. "
                     "Block device mapping: {2}").format(
                         params['name'], info['id'], block_device_mapping)
                )
        elif 'image_id' in sdk_params:
            del sdk_params['image_id']

    def update_sdk_params_networks_simple(self, conn, sdk_params):
        sdk_params['networks'] = []
        ports = list(map(ServerPort.from_data, self.params()['ports']))
        for port in ports:
            try:
                sdk_params['networks'].append(port.nova_sdk_params(conn))
            except exc.InconsistentState as e:
                params, info = self.params_and_info()
                raise exc.InconsistentState(
                    "Error creating network parameters for server '{0}' ({1}): {2}"
                    .format(params['name'], info['id'], e)
                ) from e

    @staticmethod
    def _find_sdk_res(conn, name_or_id, filters=None):
        return conn.compute.find_server(name_or_id, **(filters or {}))

    @staticmethod
    def _refs_from_sdk(conn, sdk_res):
        refs = {}

        # There are multiple representations of server in SDK, some of
        # them don't have flavor ID info.
        flavor_id = (sdk_res.get('flavor') or {}).get('id')
        if flavor_id is None:
            flavor_id = conn.get_server_by_id(sdk_res['id'])['flavor']['id']

        refs['flavor_id'] = flavor_id
        refs['flavor_ref'] = reference.flavor_ref(
            conn, flavor_id)

        refs['image_id'] = sdk_res['image']['id']
        refs['image_ref'] = reference.image_ref(
            conn, sdk_res['image']['id'])

        sec_groups = list(conn.compute.fetch_server_security_groups(sdk_res)
                          .security_groups)
        refs['security_group_ids'] = [
            sec_group['id']
            for sec_group in sec_groups]
        refs['security_group_refs'] = [
            reference.security_group_ref(conn, sec_group['id'])
            for sec_group in sec_groups]

        sdk_ports = server_ports(conn, sdk_res)
        ser_ports = list(map(lambda p: ServerPort.from_sdk(conn, p), sdk_ports))
        refs['ports'] = list(map(lambda p: p.data, ser_ports))

        sdk_fips = server_floating_ips(conn, ser_ports)
        ser_fips = map(lambda fip: ServerFloatingIP.from_sdk(conn, fip), sdk_fips)
        refs['floating_ips'] = list(map(lambda fip: fip.data, ser_fips))

        sdk_volumes = server_volumes(conn, sdk_res)
        ser_volumes = map(lambda vol: ServerVolume.from_sdk(conn, vol), sdk_volumes)
        refs['volumes'] = list(map(lambda vol: vol.data, ser_volumes))

        return refs

    def _refs_from_ser(self, conn, filters=None):
        refs = {}
        params = self.params()

        refs['flavor_ref'] = params['flavor_ref']
        refs['flavor_id'] = reference.flavor_id(
            conn, params['flavor_ref'])

        refs['image_ref'] = params['image_ref']
        if self.migration_params()['boot_disk_copy']:
            refs['image_id'] = None
        else:
            refs['image_id'] = reference.image_id(conn, params['image_ref'])

        refs['security_group_refs'] = params['security_group_refs']
        refs['security_group_ids'] = [
            reference.security_group_id(conn, sec_group_ref)
            for sec_group_ref in params['security_group_refs']]

        refs['ports'] = params['ports']
        refs['floating_ips'] = params['floating_ips']
        refs['volumes'] = params['volumes']

        return refs

    def dst_prerequisites_errors(self, conn, filters=None):
        """Get messages for unmet destination cloud prerequisites including keypairs.

        Returns: list of strings (error messages), empty when prerequisites
        are met
        """
        errors = super().dst_prerequisites_errors(conn, filters)

        # Parent class dst_prerequisites_errors does not validate keypairs exist in destination cloud.
        # To do this we do a lookup to see if keypair name exists and append to errors list if not
        params = self.params()
        try:
            conn.compute.find_keypair(params['key_name'], ignore_missing=False)
        except (openstack.exceptions.ResourceFailure,
                openstack.exceptions.ResourceNotFound,
                openstack.exceptions.DuplicateResource) as e:
            errors.append("Destination keypair prerequisites not met: {0}".format(e))
        return errors
