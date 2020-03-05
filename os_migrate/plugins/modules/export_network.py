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
module: os_migrate.os_migrate.export_network

short_description: Export OpenStack network

version_added: "2.9"

description:
  - "Export OpenStack network definition into an OS-Migrate YAML"

options:
  cloud:
    description:
      - Named cloud to operate against.
    required: true
  path:
    description:
      - Resources YAML file to where network will be serialized.
      - In case the resource file already exists, it must match the
        os-migrate version.
      - In case the resource of same type and name exists in the file,
        it will be replaced.
    required: true
  name:
    description:
      - Name (or ID) of a Network to export.
    required: true
'''

EXAMPLES = '''
- name: Export mynetwork into /opt/os-migrate/networks.yml
  os_migrate.os_migrate.export_network:
    cloud: source_cloud
    path: /opt/os-migrate/networks.yml
    name: mynetwork
'''

RETURN = '''
'''

import openstack
from ansible.module_utils.basic import AnsibleModule

from ansible_collections.os_migrate.os_migrate.plugins.module_utils import filesystem
from ansible_collections.os_migrate.os_migrate.plugins.module_utils import network
from ansible_collections.os_migrate.os_migrate.plugins.module_utils import serialization


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
    sdk_net = conn.network.find_network(module.params['name'], ignore_missing=False)
    net = network.Network.from_sdk(conn, sdk_net)

    result['changed'] = filesystem.write_or_replace_resource(
        module.params['path'], net)

    module.exit_json(**result)


def main():
    run_module()


if __name__ == '__main__':
    main()
