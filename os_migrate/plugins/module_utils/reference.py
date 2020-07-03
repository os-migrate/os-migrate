from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

from openstack.exceptions import HttpException


def network_id(conn, ref, required=True):
    """Fetch ID of Network identified by reference dict `ref`. Use
    OpenStack SDK connection `conn` to fetch the info. If `required`,
    ensure the fetch is successful.

    Returns: the ID, or None if not found and not `required`

    Raises: openstack's ResourceNotFound when `required` but not found
    """
    return _fetch_id(conn, conn.network.find_network, ref, required)


def network_ref(conn, id_, required=True):
    """Create reference dict for Network identified by ID `id_`. Use
    OpenStack SDK connection `conn` to fetch the info. If `required`,
    ensure the fetch is successful.

    Returns: the ref dict, or None if not found and not `required`

    Raises: openstack's ResourceNotFound when `required` but not found
    """
    return _fetch_ref(conn, conn.network.find_network, id_, required)


def network_flavor_ref(conn, id_, required=True):
    """Fetch reference dict for Network Flavor identified by ID `id_`. Use
    OpenStack SDK connection `conn` to fetch the info. If `required`,
    ensure the fetch is successful.

    Returns: the ref dict, or None if not found and not `required`

    Raises: openstack's ResourceNotFound when `required` but not found
    """
    return _fetch_ref(conn, conn.network.find_flavor, id_, required)


def network_flavor_id(conn, ref, required=True):
    """Fetch ID of Network Flavor identified by reference dict `ref`. Use
    OpenStack SDK connection `conn` to fetch the info. If `required`,
    ensure the fetch is successful.

    Returns: the ID, or None if not found and not `required`

    Raises: openstack's ResourceNotFound when `required` but not found

    """
    return _fetch_id(conn, conn.network.find_flavor, ref, required)


def qos_policy_name(conn, id_, required=True):
    """Fetch name of QoS Policy identified by ID `id_`. Use OpenStack SDK
    connection `conn` to fetch the info. If `required`, ensure the
    fetch is successful.

    Returns: the name, or None if not found and not `required`

    Raises: openstack's ResourceNotFound when `required` but not found
    """
    return _fetch_name(conn.network.find_qos_policy, id_, required)


def qos_policy_id(conn, name, required=True, filters=None):
    """Fetch ID of QoS Policy identified by name `name`. Use OpenStack SDK
    connection `conn` to fetch the info. If `required`, ensure the
    fetch is successful.

    Returns: the ID, or None if not found and not `required`

    Raises: openstack's ResourceNotFound when `required` but not found
    """
    return _fetch_id_simple(conn.network.find_qos_policy, name, required, filters)


def router_ref(conn, id_, required=True):
    """Fetch reference dict of Router identified by ID `id_`. Use
    OpenStack SDK connection `conn` to fetch the info. If `required`,
    ensure the fetch is successful.

    Returns: the ref dict, or None if not found and not `required`

    Raises: openstack's ResourceNotFound when `required` but not found
    """
    return _fetch_ref(conn, conn.network.find_router, id_, required)


def router_id(conn, ref, required=True):
    """Fetch ID of Router identified by reference dict `ref`. Use
    OpenStack SDK connection `conn` to fetch the info. If `required`,
    ensure the fetch is successful.

    Returns: the ID, or None if not found and not `required`

    Raises: openstack's ResourceNotFound when `required` but not found
    """
    return _fetch_id(conn, conn.network.find_router, ref, required)


def security_group_name(conn, id_, required=True):
    """Fetch name of the Security Group identified by ID `id_`. Use OpenStack SDK
    connection `conn` to fetch the info. If `required`, ensure the
    fetch is successful.

    Returns: the name, or None if not found and not `required`

    Raises: openstack's ResourceNotFound when `required` but not found
    """
    return _fetch_name(conn.network.find_security_group, id_, required)


def security_group_id(conn, name, required=True, filters=None):
    """Fetch ID of Security group identified by name `name`. Use OpenStack SDK
    connection `conn` to fetch the info. If `required`, ensure the
    fetch is successful.

    Returns: the ID, or None if not found and not `required`

    Raises: openstack's ResourceNotFound when `required` but not found
    """
    return _fetch_id_simple(conn.network.find_security_group, name, required, filters)


def subnet_ref(conn, id_, required=True):
    """Fetch reference dict of Subnet identified by ID `id_`. Use
    OpenStack SDK connection `conn` to fetch the info. If `required`,
    ensure the fetch is successful.

    Returns: the ref dict, or None if not found and not `required`

    Raises: openstack's ResourceNotFound when `required` but not found
    """
    return _fetch_ref(conn, conn.network.find_subnet, id_, required)


def subnet_id(conn, ref, required=True):
    """Fetch ID of Subnet identified by reference dict `ref`. Use
    OpenStack SDK connection `conn` to fetch the info. If `required`,
    ensure the fetch is successful.

    Returns: the ID, or None if not found and not `required`

    Raises: openstack's ResourceNotFound when `required` but not found
    """
    return _fetch_id(conn, conn.network.find_subnet, ref, required)


