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
module: os_migrate.os_migrate.export_router_interfaces

short_description: Export OpenStack router interfaces

version_added: "2.9"

description:
  - "Export OpenStack router interfaces definition into an OS-Migrate YAML"

options:
  cloud:
    description:
      - Named cloud to operate against.
    required: true
  path:
    description:
      - Resources YAML file to where router interfaces will be serialized.
      - In case the resource file already exists, it must match the
        os-migrate version.
      - In case the resource of same type and name exists in the file,
        it will be replaced.
    required: true
  name:
    description:
      - Name (or ID) of a Router to export.
    required: true
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

import openstack
from ansible.module_utils.basic import AnsibleModule

from ansible_collections.os_migrate.os_migrate.plugins.module_utils \
    import filesystem, router_interface


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
