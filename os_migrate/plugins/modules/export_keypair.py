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
module: export_keypair

short_description: Export OpenStack Nova Keypair

extends_documentation_fragment: openstack

version_added: "2.9"

author: "OpenStack tenant migration tools (@os-migrate)"

description:
  - "Export OpenStack Nova Keypair definition into an OS-Migrate YAML"

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
      - Resources YAML file to where keypair will be serialized.
      - In case the resource file already exists, it must match the
        os-migrate version.
      - In case the resource of same type and name exists in the file,
        it will be replaced.
    required: true
    type: str
  name:
    description:
      - Name (or ID) of a Nova Keypair to export.
    required: true
    type: str
  user_id:
    description:
      - ID of the owner of the Keypair, if the owner is different
        than the authenticated user (admin-only feature).
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
'''

EXAMPLES = '''
- name: Export my_keypair into /opt/os-migrate/keypairs.yml
  os_migrate.os_migrate.export_keypair:
    cloud: source_cloud
    path: /opt/os-migrate/keypairs.yml
    name: my_keypair
'''

RETURN = '''
'''

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.openstack \
    import openstack_full_argument_spec, openstack_cloud_from_module

from ansible_collections.os_migrate.os_migrate.plugins.module_utils import filesystem
from ansible_collections.os_migrate.os_migrate.plugins.module_utils import keypair


def run_module():
    argument_spec = openstack_full_argument_spec(
        path=dict(type='str', required=True),
        name=dict(type='str', required=True),
        user_id=dict(type='str', required=False, default=None),
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
    filters = {
        'ignore_missing': False,
    }
    if module.params['user_id'] is not None:
        filters['user_id'] = module.params['user_id']
    sdk_keypair = conn.compute.find_keypair(module.params['name'], **filters)
    data = keypair.Keypair.from_sdk(conn, sdk_keypair)

    result['changed'] = filesystem.write_or_replace_resource(
        module.params['path'], data)

    module.exit_json(**result)


def main():
    run_module()


if __name__ == '__main__':
    main()
