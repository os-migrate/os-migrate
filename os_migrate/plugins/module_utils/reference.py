from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

import openstack
from openstack.exceptions import HttpException


def image_id(conn, ref, required=True):
    """Fetch ID of Image identified by reference dict `ref`. Use
    OpenStack SDK connection `conn` to fetch the info. If `required`,
    ensure the fetch is successful.

    Returns: the ID, or None if not found and not `required`

    Raises: openstack's ResourceNotFound when `required` but not found
    """
    return _fetch_id(conn, conn.image.find_image, ref, required)


def image_ref(conn, id_, required=True):
    """Create reference dict for Image identified by ID `id_`. Use
    OpenStack SDK connection `conn` to fetch the info. If `required`,
    ensure the fetch is successful.

    Returns: the ref dict, or None if not found and not `required`

    Raises: openstack's ResourceNotFound when `required` but not found
    """
    return _fetch_ref(conn, conn.image.find_image, id_, required)


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


def qos_policy_ref(conn, id_, required=True):
    """Fetch reference dict for Network QoS policy identified by ID
    `id_`. Use OpenStack SDK connection `conn` to fetch the info. If
    `required`, ensure the fetch is successful.

    Returns: the ref dict, or None if not found and not `required`

    Raises: openstack's ResourceNotFound when `required` but not found

    """
    return _fetch_ref(conn, conn.network.find_qos_policy, id_, required)


def qos_policy_id(conn, ref, required=True):
    """Fetch ID of Network QoS policy identified by reference dict `ref`. Use
    OpenStack SDK connection `conn` to fetch the info. If `required`,
    ensure the fetch is successful.

    Returns: the ID, or None if not found and not `required`

    Raises: openstack's ResourceNotFound when `required` but not found

    """
    return _fetch_id(conn, conn.network.find_qos_policy, ref, required)


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


def security_group_ref(conn, id_, required=True):
    """Fetch reference dict of SecurityGroup identified by ID `id_`. Use
    OpenStack SDK connection `conn` to fetch the info. If `required`,
    ensure the fetch is successful.

    Returns: the ref dict, or None if not found and not `required`

    Raises: openstack's ResourceNotFound when `required` but not found
    """
    return _fetch_ref(conn, conn.network.find_security_group, id_, required)


def security_group_id(conn, ref, required=True):
    """Fetch ID of SecurityGroup identified by reference dict `ref`. Use
    OpenStack SDK connection `conn` to fetch the info. If `required`,
    ensure the fetch is successful.

    Returns: the ID, or None if not found and not `required`

    Raises: openstack's ResourceNotFound when `required` but not found
    """
    return _fetch_id(conn, conn.network.find_security_group, ref, required)


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


def flavor_id(conn, ref, required=True):
    """Fetch ID of Flavor identified by reference dict `ref`. Use
    OpenStack SDK connection `conn` to fetch the info. If `required`,
    ensure the fetch is successful.

    Returns: the ID, or None if not found and not `required`

    Raises: openstack's ResourceNotFound when `required` but not found
    """
    return _fetch_id(conn, conn.compute.find_flavor, ref, required)


def flavor_ref(conn, id_, required=True):
    """Create reference dict for Flavor identified by ID `id_`. Use
    OpenStack SDK connection `conn` to fetch the info. If `required`,
    ensure the fetch is successful.

    Returns: the ref dict, or None if not found and not `required`

    Raises: openstack's ResourceNotFound when `required` but not found
    """
    # Flavor objects don't have project_id and domain_id on them
    return _fetch_ref(
        conn, conn.compute.find_flavor, id_, required, get_project_info=False)


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


def project_id(conn, ref, required=True):
    """Fetch ID of a Project identified by reference dict `ref`. Use
    OpenStack SDK connection `conn` to fetch the info. If `required`,
    ensure the fetch is successful.
    Returns: the ID, or None if not found and not `required`
    Raises: openstack's ResourceNotFound when `required` but not found
    """
    return _fetch_id(conn, conn.identity.find_project, ref, required)


def project_ref(conn, id_, required=True):
    """Create reference dict for a Project identified by ID `id_`. Use
    OpenStack SDK connection `conn` to fetch the info. If `required`,
    ensure the fetch is successful.
    Returns: the ref dict, or None if not found and not `required`
    Raises: openstack's ResourceNotFound when `required` but not found
    """
    # Project objects don't have project_id
    return _fetch_ref(conn, conn.identity.find_project, id_, required, get_project_info=False)


def _fetch_ref(conn, get_method, id_, required=True, get_project_info=True):
    if id_ is None:
        return None

    resource = get_method(id_, ignore_missing=not required)
    if resource is None:
        return None

    if get_project_info:
        if isinstance(resource, openstack.image.v2.image.Image):
            project_name, domain_name = _fetch_project_name_and_domain_name(
                conn, resource.owner)
        else:
            project_name, domain_name = _fetch_project_name_and_domain_name(
                conn, resource.project_id)
    else:
        project_name, domain_name = None, None
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
