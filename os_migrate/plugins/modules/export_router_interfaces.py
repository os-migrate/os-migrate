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
module: export_router_interfaces

short_description: Export OpenStack router interfaces

extends_documentation_fragment: openstack

version_added: "2.9"

author: "OpenStack tenant migration tools (@os-migrate)"

description:
  - "Export OpenStack router interfaces definition into an OS-Migrate YAML"

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
      - Resources YAML file to where router interfaces will be serialized.
      - In case the resource file already exists, it must match the
        os-migrate version.
      - In case the resource of same type and name exists in the file,
        it will be replaced.
    required: true
    type: str
  name:
    description:
      - Name (or ID) of a Router to export.
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
- name: Export myrouter interfaces into /opt/os-migrate/router_interfaces.yml
  os_migrate.os_migrate.export_router_interfaces:
    cloud: source_cloud
    path: /opt/os-migrate/router_interfaces.yml
    name: myrouter
'''

RETURN = '''
'''

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.openstack \
    import openstack_full_argument_spec, openstack_cloud_from_module

from ansible_collections.os_migrate.os_migrate.plugins.module_utils \
    import filesystem, router_interface


def run_module():
    argument_spec = openstack_full_argument_spec(
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
    sdk_rtr = conn.network.find_router(module.params['name'], ignore_missing=False)
    sdk_ports = router_interface.router_interfaces(conn, sdk_rtr)
    ifaces = map(lambda port: router_interface.RouterInterface.from_sdk(conn, port),
                 sdk_ports)

    for iface in list(ifaces):
        if filesystem.write_or_replace_resource(module.params['path'], iface):
            result['changed'] = True

    module.exit_json(**result)


def main():
    run_module()


if __name__ == '__main__':
    main()
