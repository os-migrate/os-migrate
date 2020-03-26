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
module: os_migrate.os_migrate.import_security_group_rule
short_description: Import OpenStack security group rule
version_added: "2.9"
description:
  - "Import OpenStack security group from an OS-Migrate YAML structure"
options:
  cloud:
    description:
      - Named cloud to operate against.
    required: true
  data:
    description:
      - Data structure with the security group rule parameters as loaded from OS-Migrate YAML file.
    required: true
'''

EXAMPLES = '''
- name: Import mysecgrouprule into /opt/os-migrate/security_group_rule.yml
  os_migrate.os_migrate.import_security_group_rule:
    cloud: source_cloud
    data:
      - type: openstack.security_group_rule
        params:
          name: my_secgrouprule
'''

RETURN = '''
'''

import openstack
from ansible.module_utils.basic import AnsibleModule

from ansible_collections.os_migrate.os_migrate.plugins.module_utils import security_group_rule


def run_module():
    module_args = dict(
        cloud=dict(type='str', required=True),
        data=dict(type='dict', required=True),
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
    ser_secrule = module.params['data']
    secrule_refs = security_group_rule.security_group_rule_refs_from_ser(conn, ser_secrule)
    secrule_params = security_group_rule.security_group_rule_sdk_params(ser_secrule, secrule_refs)

    # The create security group rule method will return an exeption
    # If it's already created.
    try:
        conn.network.create_security_group_rule(**secrule_params)
        result['changed'] = True
    except openstack.exceptions.ConflictException:
        result['msg'] = "This security group rule already exists"

    module.exit_json(**result)


def main():
    run_module()


if __name__ == '__main__':
    main()
