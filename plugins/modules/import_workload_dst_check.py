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
module: import_workload_dst_check

short_description: Export OpenStack instance information

extends_documentation_fragment:
  - os_migrate.os_migrate.openstack

version_added: "2.9.0"

author: "OpenStack tenant migration tools (@os-migrate)"

description:
  - "Check OpenStack workload in source cloud"

options:
  auth:
    description:
      - Required if 'cloud' param not used
    required: false
    type: dict
  auth_type:
    description:
      - Auth type plugin for OpenStack. Can be omitted if using password authentication.
    required: false
    type: str
  validate_certs:
    description:
      - Validate HTTPS certificates when logging in to OpenStack.
    required: false
    type: bool
  region_name:
    description:
      - OpenStack region name. Can be omitted if using default region.
    required: false
    type: str
  data:
    description:
      - Data structure with server parameters as loaded from OS-Migrate workloads YAML file.
    required: true
    type: dict
  dst_filters:
    description:
      - Options for filtering the migration idempotence lookup, e.g. by project.
    required: false
    type: dict
    default: {}
  cloud:
    description:
      - Cloud resource from clouds.yml
      - Required if 'auth' param not used.
    required: false
    type: raw
"""

EXAMPLES = r"""
- name: ensure workload in source cloud is ready to continue
  os_migrate.os_migrate.import_workload_dst_check:
    auth: "{{ os_migrate_src_auth }}"
    auth_type: "{{ os_migrate_src_auth_type|default(omit) }}"
    region_name: "{{ os_migrate_src_region_name|default(omit) }}"
    validate_certs: "{{ os_migrate_src_validate_certs|default(omit) }}"
    ca_cert: "{{ os_migrate_src_ca_cert|default(omit) }}"
    client_cert: "{{ os_migrate_src_client_cert|default(omit) }}"
    client_key: "{{ os_migrate_src_client_key|default(omit) }}"
    data: {
        # ...
    }
  when: prelim.changed
"""

RETURN = r"""
"""

from ansible.module_utils.basic import AnsibleModule

# Import openstack module utils from ansible_collections.openstack.cloud.plugins as per ansible 3+
HAS_OPENSTACK_CLOUD = False
try:
    from ansible_collections.openstack.cloud.plugins.module_utils.openstack import (
        openstack_full_argument_spec,
        openstack_cloud_from_module,
    )
    HAS_OPENSTACK_CLOUD = True
except ImportError:
    try:
        # If this fails fall back to ansible < 3 imports
        from ansible.module_utils.openstack import (
            openstack_full_argument_spec,
            openstack_cloud_from_module,
        )
        HAS_OPENSTACK_CLOUD = True
    except ImportError:
        # Create stub functions for sanity testing
        HAS_OPENSTACK_CLOUD = False

        def openstack_full_argument_spec(**kwargs):
            spec = dict(
                cloud=dict(type='raw'),
                auth=dict(type='dict'),
                auth_type=dict(type='str'),
                region_name=dict(type='str'),
                wait=dict(type='bool', default=True),
                timeout=dict(type='int', default=180),
                api_timeout=dict(type='int'),
                validate_certs=dict(type='bool', aliases=['verify']),
                ca_cert=dict(type='str', aliases=['cacert']),
                client_cert=dict(type='str', aliases=['cert']),
                client_key=dict(type='str', aliases=['key'], no_log=True),
                interface=dict(type='str', choices=['admin', 'internal', 'public'], default='public', aliases=['endpoint_type']),
                sdk_log_path=dict(type='str'),
                sdk_log_level=dict(type='str', default='INFO', choices=['INFO', 'DEBUG']),
            )
            spec.update(kwargs)
            return spec

        def openstack_cloud_from_module(module):
            return None, None

from ansible_collections.os_migrate.os_migrate.plugins.module_utils import server


def run_module():
    argument_spec = openstack_full_argument_spec(
        data=dict(type="dict", required=True),
        dst_filters=dict(type="dict", required=False, default={}),
    )

    result = dict(
        changed=False,
    )

    module = AnsibleModule(
        argument_spec=argument_spec,
        # TODO: Consider check mode. We'd fetch the resource and check
        # if the file representation matches it.
        # supports_check_mode=True,
    )

    if not HAS_OPENSTACK_CLOUD:
        module.fail_json(msg='openstack.cloud collection is required for this module')

    sdk, conn = openstack_cloud_from_module(module)
    ser_server = server.Server.from_data(module.params["data"])
    errors = ser_server.dst_prerequisites_errors(conn, module.params["dst_filters"])

    if errors:
        error_msg = " ".join(errors)
        module.fail_json(msg=error_msg, **result)

    module.exit_json(**result)


def main():
    run_module()


if __name__ == "__main__":
    main()
