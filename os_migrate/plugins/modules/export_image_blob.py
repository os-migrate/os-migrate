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
module: export_image_blob

short_description: Export OpenStack image

extends_documentation_fragment: openstack

version_added: "2.9.0"

author: "OpenStack tenant migration tools (@os-migrate)"

description:
  - "Export OpenStack image definition into an OS-Migrate YAML"

options:
  auth:
    description:
      - Required if 'cloud' param not used.
    required: false
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
  blob_path:
    description:
      - Path where the image blob content will be saved.
      - In case the file already exists, it is assumed that the export was
        already performed and the module doesn't overwrite it.
    required: true
    type: str
  name:
    description:
      - Name (or ID) of a Image to export.
    required: true
    type: str
  availability_zone:
    description:
      - Availability zone.
    required: false
    type: str
  cloud:
    description:
      - Cloud resource from clouds.yml
      - Required if 'auth' param not used.
    required: false
    type: raw
'''

EXAMPLES = '''
- name: Export myimage into /opt/os-migrate/images.yml
  os_migrate.os_migrate.export_image_blob:
    path: /opt/os-migrate/image_blobs/myimage
    name: myimage
'''

RETURN = '''
'''

from ansible.module_utils.basic import AnsibleModule
# Import openstack module utils from ansible_collections.openstack.cloud.plugins as per ansible 3+
try:
    from ansible_collections.openstack.cloud.plugins.module_utils.openstack \
        import openstack_full_argument_spec, openstack_cloud_from_module
except ImportError:
    # If this fails fall back to ansible < 3 imports
    from ansible.module_utils.openstack \
        import openstack_full_argument_spec, openstack_cloud_from_module

from ansible_collections.os_migrate.os_migrate.plugins.module_utils import image


def run_module():
    argument_spec = openstack_full_argument_spec(
        blob_path=dict(type='str', required=True),
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
    sdk_image = conn.image.find_image(module.params['name'], ignore_missing=False)
    result['changed'] = image.export_blob(conn, sdk_image, module.params['blob_path'])

    module.exit_json(**result)


def main():
    run_module()


if __name__ == '__main__':
    main()
