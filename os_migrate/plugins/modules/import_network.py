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
module: os_migrate.os_migrate.import_network

short_description: Import OpenStack network

version_added: "2.9"

description:
  - "Import OpenStack network from an OS-Migrate YAML structure"

options:
  cloud:
    description:
      - Named cloud to operate against.
    required: true
  data:
    description:
      - Data structure with network parameters as loaded from OS-Migrate YAML file.
    required: true
'''

EXAMPLES = '''
- name: Import mynetwork into /opt/os-migrate/networks.yml
  os_migrate.os_migrate.import_network:
    cloud: source_cloud
    data:
      - type: openstack.network
        params:
          name: my_net
'''

RETURN = '''
'''

import openstack
from ansible.module_utils.basic import AnsibleModule

from ansible_collections.os_migrate.os_migrate.plugins.module_utils import network


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
    net_params = network.network_sdk_params(module.params['data'])
    existing_network = conn.network.find_network(net_params['name'])
    if existing_network:
        if network.network_needs_update(
                existing_network, module.params['data']):
            conn.network.update_network(net_params['name'], **net_params)
            result['changed'] = True
        # else: pass -- nothing to update
    else:
        conn.network.create_network(**net_params)
        result['changed'] = True

    module.exit_json(**result)


def main():
    run_module()


if __name__ == '__main__':
    main()
