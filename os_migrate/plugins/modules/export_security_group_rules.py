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
module: export_security_group_rules

short_description: Export OpenStack security group rules

extends_documentation_fragment: openstack

version_added: "2.9.0"

author: "OpenStack tenant migration tools (@os-migrate)"

description:
  - "Export an OpenStack security group rules definition into an OS-Migrate YAML"

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
  region_name:
    description:
      - OpenStack region name. Can be omitted if using default region.
    required: false
    type: str
  path:
    description:
      - Resources YAML file to where security groups will be serialized.
      - In case the resource file already exists, it must match the
        os-migrate version.
      - In case the resource of same type and name exists in the file,
        it will be replaced.
    required: true
    type: str
  name:
    description:
      - Name of the security group. OS-Migrate requires unique resource names.
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
- name: Export security groups into /opt/os-migrate/security_groups.yml
  os_migrate.os_migrate.export_security_group_rules:
    cloud: source_cloud
    path: /opt/os-migrate/security_groups.yml
    name: mysecgroup
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

from ansible_collections.os_migrate.os_migrate.plugins.module_utils import filesystem
from ansible_collections.os_migrate.os_migrate.plugins.module_utils import security_group_rule


def run_module():
    argument_spec = openstack_full_argument_spec(
        auth=dict(type='dict', no_log=True, required=True),
        path=dict(type='str', required=True),
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
    sdk_sec = conn.network.find_security_group(module.params['name'], ignore_missing=False)
    sdk_rules = conn.network.security_group_rules(security_group_id=sdk_sec['id'])

    result['changed'] = False

    for sdk_rule in sdk_rules:
        ser_rule = security_group_rule.SecurityGroupRule.from_sdk(conn, sdk_rule)

        rchanged = filesystem.write_or_replace_resource(module.params['path'], ser_rule)
        if rchanged:
            result['changed'] = True

    module.exit_json(**result)


def main():
    run_module()


if __name__ == '__main__':
    main()
