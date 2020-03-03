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
module: os_migrate.os_migrate.export_security_group_rules

short_description: Export OpenStack security group rules

version_added: "2.9"

description:
  - "Export an OpenStack security group rules definition into an OS-Migrate YAML"

options:
  cloud:
    description:
      - Named cloud to operate against.
    required: true
  path:
    description:
      - Resources YAML file to where security groups will be serialized.
      - In case the resource file already exists, it must match the
        os-migrate version.
      - In case the resource of same type and name exists in the file,
        it will be replaced.
    required: true
  name:
    description:
      - Name of the security group. OS-Migrate requires unique resource names.
    required: true
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

import openstack
from ansible.module_utils.basic import AnsibleModule

from ansible_collections.os_migrate.os_migrate.plugins.module_utils import filesystem
from ansible_collections.os_migrate.os_migrate.plugins.module_utils import network


def run_module():
    module_args = dict(
        cloud=dict(type='str', required=True),
        path=dict(type='str', required=True),
        name=dict(type='str', required=True),
    )

    result = dict(
        changed=False,
    )

    module = AnsibleModule(
        argument_spec=module_args,
        # TODO: Consider check mode. We'd fetch the resource and check
        # if the file representation matches it.
        # supports_check_mode=True,
    )

    conn = openstack.connect(cloud=module.params['cloud'])
    sdk_sec = conn.network.find_security_group(module.params['name'], ignore_missing=False)

    for rule in sdk_sec['security_group_rules']:
        # In this particular case we are creating a SecurityGroupRule
        # object parsed from the rule dictionary.
        # We check that serialize_security_group_rule receives
        # a openstack.network.v2.security_group_rule.SecurityGroupRule
        sec_rule_obj = openstack.network.v2.security_group_rule.SecurityGroupRule(**rule)
        sec_refs = network.security_group_rule_refs_from_sdk(conn, sec_rule_obj)
        ser_sec = network.serialize_security_group_rule(sec_rule_obj, sec_refs)

    result['changed'] = filesystem.write_or_replace_resource(
        module.params['path'], ser_sec)

    module.exit_json(**result)


def main():
    run_module()


if __name__ == '__main__':
    main()
