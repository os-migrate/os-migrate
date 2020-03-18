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
module: import_router_interface

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
- name: Import router interface
  os_migrate.os_migrate.import_router_interface:
    cloud: source_cloud
    data:
      params:
        fixed_ips_names:
        - ip_address: 192.168.0.10
          subnet_name: osm_subnet
        router_name: osm_router
      type: openstack.network.RouterInterface
'''

RETURN = '''
'''

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.openstack \
    import openstack_full_argument_spec, openstack_cloud_from_module

from ansible_collections.os_migrate.os_migrate.plugins.module_utils \
    import router_interface


def run_module():
    argument_spec = openstack_full_argument_spec(
        data=dict(type='dict', required=True),
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
    iface = router_interface.RouterInterface.from_data(module.params['data'])
    result['changed'] = iface.create_or_update(conn)

    module.exit_json(**result)


def main():
    run_module()


if __name__ == '__main__':
    main()
