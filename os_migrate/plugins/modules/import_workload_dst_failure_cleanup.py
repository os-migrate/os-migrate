#!/usr/bin/python


from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

ANSIBLE_METADATA = {
    'metadata_version': '1.1',
    'status': ['preview'],
    'supported_by': 'community'
}

DOCUMENTATION = '''
---
module: import_workload_dst_failure_cleanup

short_description: Clean up temporary volumes after a workload migration

extends_documentation_fragment: openstack

version_added: "2.9"

author: "OpenStack tenant migration tools (@os-migrate)"

description:
  - Remove any volumes associated with a failed workload migration in the destination cloud.

options:
  auth:
    description:
      - Dictionary with parameters for chosen auth type on the destination cloud.
    required: true
    type: dict
  auth_type:
    description:
      - Auth type plugin for destination OpenStack cloud. Can be omitted if using password authentication.
    required: false
    type: str
  region_name:
    description:
      - Destination OpenStack region name. Can be omitted if using default region.
    required: false
    type: str
  availability_zone:
    description:
      - Availability zone.
    required: false
    type: str
  cloud:
    description:
      - Ignored. Present for backwards compatibility.
    required: false
    type: raw
  validate_certs:
    description:
      - Validate HTTPS certificates when logging in to OpenStack.
    required: false
    type: bool
  conversion_host:
    description:
      - Dictionary with information about the destination conversion host (address, status, name, id)
    required: true
    type: dict
  data:
    description:
      - Data structure with server parameters as loaded from OS-Migrate workloads YAML file.
    required: true
    type: dict
  log_file:
    description:
      - Path to store a log file for this conversion process.
    required: false
    type: str
  state_file:
    description:
      - Path to store a transfer progress file for this conversion process.
    required: false
    type: str
  ssh_key_path:
    description:
      - Path to an SSH private key authorized on the destination cloud.
    required: true
    type: str
  ssh_user:
    description:
      - The SSH user to connect to the conversion hosts.
    required: true
    type: str
  transfer_uuid:
    description:
      - A UUID used to keep track of this tranfer's resources on the conversion hosts.
      - Provided by the import_workloads_export_volumes module.
    required: true
    type: str
  volume_map:
    description:
      - Dictionary providing information about the volumes to transfer.
      - Provided by the import_workloads_export_volumes module.
    required: true
    type: dict
  timeout:
    description:
      - Timeout for long running operations, in seconds.
    required: false
    default: 1800
    type: int
'''

EXAMPLES = '''
  rescue:
    - name: clean up in the destination cloud after migration failure
      os_migrate.os_migrate.import_workload_dst_failure_cleanup:
        auth: "{{ os_migrate_src_auth }}"
        auth_type: "{{ os_migrate_src_auth_type|default(omit) }}"
        region_name: "{{ os_migrate_src_region_name|default(omit) }}"
        validate_certs: "{{ os_migrate_src_validate_certs|default(omit) }}"
        ca_cert: "{{ os_migrate_src_ca_cert|default(omit) }}"
        client_cert: "{{ os_migrate_src_client_cert|default(omit) }}"
        client_key: "{{ os_migrate_src_client_key|default(omit) }}"
        data: "{{ item }}"
        conversion_host:
          "{{ os_src_conversion_host_info.openstack_conversion_host }}"
        ssh_key_path: "{{ os_migrate_conversion_keypair_private_path }}"
        ssh_user: "{{ os_migrate_conversion_host_ssh_user }}"
        transfer_uuid: "{{ exports.transfer_uuid }}"
        volume_map: "{{ exports.volume_map }}"
        state_file: "{{ os_migrate_data_dir }}/{{ prelim.server_name }}.state"
        log_file: "{{ os_migrate_data_dir }}/{{ prelim.server_name }}.log"
      when:
        - prelim.changed
        - os_migrate_workload_cleanup_on_failure

    - fail:
        msg: "Failed to import {{ item.params.name }}!"
'''

RETURN = '''
'''

from ansible.module_utils.basic import AnsibleModule
# Import openstack module utils from ansible_collections.openstack.cloud.plugins as per ansible 3+
try:
    from ansible_collections.openstack.cloud.plugins.module_utils.openstack \
        import openstack_full_argument_spec, openstack_cloud_from_module
except ImportError:
    # If this fails fall back to ansible < 3 imports
    from ansible.module_utils.openstack \
        import openstack_full_argument_spec, openstack_cloud_from_module

from ansible_collections.os_migrate.os_migrate.plugins.module_utils import server

