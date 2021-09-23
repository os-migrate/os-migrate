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
module: import_workload_src_check

short_description: Export OpenStack instance information

extends_documentation_fragment: openstack

version_added: "2.9"

author: "OpenStack tenant migration tools (@os-migrate)"

description:
  - "Check OpenStack workload in source cloud"

options:
  auth:
    description:
      - Dictionary with parameters for chosen auth type.
    required: true
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
  name:
    description:
      - Name (or ID) of an instance to check.
    required: true
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
'''

EXAMPLES = '''
- name: ensure workload in source cloud is ready to continue
  os_migrate.os_migrate.import_workload_src_check:
    auth: "{{ os_migrate_src_auth }}"
    auth_type: "{{ os_migrate_src_auth_type|default(omit) }}"
    region_name: "{{ os_migrate_src_region_name|default(omit) }}"
    validate_certs: "{{ os_migrate_src_validate_certs|default(omit) }}"
    ca_cert: "{{ os_migrate_src_ca_cert|default(omit) }}"
    client_cert: "{{ os_migrate_src_client_cert|default(omit) }}"
    client_key: "{{ os_migrate_src_client_key|default(omit) }}"
    name: migration-vm
  when: prelim.changed
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


def run_module():
    argument_spec = openstack_full_argument_spec(
        name=dict(type='str', required=True),
    )
    # TODO: check the del
    # del argument_spec['cloud']

    result = dict(
        changed=False,
    )

    module = AnsibleModule(
        argument_spec=argument_spec,
        # TODO: Consider check mode. We'd fetch the resource and check
        # if the file representation matches it.
        # supports_check_mode=True,
    )

    sdk, conn = openstack_cloud_from_module(module)
    sdk_server_nodetails = conn.compute.find_server(module.params['name'], ignore_missing=False)
    sdk_server = conn.compute.get_server(sdk_server_nodetails['id'])
    srv = server.Server.from_sdk(conn, sdk_server)
    params, info = srv.params_and_info()
    result['server_name'] = params['name']

    # Checks
    # below this area add a block for each check required on a source workload
    # prior to migration.  If the check fails, exit the module with a
    # descriptive message of why the check failed.

    # Status Check
    #: The state this server is in. Valid values include ``ACTIVE``,
    #: ``BUILDING``, ``DELETED``, ``ERROR``, ``HARD_REBOOT``, ``PASSWORD``,
    #: ``PAUSED``, ``REBOOT``, ``REBUILD``, ``RESCUED``, ``RESIZED``,
    #: ``REVERT_RESIZE``, ``SHUTOFF``, ``SOFT_DELETED``, ``STOPPED``,
    #: ``SUSPENDED``, ``UNKNOWN``, or ``VERIFY_RESIZE``.
    # Make sure source instance is shutdown before proceeding.
    if info['status'] != 'SHUTOFF':
        msg = "Cannot migrate instance {} because it is not in state SHUTOFF! Currently in state {}."
        module.fail_json(msg=msg.format(params['name'], info['status']), **result)

    module.exit_json(**result)


def main():
    run_module()


if __name__ == '__main__':
    main()
