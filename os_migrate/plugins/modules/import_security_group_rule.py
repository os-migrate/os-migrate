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
  auth:
    description:
      - Dictionary with parameters for chosen auth type.
    required: true
  auth_type:
    description:
      - Auth type plugin for OpenStack. Can be omitted if using password authentication.
    required: false
  region_name:
    description:
      - OpenStack region name. Can be omitted if using default region.
    required: false

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

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.openstack \
    import openstack_full_argument_spec, openstack_cloud_from_module

from ansible_collections.os_migrate.os_migrate.plugins.module_utils import security_group_rule


def run_module():
    argument_spec = openstack_full_argument_spec(
        data=dict(type='dict', required=True),
    )
    del argument_spec['cloud']

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
    ser_secrule = module.params['data']
    secrule_refs = security_group_rule.security_group_rule_refs_from_ser(conn, ser_secrule)
    secrule_params = security_group_rule.security_group_rule_sdk_params(ser_secrule, secrule_refs)

    # The create security group rule method will return an exeption
    # If it's already created.
    try:
        conn.network.create_security_group_rule(**secrule_params)
        result['changed'] = True
    except sdk.exceptions.ConflictException:
        result['msg'] = "This security group rule already exists"

    module.exit_json(**result)


def main():
    run_module()


if __name__ == '__main__':
    main()
