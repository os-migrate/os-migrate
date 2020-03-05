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
module: os_migrate.os_migrate.export_router

short_description: Export OpenStack router

version_added: "2.9"

description:
  - "Export OpenStack router definition into an OS-Migrate YAML"

options:
  cloud:
    description:
      - Named cloud to operate against.
    required: true
  path:
    description:
      - Resources YAML file to where router will be serialized.
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
- name: Export myrouter into /opt/os-migrate/routers.yml
  os_migrate.os_migrate.export_router:
    cloud: source_cloud
    path: /opt/os-migrate/routers.yml
    name: myrouter
'''

RETURN = '''
'''

import openstack
from ansible.module_utils.basic import AnsibleModule

from ansible_collections.os_migrate.os_migrate.plugins.module_utils import filesystem
from ansible_collections.os_migrate.os_migrate.plugins.module_utils import router


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
    sdk_net = conn.network.find_router(module.params['name'], ignore_missing=False)
    net_refs = router.router_refs_from_sdk(conn, sdk_net)
    ser_net = router.serialize_router(sdk_net, net_refs)

    result['changed'] = filesystem.write_or_replace_resource(
        module.params['path'], ser_net)

    module.exit_json(**result)


def main():
    run_module()


if __name__ == '__main__':
    main()
