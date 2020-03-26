from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

import openstack

from ansible_collections.os_migrate.os_migrate.plugins.module_utils \
    import const, exc, serialization
from ansible_collections.os_migrate.os_migrate.plugins.module_utils.serialization \
    import set_sdk_params_same_name, set_ser_params_same_name


def security_group_needs_update(sdk_sec, target_ser_sec):
    """Having OpenStack SDK security group `sdk_sec`,
    decide if the security group needs to be updated to
    reach state represented in OS-Migrate Security group serialization
    `target_ser_sec`.

    Returns: True if security group needs to be updated, False otherwise
    """
    current_ser_sec = serialize_security_group(sdk_sec)
    return serialization.resource_needs_update(current_ser_sec, target_ser_sec)


def serialize_security_group(sdk_sec):
    """Serialize OpenStack SDK security group `sdk_sec`
    into OS-Migrate format.

    Returns: Dict - OS-Migrate structure for Security group.
    """
    expected_type = openstack.network.v2.security_group.SecurityGroup
    if type(sdk_sec) != expected_type:
        raise exc.UnexpectedResourceType(expected_type, type(sdk_sec))

    resource = {}
    params = {}
    info = {}

    resource[const.RES_PARAMS] = params
    resource[const.RES_INFO] = info
    resource[const.RES_TYPE] = const.RES_TYPE_SECURITYGROUP
    params['tags'] = sorted(sdk_sec['tags'])

    # Decide which attrs are param and which are info
    set_ser_params_same_name(info, sdk_sec, [
        'id',
        'project_id',
        'created_at',
        'updated_at',
        'revision_number',
    ])

    set_ser_params_same_name(params, sdk_sec, [
        'name',
        'description',
    ])

    return resource


def security_group_sdk_params(ser_sec):
    """Create OpenStack SDK parameters dict for creation or update of the
    OS-Migrate Security groups `ser_sec`.

    Returns: Parameters to be fed into `openstack.network.v2.security_group.SecurityGroup`
    """
    res_type = ser_sec.get(const.RES_TYPE, None)
    if res_type != const.RES_TYPE_SECURITYGROUP:
        raise exc.UnexpectedResourceType(const.RES_TYPE_SECURITYGROUP, res_type)

    ser_params = ser_sec[const.RES_PARAMS]
    sdk_params = {}

    set_sdk_params_same_name(ser_params, sdk_params, [
        'description',
        'name',
    ])

    return sdk_params
