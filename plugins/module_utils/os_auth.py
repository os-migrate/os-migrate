from __future__ import absolute_import, division, print_function
__metaclass__ = type

import openstack

def openstack_full_argument_spec(**kwargs):
    """Standard OpenStack arguments with alias handling"""
    spec = dict(
        cloud=dict(type='str', required=False),
        auth=dict(type='dict', required=False, no_log=True),
        region_name=dict(type='str', required=False),
        auth_type=dict(type='str', required=False),
        # Accept both for backward compatibility
        verify=dict(type='bool', required=False),
        validate_certs=dict(type='bool', required=False),
    )
    spec.update(kwargs)
    return spec

def get_connection(module):
    """Create and return an OpenStack SDK connection from module params"""
    params = module.params
    cloud = module.params.get("cloud")
    auth = module.params.get("auth")
    region = module.params.get("region_name")
    # Handle the 'validate_certs' vs 'verify' logic
    # If verify is set, use it. If not, look for validate_certs. 
    # Default to True if neither are provided.
    verify = params.get("verify")
    if verify is None:
        verify = params.get("validate_certs", True)

    try:
        # If 'cloud' is a dictionary, it's already a config object
        if isinstance(cloud, dict):
            return openstack.connect(**cloud)

        # If 'cloud' is a string, it's a name in clouds.yaml
        if isinstance(cloud, str):
            return openstack.connect(
                cloud=cloud, 
                region_name=region, 
                verify=verify,
            )
        
        # If no cloud, use explicit auth dict
        if auth:
            return openstack.connection.Connection(
                auth=auth,
                region_name=region,
                verify=verify,
            )

        module.fail_json(msg="Either 'cloud' (name or dict) or 'auth' must be provided")

    except Exception as e:
        module.fail_json(msg=f"Failed to create OpenStack connection: {str(e)}")