def segment_id(conn, ref, required=True):
    """Fetch ID of Segment identified by reference dict `ref`. Use
    OpenStack SDK connection `conn` to fetch the info. If `required`,
    ensure the fetch is successful.

    Returns: the ID, or None if not found and not `required`

    Raises: openstack's ResourceNotFound when `required` but not found
    """
    return _fetch_id(conn, conn.network.find_segment, ref, required)


def segment_ref(conn, id_, required=True):
    """Create reference dict for Segment identified by ID `id_`. Use
    OpenStack SDK connection `conn` to fetch the info. If `required`,
    ensure the fetch is successful.

    Returns: the ref dict, or None if not found and not `required`

    Raises: openstack's ResourceNotFound when `required` but not found
    """
    return _fetch_ref(conn, conn.network.find_segment, id_, required)


def server_flavor_name(conn, id_, required=True):
    """Fetch name of server flavor identified by ID `id_`. Use OpenStack
    SDK connection `conn` to fetch the info. If `required`, ensure the
    fetch is successful.

    Returns: the name, or None if not found and not `required`

    Raises: openstack's ResourceNotFound when `required` but not found
    """
    return _fetch_name(conn.compute.find_flavor, id_, required)


def server_flavor_id(conn, name, required=True, filters=None):
    """Fetch ID of server flavor identified by name `name`. Use OpenStack
    SDK connection `conn` to fetch the info. If `required`, ensure the
    fetch is successful.

    Returns: the ID, or None if not found and not `required`

    Raises: openstack's ResourceNotFound when `required` but not found
    """
    return _fetch_id_simple(conn.compute.find_flavor, name, required, filters)


def subnet_pool_id(conn, ref, required=True):
    """Fetch ID of SubnetPool identified by reference dict `ref`. Use
    OpenStack SDK connection `conn` to fetch the info. If `required`,
    ensure the fetch is successful.

    Returns: the ID, or None if not found and not `required`

    Raises: openstack's ResourceNotFound when `required` but not found
    """
    return _fetch_id(conn, conn.network.find_subnet_pool, ref, required)


def subnet_pool_ref(conn, id_, required=True):
    """Create reference dict for SubnetPool identified by ID `id_`. Use
    OpenStack SDK connection `conn` to fetch the info. If `required`,
    ensure the fetch is successful.

    Returns: the ref dict, or None if not found and not `required`

    Raises: openstack's ResourceNotFound when `required` but not found
    """
    return _fetch_ref(conn, conn.network.find_subnet_pool, id_, required)


def _fetch_name(get_method, id_, required=True):
    """Use `get_method` to fetch an OpenStack SDK resource by `id_` and
    return its name. If `required`, ensure the fetch is successful.

    Returns: the ID, or None if not found and not `required`

    Raises: openstack's ResourceNotFound when `required` but not found
    """
    if id_ is not None:
        return get_method(id_, ignore_missing=not required)['name']


def _fetch_id_simple(get_method, name, required=True, filters=None):
    """Use `get_method` to fetch an OpenStack SDK resource by `name` and
    return its ID. If `required`, ensure the fetch is successful.

    Returns: the ID, or None if not found and not `required`

    Raises: openstack's ResourceNotFound when `required` but not found
    """
    if name is not None:
        return get_method(name, ignore_missing=not required, **(filters or {}))['id']


def _fetch_ref(conn, get_method, id_, required=True):
    if id_ is None:
        return None

    resource = get_method(id_, ignore_missing=not required)
    if resource is None:
        return None

    project_name, domain_name = _fetch_project_name_and_domain_name(conn, resource.project_id)
    return {
        'name': resource['name'],
        'project_name': project_name,
        'domain_name': domain_name,
    }


def _fetch_id(conn, get_method, ref, required=True):
    if ref is None:
        return None

    return get_method(
        ref['name'],
        ignore_missing=not required,
        **_project_id_filters(conn, ref),
    )['id']


def _project_id_filters(conn, ref):
    if ref['project_name'] == '%auth%':
        return {'project_id': conn.current_project_id}

    domain_filters = {}
    if ref['domain_name'] is not None and ref['domain_name'] != '%auth%':
        try:
            domain = conn.identity.find_domain(ref['domain_name'])
            domain_filters = {'domain_id': domain['id']}
        except HttpException as e:
            if e.status_code != 403:
                raise e

    if ref['project_name'] is not None:
        try:
            project = conn.identity.find_project(ref['project_name'], **domain_filters)
            return {'project_id': project['id']}
        except HttpException as e:
            if e.status_code != 403:
                raise e
    return {}


def _fetch_project_name_and_domain_name(conn, project_id):
    # Perhaps we could make it configurable whether to use explicit
    # project/domain names even when the project_id matches the
    # currently authenticated one. However, always using '%auth%'
    # should probably cover any sane use cases, so let's use it always
    # until we get a RFE to do otherwise.
    if project_id == conn.current_project_id:
        return ('%auth%', '%auth%')

    project_name = None
    domain_name = None
    try:
        project = conn.identity.get_project(project_id)
        project_name = project['name']

        domain = conn.identity.get_domain(project.domain_id)
        domain_name = domain['name']
    except HttpException as e:
        # If we don't have permission to fetch project/domain names,
        # make a simple reference based on resource name only (keep
        # project and domain names as None). Re-raise any other error.
        if e.status_code != 403:
            raise e

    return (project_name, domain_name)
