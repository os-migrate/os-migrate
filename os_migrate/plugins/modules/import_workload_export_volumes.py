#!/usr/bin/python

from __future__ import absolute_import, division, print_function

__metaclass__ = type

ANSIBLE_METADATA = {
    "metadata_version": "1.1",
    "status": ["preview"],
    "supported_by": "community",
}

DOCUMENTATION = """
---
module: import_workload_export_volumes

short_description: Create NBD exports of OpenStack volumes

extends_documentation_fragment: openstack

version_added: "2.9.0"

author: "OpenStack tenant migration tools (@os-migrate)"

description:
  - "Take an instance from an OS-Migrate YAML structure, and export its volumes over NBD."

options:
  auth:
    description:
      - Required if 'cloud' param not used.
    required: false
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
      - Cloud resource from clouds.yml
      - Required if 'auth' param not used
    required: false
    type: raw
  validate_certs:
    description:
      - Validate HTTPS certificates when logging in to OpenStack.
    required: false
    type: bool
  boot_volume_prefix:
    description:
      - Name prefix to apply when server boot volume copies are created.
    required: false
    type: str
  conversion_host:
    description:
      - Dictionary with information about the source conversion host (address, status, name, id)
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
  src_conversion_host_address:
    description:
      - Optional IP address of the source conversion host. Without this, the
        plugin will use the 'access_ipv4' property of the conversion host instance.
    required: false
    type: str
  ssh_key_path:
    description:
      - Path to an SSH private key authorized on the source cloud.
    required: true
    type: str
  ssh_user:
    description:
      - The SSH user to connect to the conversion hosts.
    required: true
    type: str
  timeout:
    description:
      - Timeout for long running operations, in seconds.
    required: false
    default: 1800
    type: int
"""

EXAMPLES = """
main.yml:

- name: validate loaded resources
  os_migrate.os_migrate.validate_resource_files:
    paths:
      - "{{ os_migrate_data_dir }}/workloads.yml"
  register: workloads_file_validation
  when: import_workloads_validate_file

- name: read workloads resource file
  os_migrate.os_migrate.read_resources:
    path: "{{ os_migrate_data_dir }}/workloads.yml"
  register: read_workloads

- name: get source conversion host address
  os_migrate.os_migrate.os_conversion_host_info:
    auth:
        auth_url: https://src-osp:13000/v3
        username: migrate
        password: migrate
        project_domain_id: default
        project_name: migration-source
        user_domain_id: default
    server_id: ce4dda96-5d8e-4b67-aee2-9845cdc943fe
  register: os_src_conversion_host_info

- name: get destination conversion host address
  os_migrate.os_migrate.os_conversion_host_info:
    auth:
        auth_url: https://dest-osp:13000/v3
        username: migrate
        password: migrate
        project_domain_id: default
        project_name: migration-destination
        user_domain_id: default
    server_id: 2d2afe57-ace5-4187-8fca-5f10f9059ba1
  register: os_dst_conversion_host_info

- name: import workloads
  include_tasks: workload.yml
  loop: "{{ read_workloads.resources }}"



workload.yml:

- block:
  - name: preliminary setup for workload import
    os_migrate.os_migrate.import_workload_prelim:
      auth:
          auth_url: https://dest-osp:13000/v3
          username: migrate
          password: migrate
          project_domain_id: default
          project_name: migration-destination
          user_domain_id: default
      validate_certs: False
      src_conversion_host: "{{ os_src_conversion_host_info.openstack_conversion_host }}"
      src_auth:
          auth_url: https://src-osp:13000/v3
          username: migrate
          password: migrate
          project_domain_id: default
          project_name: migration-source
          user_domain_id: default
      src_validate_certs: False
      data: "{{ item }}"
      data_dir: "{{ os_migrate_data_dir }}"
    register: prelim

  - debug:
      msg:
        - "{{ prelim.server_name }} log file: {{ prelim.log_file }}"
        - "{{ prelim.server_name }} progress file: {{ prelim.state_file }}"
    when: prelim.changed

  - name: expose source volumes
    os_migrate.os_migrate.import_workload_export_volumes:
      auth: "{{ os_migrate_src_auth }}"
      auth_type: "{{ os_migrate_src_auth_type|default(omit) }}"
      region_name: "{{ os_migrate_src_region_name|default(omit) }}"
      validate_certs: "{{ os_migrate_src_validate_certs|default(omit) }}"
      ca_cert: "{{ os_migrate_src_ca_cert|default(omit) }}"
      client_cert: "{{ os_migrate_src_client_cert|default(omit) }}"
      client_key: "{{ os_migrate_src_client_key|default(omit) }}"
      conversion_host:
        "{{ os_src_conversion_host_info.openstack_conversion_host }}"
      data: "{{ item }}"
      log_file: "{{ os_migrate_data_dir }}/{{ prelim.server_name }}.log"
      state_file: "{{ os_migrate_data_dir }}/{{ prelim.server_name }}.state"
      ssh_key_path: "{{ os_migrate_conversion_keypair_private_path }}"
      ssh_user: "{{ os_migrate_conversion_host_ssh_user  }}"
    register: volume_map
    when: prelim.changed

  rescue:
    - fail:
        msg: "Failed to import {{ item.params.name }}!"
"""

