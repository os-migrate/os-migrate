#!/usr/bin/python

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
  dir:
    description:
      - Directory where the network YAML file will be created.
      - The name of the created file will be network-<name>.yml.
  name:
    description:
      - Name of the network to export. OS-Migrate requires unique resource names.
    required: true
'''

EXAMPLES = '''
- name: Export mynetwork into /opt/os-migrate/network-mynetwork.yml
  os_migrate.os_migrate.export_network:
    cloud: source_cloud
    dir: /opt/os-migrate
    name: mynetwork
'''

RETURN = '''
'''

from os import path

from ansible_collections.os_migrate.os_migrate.plugins.module_utils import const
from ansible.module_utils.basic import AnsibleModule

def run_module():
    module_args = dict(
        cloud=dict(type='str', required=True),
        dir=dict(type='str', required=True),
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

    result['file_path'] = path.join(
        module.params['dir'],
        "{}{}.yml".format(const.FILE_PREFIX_NETWORK, module.params['name']))
    result['msg'] = (
        "I should export network '{}' into file '{}' "
        "but right now i do nothing!".format(
            module.params['name'],
            result['file_path'],
        )
    )

    module.exit_json(**result)

def main():
    run_module()

if __name__ == '__main__':
    main()
