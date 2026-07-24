#!/usr/bin/python


from __future__ import absolute_import, division, print_function

__metaclass__ = type

ANSIBLE_METADATA = {
    "metadata_version": "1.1",
    "status": ["preview"],
    "supported_by": "community",
}

DOCUMENTATION = r"""
---
module: import_workload_prelim

short_description: Preliminary actions required to import an OpenStack instance

extends_documentation_fragment:
  - os_migrate.os_migrate.openstack

version_added: "2.9.0"

author: "OpenStack tenant migration tools (@os-migrate)"

description:
  - "This module communicates with the OpenStack API and sets up variables for the rest of the import_workload_* modules."

options:
  auth:
    description:
      - Required if 'cloud' param not used
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
  validate_certs:
    description:
      - Validate HTTPS certificates when logging in to OpenStack.
    required: false
    type: bool
  dst_filters:
    description:
      - Options for filtering the migration idempotence lookup, e.g. by project.
    required: false
    type: dict
    default: {}
  src_conversion_host:
    description:
      - Dictionary with information about the source conversion host (address, status, name, id)
    required: true
    type: dict
  data:
    description:
      - Data structure with server parameters as loaded from OS-Migrate workloads YAML file.
    required: true
    type: dict
  log_dir:
    description:
      - Directory for storing log and state files.
    required: false
    type: str
  cloud:
    description:
      - Cloud resource from clouds.yml
      - Required if 'auth' param not used
    required: false
    type: raw
"""

EXAMPLES = r"""
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

  - name: preliminary setup for workload import
    os_migrate.os_migrate.import_workload_prelim:
      auth: "{{ os_migrate_dst_auth }}"
      auth_type: "{{ os_migrate_dst_auth_type | default(omit) }}"
      region_name: "{{ os_migrate_dst_region_name | default(omit) }}"
      validate_certs: "{{ os_migrate_dst_validate_certs | default(omit) }}"
      src_conversion_host: "{{ os_src_conversion_host_info.openstack_conversion_host }}"
      src_auth: "{{ os_migrate_src_auth }}"
      src_auth_type: "{{ os_migrate_src_auth_type | default(omit) }}"
      src_region_name: "{{ os_migrate_src_region_name | default(omit) }}"
      src_validate_certs: "{{ os_migrate_src_validate_certs | default(omit) }}"
      data: "{{ item }}"
      log_dir: "{{ os_migrate_data_dir }}/workload_logs"
    register: prelim
"""

RETURN = r"""
server_name:
  description: The name of the target instance from params, as a convenience.
  returned: Only after successful connection to destination cloud.
  type: str
  sample: migration-vm
log_file:
  description: Local log file for workload migration.
  returned: Only on success.
  type: str
  sample: lab-migration-data/migration-vm.log
state_file:
  description: Local file containing disk transfer progress.
  returned: Only on success.
  type: str
  sample: lab-migration-data/migration-vm.state
"""

from ansible.module_utils.basic import AnsibleModule

from ansible_collections.os_migrate.os_migrate.plugins.module_utils import os_auth
from ansible_collections.os_migrate.os_migrate.plugins.module_utils import server

import os


def is_source_conversion_host(server_id, conversion_host_id):
    """True when the workload being migrated is the conversion host itself."""
    return server_id == conversion_host_id


def destination_server_exists(existing_count):
    """True when destination already has a server with the same name."""
    return existing_count > 0


def migration_log_paths(log_dir, server_name):
    """Build log and state file paths for a migrating server."""
    return {
        "log_file": os.path.join(log_dir, server_name) + ".log",
        "state_file": os.path.join(log_dir, server_name) + ".state",
    }


def run_module():
    argument_spec = os_auth.openstack_full_argument_spec(
        dst_filters=dict(type="dict", required=False, default={}),
        src_conversion_host=dict(type="dict", required=True),
        data=dict(type="dict", required=True),
        log_dir=dict(type="str", default=None),
    )

    result = dict(
        changed=False,
    )

    module = AnsibleModule(
        argument_spec=argument_spec,
    )

    conn = os_auth.get_connection(module)
    src = server.Server.from_data(module.params["data"])
    params, info = src.params_and_info()

    server_name = params["name"]
    result["server_name"] = server_name
    log_dir = module.params["log_dir"]

    # Do not convert source conversion host!
    if is_source_conversion_host(info["id"], module.params["src_conversion_host"]["id"]):
        module.exit_json(
            skipped=True, skip_reason="Skipping conversion host.", **result
        )

    # Assume an existing VM with the same name means it was already migrated.
    # With Nova, the 'name' parameter for list request is a regular expression.
    server_name_regex = f"^{server_name}$"
    existing = list(
        conn.compute.servers(
            details=False,
            name=server_name_regex,
            **module.params["dst_filters"],
        )
    )
    if destination_server_exists(len(existing)):
        module.exit_json(
            msg=f"VM '{server_name}' already exists on destination, skipping.", **result
        )

    paths = migration_log_paths(log_dir, server_name)
    result["log_file"] = paths["log_file"]
    result["state_file"] = paths["state_file"]
    result["changed"] = True

    module.exit_json(**result)


def main():
    run_module()


if __name__ == "__main__":
    main()
