from __future__ import absolute_import, division, print_function
__metaclass__ = type

import importlib

def openstack_full_argument_spec(**kwargs):
    """Refined argument spec based on official Ansible OpenStack modules"""
    spec = dict(
        cloud=dict(type='raw'),
        auth_type=dict(),
        auth=dict(type='dict', no_log=True),
        region_name=dict(),
        validate_certs=dict(type='bool', aliases=['verify']),
        ca_cert=dict(aliases=['cacert']),
        client_cert=dict(aliases=['cert']),
        client_key=dict(no_log=True, aliases=['key']),
        wait=dict(default=True, type='bool'),
        timeout=dict(default=180, type='int'),
        api_timeout=dict(type='int'),
        interface=dict(
            default='public', choices=['public', 'internal', 'admin'],
            aliases=['endpoint_type']),
    )
    spec.update(kwargs)
    return spec

def get_connection(module):
    """Establishes connection using official Ansible logic (Simplified)"""
    try:
        sdk = importlib.import_module('openstack')
    except ImportError:
        module.fail_json(msg='openstacksdk is required for this module')

    cloud_config = module.params.get('cloud')
    try:
        if isinstance(cloud_config, dict):
            # If cloud is a dict, other auth params must be None
            fail_message = (
                "A cloud config dict was provided to the cloud parameter"
                " but also a value was provided for {param}. If a cloud"
                " config dict is provided, {param} should be excluded.")
            for param in ('auth', 'region_name', 'validate_certs', 'ca_cert', 
                          'client_cert', 'client_key', 'api_timeout', 'auth_type'):
                if module.params.get(param) is not None:
                    module.fail_json(msg=fail_message.format(param=param))
            return sdk.connect(**cloud_config)
        else:
            return sdk.connect(
                cloud=cloud_config,
                auth_type=module.params.get('auth_type'),
                auth=module.params.get('auth'),
                region_name=module.params.get('region_name'),
                verify=module.params.get('validate_certs'),
                cacert=module.params.get('ca_cert'),
                key=module.params.get('client_key'),
                cert=module.params.get('client_cert'),
                api_timeout=module.params.get('api_timeout'),
                interface=module.params.get('interface'),
            )
    except sdk.exceptions.SDKException as e:
        module.fail_json(msg=f"OpenStack Connection Error: {str(e)}")