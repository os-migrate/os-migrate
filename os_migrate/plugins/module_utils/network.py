from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

import openstack

from ansible_collections.os_migrate.os_migrate.plugins.module_utils import const
from ansible_collections.os_migrate.os_migrate.plugins.module_utils import exc
from ansible_collections.os_migrate.os_migrate.plugins.module_utils import reference
from ansible_collections.os_migrate.os_migrate.plugins.module_utils import serialization
from ansible_collections.os_migrate.os_migrate.plugins.module_utils.serialization \
    import set_sdk_params_same_name, set_ser_params_same_name


def serialize_network(sdk_net, net_refs):
    """Serialize OpenStack SDK network `sdk_net` into OS-Migrate
    format. Use `net_refs` for id-to-name mappings.

    Returns: Dict - OS-Migrate structure for Network
    """
    expected_type = openstack.network.v2.network.Network
    if type(sdk_net) != expected_type:
        raise exc.UnexpectedResourceType(expected_type, type(sdk_net))

    resource = {}
    params = {}
    info = {}
    resource[const.RES_PARAMS] = params
    resource[const.RES_INFO] = info
    resource[const.RES_TYPE] = const.RES_TYPE_NETWORK

    params['availability_zone_hints'] = sorted(sdk_net['availability_zone_hints'])
    set_ser_params_same_name(params, sdk_net, [
        'description',
        'dns_domain',
        'is_admin_state_up',
        'is_default',
        'is_port_security_enabled',
        'is_router_external',
        'is_shared',
        'is_vlan_transparent',
        'mtu',
        'name',
        'provider_network_type',
        'provider_physical_network',
        'provider_segmentation_id',
        'segments',
    ])
    set_ser_params_same_name(params, net_refs, [
        'qos_policy_name',
    ])

    info['subnet_ids'] = sorted(sdk_net['subnet_ids'])
    set_ser_params_same_name(info, sdk_net, [
        'availability_zones',
        'created_at',
        'id',
        'project_id',
        'qos_policy_id',
        'revision_number',
        'status',
        'updated_at',
    ])

    return resource


def network_sdk_params(ser_net, net_refs):
    """Create OpenStack SDK parameters dict for creation or update of the
    OS-Migrate Network serialization `ser_net`. Use `net_refs` for
    name-to-id mappings.

    Returns: Parameters to be fed into `openstack.network.v2.network.Network`
    """
    res_type = ser_net.get(const.RES_TYPE, None)
    if res_type != const.RES_TYPE_NETWORK:
        raise exc.UnexpectedResourceType(const.RES_TYPE_NETWORK, res_type)

    ser_params = ser_net[const.RES_PARAMS]
    sdk_params = {}

    set_sdk_params_same_name(ser_params, sdk_params, [
        'availability_zone_hints',
        'description',
        'dns_domain',
        'is_admin_state_up',
        'is_default',
        'is_port_security_enabled',
        'is_router_external',
        'is_shared',
        'is_vlan_transparent',
        'mtu',
        'name',
        'provider_network_type',
        'provider_physical_network',
        'provider_segmentation_id',
        'segments',
    ])
    set_sdk_params_same_name(net_refs, sdk_params, [
        'qos_policy_id',
    ])

    return sdk_params


def network_needs_update(sdk_net, net_refs, target_ser_net):
    """Having OpenStack SDK network `sdk_net` and corresponding id-name
    mappings `net_refs`, decide if the network needs to be updated to
    reach state represented in OS-Migrate Network serialization
    `target_ser_net`.

    Returns: True if network needs to be updated, False otherwise
    """
    current_ser_net = serialize_network(sdk_net, net_refs)
    return serialization.resource_needs_update(current_ser_net, target_ser_net)


def security_group_needs_update(sdk_sec, target_ser_sec):
    """Having OpenStack SDK security group `sdk_sec`,
    decide if the security group needs to be updated to
    reach state represented in OS-Migrate Security group serialization
    `target_ser_sec`.

    Returns: True if security group needs to be updated, False otherwise
    """
    current_ser_sec = serialize_security_group(sdk_sec)
    return serialization.resource_needs_update(current_ser_sec, target_ser_sec)


def network_refs_from_sdk(conn, sdk_net):
    """Create a dict of name/id mappings for resources referenced from
    OpenStack SDK Network `sdk_net`. Fetch any necessary information
    from OpenStack SDK connection `conn`.

    Returns: dict with names and IDs of resources referenced from
    `sdk_net` (only those important for OS-Migrate)
    """
    expected_type = openstack.network.v2.network.Network
    if type(sdk_net) != expected_type:
        raise exc.UnexpectedResourceType(expected_type, type(sdk_net))
    refs = {}

    # when creating refs from SDK Network object, we copy IDs and
    # query the cloud for names
    refs['qos_policy_id'] = sdk_net['qos_policy_id']
    refs['qos_policy_name'] = reference.qos_policy_name(
        conn, sdk_net['qos_policy_id'])

    return refs


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


def network_refs_from_ser(conn, ser_net):
    """Create a dict of name/id mappings for resources referenced from
    OS-Migrage network serialization `sdk_net`. Fetch any necessary
    information from OpenStack SDK connection `conn`.

    Returns: dict with names and IDs of resources referenced from
    `sdk_net` (only those important for OS-Migrate)
    """
    if ser_net[const.RES_TYPE] != const.RES_TYPE_NETWORK:
        raise exc.UnexpectedResourceType(
            const.RES_TYPE_NETWORK, ser_net[const.RES_TYPE])
    ser_params = ser_net[const.RES_PARAMS]
    refs = {}

    # when creating refs from serialized Network, we copy names and
    # query the cloud for IDs
    refs['qos_policy_name'] = ser_params['qos_policy_name']
    refs['qos_policy_id'] = reference.qos_policy_id(
        conn, ser_params['qos_policy_name'])

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
    sdk_params = {}

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
    sdk_params = {}

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
