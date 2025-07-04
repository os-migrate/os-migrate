#!/usr/bin/python


from __future__ import absolute_import, division, print_function

__metaclass__ = type

ANSIBLE_METADATA = {
    "metadata_version": "1.1",
    "status": ["preview"],
    "supported_by": "community",
}

DOCUMENTATION = r"""
---
module: import_image

short_description: Import OpenStack image

extends_documentation_fragment:
  - os_migrate.os_migrate.openstack

version_added: "2.9.0"

author: "OpenStack tenant migration tools (@os-migrate)"

description:
  - "Import OpenStack image from an OS-Migrate YAML structure"

options:
  auth:
    description:
      - Required if 'cloud' param is not used.
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
  data:
    description:
      - Data structure with image parameters as loaded from OS-Migrate YAML file.
    required: true
    type: dict
  filters:
    description:
      - Options for filtering existing resources to be looked up, e.g. by project.
    required: false
    type: dict
  blob_path:
    description:
      - Path where the image blob content will be saved.
      - In case the file already exists, it is assumed that the export was
        already performed and the module doesn't overwrite it.
    required: true
    type: str
  availability_zone:
    description:
      - Availability zone.
    required: false
    type: str
  cloud:
    description:
      - Cloud from clouds.yaml to use.
      - Required if 'auth' parameter is not used.
    required: false
    type: raw
"""

EXAMPLES = r"""
- name: Import myimage into /opt/os-migrate/images.yml
  os_migrate.os_migrate.import_image:
    auth: {}
    data:
      - type: openstack.image.Image
        params:
          name: my_image
    blob_path: /path/to/image_blob
"""

RETURN = r"""
"""

from ansible.module_utils.basic import AnsibleModule

# Import openstack module utils from ansible_collections.openstack.cloud.plugins as per ansible 3+
try:
    from ansible_collections.openstack.cloud.plugins.module_utils.openstack import (
        openstack_full_argument_spec,
        openstack_cloud_from_module,
    )
except ImportError:
    # If this fails fall back to ansible < 3 imports
    from ansible.module_utils.openstack import (
        openstack_full_argument_spec,
        openstack_cloud_from_module,
    )

from ansible_collections.os_migrate.os_migrate.plugins.module_utils import image


def run_module():
    argument_spec = openstack_full_argument_spec(
        data=dict(type="dict", required=True),
        blob_path=dict(type="str", required=True),
        filters=dict(type="dict", required=False, default={}),
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
    ser_img = image.Image.from_data(module.params["data"])
    result["changed"] = ser_img.create_or_update(
        conn, module.params["filters"], module.params["blob_path"]
    )

    module.exit_json(**result)


def main():
    run_module()


if __name__ == "__main__":
    main()