RETURN = """
transfer_uuid:
  description: UUID to identify this transfer when needed
  returned: Only on success.
  type: str
  sample: 9b8a64b3-c976-4103-b34e-995e4ab9f57b
volume_map:
  description:
    - Mapping of source volume devices to NBD export URLs.
    - This structure only has source-related fields filled out.
  returned: Only after successfully moving volumes on source cloud.
  type: dict
  sample:
    "volume_map": {
          "/dev/vda": {
              "bootable": True,
              "dest_dev": null,
              "dest_id": null,
              "image_id": null,
              "name": "migration-vm-boot",
              "port": 49164,
              "progress": 0.0,
              "size": 10,
              "snap_id": "52aa3444-6d22-4348-8cc7-5146a1fb9762",
              "source_dev": "/dev/vdb",
              "source_id": "ac62dcda-181d-4491-aa40-de60aa5918f3",
              "url": "nbd://localhost:49164/f544092c-6bb8-4e3e-b509-d59b1520540d"
          }
     }
"""

from ansible.module_utils.basic import AnsibleModule

# Import openstack module utils from ansible_collections.openstack.cloud.plugins as per ansible 3+
try:
    from ansible_collections.openstack.cloud.plugins.module_utils.openstack import (
        openstack_full_argument_spec,
        openstack_cloud_from_module,
    )
except ImportError:
    # If this fails fall back to ansible < 3 imports
    from ansible.module_utils.openstack import (
        openstack_full_argument_spec,
        openstack_cloud_from_module,
    )

from ansible_collections.os_migrate.os_migrate.plugins.module_utils import server

from ansible_collections.os_migrate.os_migrate.plugins.module_utils.volume_common import (
    DEFAULT_TIMEOUT,
    OpenstackVolumeExport,
)

import uuid


