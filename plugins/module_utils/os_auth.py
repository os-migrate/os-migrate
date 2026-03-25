from __future__ import absolute_import, division, print_function
__metaclass__ = type

import openstack

def openstack_full_argument_spec(**kwargs):
    """Standard OpenStack arguments for all modules"""
    spec = dict(
        cloud=dict(type='str', required=False),
        auth=dict(type='dict', required=False, no_log=True),
        region_name=dict(type='str', required=False),
        auth_type=dict(type='str', required=False),
        verify=dict(type='bool', required=False, default=True),
    )
    spec.update(kwargs)
    return spec

def get_connection(module):
    """Create and return an OpenStack SDK connection from module params"""
    cloud = module.params.get("cloud")
    auth = module.params.get("auth")
    region = module.params.get("region_name")
    verify = module.params.get("verify")

    try:
        # If 'cloud' is provided, we use openstack.connect to read clouds.yaml
        if cloud:
            return openstack.connect(cloud=cloud, region_name=region, verify=verify)
        
        # Otherwise, we use the explicit 'auth' dictionary
        if not auth:
            module.fail_json(msg="Either 'cloud' or 'auth' must be provided")

        return openstack.connection.Connection(
            auth=auth,
            region_name=region,
            verify=verify,
        )

    except Exception as e:
        module.fail_json(msg=f"Failed to create OpenStack connection: {str(e)}")