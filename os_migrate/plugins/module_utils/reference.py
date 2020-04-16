from __future__ import (absolute_import, division, print_function)
__metaclass__ = type


def flavor_name(conn, id_, required=True):
    """Fetch name of flavor identified by ID `id_`. Use OpenStack
    SDK connection `conn` to fetch the info. If `required`, ensure the
    fetch is successful.

    Returns: the name, or None if not found and not `required`

    Raises: openstack's ResourceNotFound when `required` but not found
    """
    return _fetch_name(conn.compute.find_flavor, id_, required)


def flavor_id(conn, name, required=True):
    """Fetch ID of flavor identified by name `name`. Use OpenStack
    SDK connection `conn` to fetch the info. If `required`, ensure the
    fetch is successful.

    Returns: the ID, or None if not found and not `required`

    Raises: openstack's ResourceNotFound when `required` but not found
    """
    return _fetch_id(conn.compute.find_flavor, name, required)


def network_name(conn, id_, required=True):
    """Fetch name of Network identified by ID `id_`. Use OpenStack
    SDK connection `conn` to fetch the info. If `required`, ensure the
    fetch is successful.

    Returns: the name, or None if not found and not `required`

    Raises: openstack's ResourceNotFound when `required` but not found
    """
    return _fetch_name(conn.network.find_network, id_, required)


def network_id(conn, name, required=True):
    """Fetch ID of Network identified by name `name`. Use OpenStack
    SDK connection `conn` to fetch the info. If `required`, ensure the
    fetch is successful.

    Returns: the ID, or None if not found and not `required`

    Raises: openstack's ResourceNotFound when `required` but not found
    """
    return _fetch_id(conn.network.find_network, name, required)


def network_flavor_name(conn, id_, required=True):
    """Fetch name of Network Flavor identified by ID `id_`. Use OpenStack
    SDK connection `conn` to fetch the info. If `required`, ensure the
    fetch is successful.

    Returns: the name, or None if not found and not `required`

    Raises: openstack's ResourceNotFound when `required` but not found
    """
    return _fetch_name(conn.network.find_flavor, id_, required)


def network_flavor_id(conn, name, required=True):
    """Fetch ID of Network Flavor identified by name `name`. Use OpenStack
    SDK connection `conn` to fetch the info. If `required`, ensure the
    fetch is successful.

    Returns: the ID, or None if not found and not `required`

    Raises: openstack's ResourceNotFound when `required` but not found
    """
    return _fetch_id(conn.network.find_flavor, name, required)


def qos_policy_name(conn, id_, required=True):
    """Fetch name of QoS Policy identified by ID `id_`. Use OpenStack SDK
    connection `conn` to fetch the info. If `required`, ensure the
    fetch is successful.

    Returns: the name, or None if not found and not `required`

    Raises: openstack's ResourceNotFound when `required` but not found
    """
    return _fetch_name(conn.network.find_qos_policy, id_, required)


def qos_policy_id(conn, name, required=True):
    """Fetch ID of QoS Policy identified by name `name`. Use OpenStack SDK
    connection `conn` to fetch the info. If `required`, ensure the
    fetch is successful.

    Returns: the ID, or None if not found and not `required`

    Raises: openstack's ResourceNotFound when `required` but not found
    """
    return _fetch_id(conn.network.find_qos_policy, name, required)


def router_name(conn, id_, required=True):
    """Fetch name of Router identified by ID `id_`. Use OpenStack
    SDK connection `conn` to fetch the info. If `required`, ensure the
    fetch is successful.

    Returns: the name, or None if not found and not `required`

    Raises: openstack's ResourceNotFound when `required` but not found
    """
    return _fetch_name(conn.network.find_router, id_, required)


def router_id(conn, name, required=True):
    """Fetch ID of Router identified by name `name`. Use OpenStack
    SDK connection `conn` to fetch the info. If `required`, ensure the
    fetch is successful.

    Returns: the ID, or None if not found and not `required`

    Raises: openstack's ResourceNotFound when `required` but not found
    """
    return _fetch_id(conn.network.find_router, name, required)


