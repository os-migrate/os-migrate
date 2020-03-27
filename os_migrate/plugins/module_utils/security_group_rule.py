from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

import openstack

from ansible_collections.os_migrate.os_migrate.plugins.module_utils \
    import const, exc, reference
from ansible_collections.os_migrate.os_migrate.plugins.module_utils.serialization \
    import set_sdk_params_same_name, set_ser_params_same_name


def security_group_rule_refs_from_sdk(conn, sdk_rule):
    """Create a dict of name/id mappings for resources referenced from
    OpenStack SDK Security Group Rule `sdk_rule`. Fetch any necessary information
    from OpenStack SDK connection `conn`.

    Returns: dict with names and IDs of resources referenced from
    `sdk_rule` (only those important for OS-Migrate)
    """
    expected_type = openstack.network.v2.security_group_rule.SecurityGroupRule
    if type(sdk_rule) != expected_type:
        raise exc.UnexpectedResourceType(expected_type, type(sdk_rule))
    refs = {}

    # when creating refs from SDK Security Group Rule object, we copy IDs and
    # query the cloud for names
    refs['security_group_name'] = reference.security_group_name(
        conn, sdk_rule['security_group_id'])
    refs['remote_group_name'] = reference.security_group_name(
        conn, sdk_rule['remote_group_id'])

    return refs


def security_group_rule_refs_from_ser(conn, ser_sec):
    """Create a dict of name/id mappings for resources referenced from
    OS-Migrage security group rule serialization `sdk_sec`. Fetch any necessary
    information from OpenStack SDK connection `conn`.

    Returns: dict with names and IDs of resources referenced from
    `sdk_sec` (only those important for OS-Migrate)
    """
    if ser_sec[const.RES_TYPE] != const.RES_TYPE_SECURITYGROUPRULE:
        raise exc.UnexpectedResourceType(
            const.RES_TYPE_SECURITYGROUPRULE, ser_sec[const.RES_TYPE])
    ser_params = ser_sec[const.RES_PARAMS]
    refs = {}

    # when creating refs from serialized security group, we copy names and
    # query the cloud for IDs
    refs['security_group_name'] = ser_params['security_group_name']
    refs['security_group_id'] = reference.security_group_id(
        conn, ser_params['security_group_name'])

    return refs


def serialize_security_group_rule(sdk_sec_rule, sec_refs):
    """Serialize OpenStack SDK security group rule
    `sdk_sec_rule` into OS-Migrate format.

    Returns: Dict - OS-Migrate structure for Security group rule.
    """
    expected_type = openstack.network.v2.security_group_rule.SecurityGroupRule
    if type(sdk_sec_rule) != expected_type:
        raise exc.UnexpectedResourceType(expected_type, type(sdk_sec_rule))

    resource = {}
    params = {}
    info = {}

    resource[const.RES_PARAMS] = params
    resource[const.RES_INFO] = info
    resource[const.RES_TYPE] = const.RES_TYPE_SECURITYGROUPRULE

    params['tags'] = sorted(sdk_sec_rule['tags'])

    # Decide which attrs are param and which are info
    set_ser_params_same_name(info, sdk_sec_rule, [
        'id',
        'security_group_id',
        'remote_group_id',
        'project_id',
        'created_at',
        'updated_at',
        'revision_number',
    ])

    set_ser_params_same_name(params, sec_refs, [
        'security_group_name',
        'remote_group_name',
    ])

    set_ser_params_same_name(params, sdk_sec_rule, [
        'description',
        'direction',
        'port_range_max',
        'port_range_min',
        'protocol',
        'remote_ip_prefix',
    ])

    return resource


def security_group_rule_sdk_params(ser_sec_rule, sec_refs):
    """Create OpenStack SDK parameters dict for creation or update of the
    OS-Migrate Security group rules `ser_sec_rule`. Use `sec_refs` for
    name-to-id mappings.

    Returns: Parameters to be fed into `openstack.network.v2.security_group_rule.SecurityGroupRule`
    """
    res_type = ser_sec_rule.get(const.RES_TYPE, None)
    if res_type != const.RES_TYPE_SECURITYGROUPRULE:
        raise exc.UnexpectedResourceType(const.RES_TYPE_SECURITYGROUPRULE, res_type)

    ser_params = ser_sec_rule[const.RES_PARAMS]
    sdk_params = {}

    set_sdk_params_same_name(sec_refs, sdk_params, [
        'remote_group_id',
        'security_group_id',
    ])

    set_sdk_params_same_name(ser_params, sdk_params, [
        'description',
        'direction',
        'port_range_max',
        'port_range_min',
        'protocol',
        'remote_ip_prefix',
        'revision_number',
    ])

    return sdk_params
