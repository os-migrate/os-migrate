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
module: os_migrate.os_migrate.import_router

short_description: Import OpenStack router

version_added: "2.9"

description:
  - "Import OpenStack router from an OS-Migrate YAML structure"

options:
  cloud:
    description:
      - Named cloud to operate against.
    required: true
  data:
    description:
      - Data structure with router parameters as loaded from OS-Migrate YAML file.
    required: true
'''

EXAMPLES = '''
- name: Import myrouter into /opt/os-migrate/routers.yml
  os_migrate.os_migrate.import_router:
    cloud: source_cloud
    data:
      - type: openstack.router
        params:
          name: my_rtr
'''

RETURN = '''
'''

import openstack
from ansible.module_utils.basic import AnsibleModule

from ansible_collections.os_migrate.os_migrate.plugins.module_utils import router


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
    rtr = router.Router.from_data(module.params['data'])
    result['changed'] = rtr.create_or_update(conn)

    module.exit_json(**result)


def main():
    run_module()


if __name__ == '__main__':
    main()