def security_group_name(conn, id_, required=True):
    """Fetch name of the Security Group identified by ID `id_`. Use OpenStack SDK
    connection `conn` to fetch the info. If `required`, ensure the
    fetch is successful.

    Returns: the name, or None if not found and not `required`

    Raises: openstack's ResourceNotFound when `required` but not found
    """
    return _fetch_name(conn.network.find_security_group, id_, required)


def security_group_id(conn, name, required=True):
    """Fetch ID of Security group identified by name `name`. Use OpenStack SDK
    connection `conn` to fetch the info. If `required`, ensure the
    fetch is successful.

    Returns: the ID, or None if not found and not `required`

    Raises: openstack's ResourceNotFound when `required` but not found
    """
    return _fetch_id(conn.network.find_security_group, name, required)


def subnet_name(conn, id_, required=True):
    """Fetch name of Subnet identified by ID `id_`. Use OpenStack
    SDK connection `conn` to fetch the info. If `required`, ensure the
    fetch is successful.

    Returns: the name, or None if not found and not `required`

    Raises: openstack's ResourceNotFound when `required` but not found
    """
    return _fetch_name(conn.network.find_subnet, id_, required)


def subnet_id(conn, name, required=True):
    """Fetch ID of Subnet identified by name `name`. Use OpenStack
    SDK connection `conn` to fetch the info. If `required`, ensure the
    fetch is successful.

    Returns: the ID, or None if not found and not `required`

    Raises: openstack's ResourceNotFound when `required` but not found
    """
    return _fetch_id(conn.network.find_subnet, name, required)


def segment_name(conn, id_, required=True):
    """Fetch name of Segment identified by ID `id_`. Use OpenStack
    SDK connection `conn` to fetch the info. If `required`, ensure the
    fetch is successful.

    Returns: the name, or None if not found and not `required`

    Raises: openstack's ResourceNotFound when `required` but not found
    """
    return _fetch_name(conn.network.find_segment, id_, required)


def segment_id(conn, name, required=True):
    """Fetch ID of Segment identified by name `name`. Use OpenStack
    SDK connection `conn` to fetch the info. If `required`, ensure the
    fetch is successful.

    Returns: the ID, or None if not found and not `required`

    Raises: openstack's ResourceNotFound when `required` but not found
    """
    return _fetch_id(conn.network.find_segment, name, required)


def subnet_pool_name(conn, id_, required=True):
    """Fetch name of Subnet Pool identified by ID `id_`. Use OpenStack
    SDK connection `conn` to fetch the info. If `required`, ensure the
    fetch is successful.

    Returns: the name, or None if not found and not `required`

    Raises: openstack's ResourceNotFound when `required` but not found
    """
    return _fetch_name(conn.network.find_subnet_pool, id_, required)


def subnet_pool_id(conn, name, required=True):
    """Fetch ID of Subnet Pool identified by name `name`. Use OpenStack
    SDK connection `conn` to fetch the info. If `required`, ensure the
    fetch is successful.

    Returns: the ID, or None if not found and not `required`

    Raises: openstack's ResourceNotFound when `required` but not found
    """
    return _fetch_id(conn.network.find_subnet_pool, name, required)


def _fetch_name(get_method, id_, required=True):
    """Use `get_method` to fetch an OpenStack SDK resource by `id_` and
    return its name. If `required`, ensure the fetch is successful.

    Returns: the ID, or None if not found and not `required`

    Raises: openstack's ResourceNotFound when `required` but not found
    """
    if id_ is not None:
        return get_method(id_, ignore_missing=not required)['name']


def _fetch_id(get_method, name, required=True):
    """Use `get_method` to fetch an OpenStack SDK resource by `name` and
    return its ID. If `required`, ensure the fetch is successful.

    Returns: the ID, or None if not found and not `required`

    Raises: openstack's ResourceNotFound when `required` but not found
    """
    if name is not None:
        return get_method(name, ignore_missing=not required)['id']