from ansible_collections.os_migrate.os_migrate.plugins.module_utils.workload_common \
    import use_lock, ATTACH_LOCK_FILE_DESTINATION, DEFAULT_TIMEOUT, OpenStackHostBase

import time


class OpenStackDstFailureCleanup(OpenStackHostBase):
    """ Removes volumes after a failed migration from the destination cloud. """

    def __init__(self, openstack_connection, destination_conversion_host_id,
                 ssh_key_path, ssh_user, transfer_uuid, volume_map,
                 state_file=None, log_file=None, timeout=DEFAULT_TIMEOUT):

        super().__init__(
            openstack_connection,
            destination_conversion_host_id,
            ssh_key_path,
            ssh_user,
            transfer_uuid,
            state_file=state_file,
            log_file=log_file,
            timeout=timeout,
        )
        self.volume_map = volume_map

    def delete_migrated_volumes(self):
        """ Detach destination volumes from converter and delete them. """
        self._detach_volumes_from_converter()
        self._delete_volumes()

    def _volume_still_attached(self, volume, vm):
        """ Check if a volume is still attached to a VM. """
        for attachment in volume.attachments:
            if attachment.server_id == vm.id:
                return True
        return False

    def _get_volume_maybe(self, id_maybe):
        """ Get volume by id, or None if id_maybe is None or if volume doesn't exist. """
        if not id_maybe:
            return None
        return self.conn.get_volume_by_id(id_maybe)

    @use_lock(ATTACH_LOCK_FILE_DESTINATION)
    def _detach_volumes_from_converter(self):
        """ Detach volumes from conversion host. """
        self.log.info('Detaching volumes from the destination conversion host.')
        converter = self._converter()
        for path, mapping in self.volume_map.items():
            volume = self._get_volume_maybe(mapping['dest_id'])
            if not volume:
                continue
            if not self._volume_still_attached(volume, converter):
                self.log.info('Volume %s is not attached to conversion host, skipping detach.',
                              volume['id'])
                continue

            self.log.info('Detaching volume %s.', volume['id'])
            self.conn.detach_volume(server=converter, volume=volume,
                                    timeout=self.timeout, wait=True)
            for second in range(self.timeout):
                converter = self._converter()
                volume = self.conn.get_volume_by_id(mapping['dest_id'])
                if not self._volume_still_attached(volume, converter):
                    break
                time.sleep(1)
            else:
                raise RuntimeError('Timed out waiting to detach volumes from '
                                   'destination conversion host!')

    def _delete_volumes(self):
        """ Delete destination volumes. """
        self.log.info('Deleting migrated volumes from destination.')
        for path, mapping in self.volume_map.items():
            volume = self._get_volume_maybe(mapping['dest_id'])
            if not volume:
                continue
            if volume.attachments:
                self.log.warning('Volume %s is still has attachments, skipping delete.',
                                 volume['id'])
                continue

            self.log.info('Deleting volume %s.', volume['id'])
            self.conn.delete_volume(volume['id'], timeout=self.timeout, wait=True)


def run_module():
    argument_spec = openstack_full_argument_spec(
        data=dict(type='dict', required=True),
        conversion_host=dict(type='dict', required=True),
        ssh_key_path=dict(type='str', required=True),
        ssh_user=dict(type='str', required=True),
        transfer_uuid=dict(type='str', required=True),
        volume_map=dict(type='dict', required=True),
        state_file=dict(type='str', default=None),
        log_file=dict(type='str', default=None),
        timeout=dict(type='int', default=DEFAULT_TIMEOUT),
    )

    result = dict(
        changed=False,
    )

    module = AnsibleModule(
        argument_spec=argument_spec,
    )

    sdk, conn = openstack_cloud_from_module(module)
    src = server.Server.from_data(module.params['data'])
    params, info = src.params_and_info()

    # Required parameters
    destination_conversion_host_id = module.params['conversion_host']['id']
    ssh_key_path = module.params['ssh_key_path']
    ssh_user = module.params['ssh_user']
    transfer_uuid = module.params['transfer_uuid']
    volume_map = module.params['volume_map']

    # Optional parameters
    state_file = module.params.get('state_file', None)
    log_file = module.params.get('log_file', None)
    timeout = module.params['timeout']

    failure_cleanup = OpenStackDstFailureCleanup(
        conn,
        destination_conversion_host_id,
        ssh_key_path,
        ssh_user,
        transfer_uuid,
        volume_map,
        state_file=state_file,
        log_file=log_file,
        timeout=timeout,
    )
    failure_cleanup.delete_migrated_volumes()

    module.exit_json(**result)


def main():
    run_module()


if __name__ == '__main__':
    main()
