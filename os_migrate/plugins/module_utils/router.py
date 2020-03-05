from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

from copy import deepcopy
import openstack

from ansible_collections.os_migrate.os_migrate.plugins.module_utils import const
from ansible_collections.os_migrate.os_migrate.plugins.module_utils import exc
from ansible_collections.os_migrate.os_migrate.plugins.module_utils import reference
from ansible_collections.os_migrate.os_migrate.plugins.module_utils.serialization \
    import set_ser_params_same_name


def serialize_router(sdk_router, router_refs):
    """Serialize OpenStack SDK router `sdk_router` into OS-Migrate
    format. Use `router_refs` for id-to-name mappings.

    Returns: Dict - OS-Migrate structure for Router
    """
    expected_type = openstack.network.v2.router.Router
    if type(sdk_router) != expected_type:
        raise exc.UnexpectedResourceType(expected_type, type(sdk_router))

    resource = {}
    params = {}
    info = {}
    resource[const.RES_PARAMS] = params
    resource[const.RES_INFO] = info
    resource[const.RES_TYPE] = const.RES_TYPE_ROUTER

    set_ser_params_same_name(params, sdk_router, [
        'availability_zone_hints',
        'availability_zones',
        'description',
        'is_admin_state_up',
        'is_distributed',
        'is_ha',
        'name',
        'routes',
    ])
    set_ser_params_same_name(params, router_refs, [
        'external_gateway_nameinfo',
        'flavor_name',
    ])

    set_ser_params_same_name(info, sdk_router, [
        'created_at',
        'project_id',
        'revision_number',
        'status',
        'updated_at',
    ])
    set_ser_params_same_name(info, router_refs, [
        'external_gateway_info',
        'flavor_id',
    ])

    return resource


def router_refs_from_sdk(conn, sdk_router):
    """Create a dict of name/id mappings for resources referenced from
    OpenStack SDK Router `sdk_router`. Fetch any necessary information
    from OpenStack SDK connection `conn`.

    Returns: dict with names and IDs of resources referenced from
    `sdk_router` (only those important for OS-Migrate)
    """
    expected_type = openstack.network.v2.router.Router
    if type(sdk_router) != expected_type:
        raise exc.UnexpectedResourceType(expected_type, type(sdk_router))
    refs = {}

    # when creating refs from SDK Router object, we copy IDs and
    # query the cloud for names
    refs['external_gateway_info'] = sdk_router['external_gateway_info']
    refs['flavor_id'] = sdk_router['flavor_id']

    def _external_gateway_nameinfo(conn, egi):
        egni = deepcopy(egi)
        del egni['network_id']
        del egni['external_fixed_ips']

        egni['network_name'] = reference.network_name(conn, egi['network_id'])
        # We currently do not put external_fixed_ips into params:
        # * As a tenant we cannot fetch subnet_name for a subnet in a public
        #   net, so we do not request a particular public IP for the router
        #   when recreating it. It may be worth circling back if there is a way
        #   to try and preserve the IPs.
        return egni

    refs['external_gateway_nameinfo'] = _external_gateway_nameinfo(
        conn, sdk_router['external_gateway_info'])
    refs['flavor_name'] = reference.network_flavor_name(
        conn, sdk_router['flavor_id'])

    return refs
