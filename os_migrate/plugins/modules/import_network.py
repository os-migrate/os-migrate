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
module: import_network

short_description: Import OpenStack network

extends_documentation_fragment: openstack

version_added: "2.9"

author: "OpenStack tenant migration tools (@os-migrate)"

description:
  - "Import OpenStack network from an OS-Migrate YAML structure"

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
  data:
    description:
      - Data structure with network parameters as loaded from OS-Migrate YAML file.
    required: true
    type: dict
  filters:
    description:
      - Options for filtering existing resources to be looked up, e.g. by project.
    required: true
    type: dict
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

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.openstack \
    import openstack_full_argument_spec, openstack_cloud_from_module

from ansible_collections.os_migrate.os_migrate.plugins.module_utils import network


def run_module():
    argument_spec = openstack_full_argument_spec(
        data=dict(type='dict', required=True),
        filters=dict(type='dict', required=False, default={}),
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
    net = network.Network.from_data(module.params['data'])
    result['changed'] = net.create_or_update(conn, module.params['filters'])

    module.exit_json(**result)


def main():
    run_module()


if __name__ == '__main__':
    main()