class OpenStackSourceVolume(OpenstackVolumeExport):
    """Export volumes from an OpenStack instance over NBD."""

    def __init__(
        self,
        openstack_connection,
        source_conversion_host_id,
        ssh_key_path,
        ssh_user,
        source_instance_id,
        ser_server,
        state_file=None,
        log_file=None,
        source_conversion_host_address=None,
        boot_volume_prefix=None,
        timeout=DEFAULT_TIMEOUT,
    ):
        # UUID marker for child processes on conversion hosts.
        transfer_uuid = str(uuid.uuid4())

        super().__init__(
            openstack_connection,
            source_conversion_host_id,
            ssh_key_path,
            ssh_user,
            transfer_uuid,
            conversion_host_address=source_conversion_host_address,
            state_file=state_file,
            log_file=log_file,
            timeout=timeout,
        )

        # Required unique parameters:
        # source_instance_id: ID of VM to migrate from the source
        self.source_instance_id = source_instance_id

        # Optional parameters:
        # source_disks: (TODO) List of disks to migrate, otherwise all of them
        self.source_disks = None

        if boot_volume_prefix is not None:
            self.boot_volume_prefix = boot_volume_prefix
        else:
            self.boot_volume_prefix = "os-migrate-"

        # Build up a list of VolumeMappings keyed by the original device path
        # provided by the OpenStack API. Details:
        #   source_dev:  Device path (like /dev/vdb) on source conversion host
        #   source_id:   Volume ID on source cloud
        #   dest_dev:    Device path on destination conversion host
        #   dest_id:     Volume ID on destination cloud
        #   snap_id:     Root volumes need snapshot+new volume
        #   image_id:    Direct-from-image VMs create temporary snapshot image
        #   name:        Save volume name to set on destination
        #   size:        Volume size reported by OpenStack, in GB
        #   port:        Port used to listen for NBD connections to this volume
        #   url:         Final NBD export on destination conversion host
        #   progress:    Transfer progress percentage
        #   bootable:    Boolean flag for boot disks
        self.volume_map = {}

        self.ser_server = ser_server

    def prepare_exports(self):
        """
        Attach the source VM's volumes to the source conversion host, and start
        waiting for NBD connections.
        """
        self._test_source_vm_shutdown()
        self._get_root_and_data_volumes()
        self._validate_volumes_match_data()
        self._detach_data_volumes_from_source()
        self._attach_volumes_to_converter()
        self._export_volumes_from_converter()

    def _get_root_and_data_volumes(self):
        """
        Volume mapping step one: get the IDs and sizes of all volumes on the
        source VM. Key off the original device path to eventually preserve this
        order on the destination.
        """
        sourcevm = self._source_vm()
        for server_volume in sourcevm.volumes:
            volume = self.conn.get_volume_by_id(server_volume["id"])
            self.log.info("Inspecting volume: %s", volume["id"])
            if self.source_disks and volume["id"] not in self.source_disks:
                self.log.info("Volume is not in specified disk list, ignoring.")
                continue
            dev_path = self._get_attachment(volume, sourcevm)["device"]
            self.volume_map[dev_path] = dict(
                source_dev=None,
                source_id=volume["id"],
                dest_dev=None,
                dest_id=None,
                snap_id=None,
                image_id=None,
                name=volume["name"],
                size=volume["size"],
                port=None,
                url=None,
                progress=None,
                bootable=volume["bootable"],
            )
            self._update_progress(dev_path, 0.0)


def run_module():
    argument_spec = openstack_full_argument_spec(
        data=dict(type="dict", required=True),
        boot_volume_prefix=dict(type="str", default=None),
        conversion_host=dict(type="dict", required=True),
        ssh_key_path=dict(type="str", required=True),
        ssh_user=dict(type="str", required=True),
        src_conversion_host_address=dict(type="str", default=None),
        state_file=dict(type="str", default=None),
        log_file=dict(type="str", default=None),
        timeout=dict(type="int", default=DEFAULT_TIMEOUT),
    )

    result = dict(
        changed=False,
    )

    module = AnsibleModule(
        argument_spec=argument_spec,
    )

    sdk, conn = openstack_cloud_from_module(module)
    ser_server = server.Server.from_data(module.params["data"])
    params, info = ser_server.params_and_info()

    # Required parameters
    source_conversion_host_id = module.params["conversion_host"]["id"]
    ssh_key_path = module.params["ssh_key_path"]
    ssh_user = module.params["ssh_user"]
    source_instance_id = info["id"]

    # Optional parameters
    source_conversion_host_address = module.params.get(
        "src_conversion_host_address", None
    )
    state_file = module.params.get("state_file", None)
    log_file = module.params.get("log_file", None)
    boot_volume_prefix = module.params.get("boot_volume_prefix", None)
    timeout = module.params["timeout"]

    source_host = OpenStackSourceVolume(
        conn,
        source_conversion_host_id,
        ssh_key_path,
        ssh_user,
        source_instance_id,
        ser_server,
        source_conversion_host_address=source_conversion_host_address,
        state_file=state_file,
        log_file=log_file,
        boot_volume_prefix=boot_volume_prefix,
        timeout=timeout,
    )
    source_host.prepare_exports()
    result["transfer_uuid"] = source_host.transfer_uuid
    result["volume_map"] = source_host.volume_map

    module.exit_json(**result)


def main():
    run_module()


if __name__ == "__main__":
    main()
