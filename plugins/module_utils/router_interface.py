from __future__ import absolute_import, division, print_function

__metaclass__ = type

import openstack

from ansible_collections.os_migrate.os_migrate.plugins.module_utils import (
    exc,
    const,
    reference,
    resource,
)


ROUTER_INTERFACE_OWNERS = [
    "network:router_interface",
    "network:ha_router_replicated_interface",
    "network:router_interface_distributed",
]


def router_interfaces(conn, sdk_rtr):
    return filter(
        lambda p: p["device_owner"] in ROUTER_INTERFACE_OWNERS,
        router_ports(conn, sdk_rtr),
    )


def router_ports(conn, sdk_rtr):
    return conn.network.ports(device_id=sdk_rtr["id"])


class RouterInterface(resource.Resource):

    resource_type = const.RES_TYPE_ROUTER_INTERFACE
    sdk_class = openstack.network.v2.port.Port

    info_from_sdk = [
        "id",
    ]
    params_from_sdk = [
        "device_owner",
    ]
    params_from_refs = [
        "device_ref",
        "fixed_ips_refs",
        "network_ref",
    ]
    sdk_params_from_params = []
    sdk_params_from_refs = [
        "fixed_ips",
        "network_id",
    ]

    @classmethod
    def from_sdk(cls, conn, sdk_resource):
        obj = super(RouterInterface, cls).from_sdk(conn, sdk_resource)
        if sdk_resource["device_owner"] not in ROUTER_INTERFACE_OWNERS:
            raise exc.UnexpectedChoice(
                "device_owner", ROUTER_INTERFACE_OWNERS, sdk_resource["device_owner"]
            )
        return obj

    # Custom logic needed for RouterInterface as the operation is complex:
    # 1. Ensure a port exists with the required `fixed_ips`
    # 2. Ensure the port is attached to the router by `router_name`. There is a
    #    specific Neutron REST API endpoint for this operation, so it is separate
    #    from the port creation.
    def create_or_update(self, conn, filters=None):
        changed = False
        refs = self._refs_from_ser(conn)

        # 1. ensure a port exists with the required `fixed_ips`
        sdk_params = self._to_sdk_params(refs)
        port = self._find_port_by_subnet_ips(conn, refs, filters)

        if port:
            # port exists but is assigned to something else => fail
            if (
                port["device_owner"]
                and port["device_owner"] not in ROUTER_INTERFACE_OWNERS
            ) or (port["device_id"] and port["device_id"] != refs["device_id"]):
                raise exc.CannotConverge(
                    "Port with IP address for router import exists, and it is assigned "
                    f"to a different device: {port.to_dict()}"
                )

            if self._port_needs_update(self.from_sdk(conn, port)):
                port = self._update_port(conn, port["id"], sdk_params)
                changed = True
        else:
            port = self._create_port(conn, sdk_params)
            changed = True

        # 2. ensure the port is attached to the router by `router_name`
        if (
            port["device_owner"] not in ROUTER_INTERFACE_OWNERS
            and port["device_id"] != refs["device_id"]
        ):
            conn.network.add_interface_to_router(refs["device_id"], port_id=port["id"])
            changed = True
        return changed

    def _find_port_by_subnet_ips(self, conn, refs, filters=None):
        net_ports = conn.network.ports(network_id=refs["network_id"], **(filters or {}))
        matching_ports = []
        for port in net_ports:
            for fixed_ip in port["fixed_ips"]:
                filtered = dict(
                    filter(
                        lambda keyval: keyval[0] in ["subnet_id", "ip_address"],
                        fixed_ip.items(),
                    )
                )
                if filtered in refs["fixed_ips"]:
                    matching_ports.append(port)
                    break
        if len(matching_ports) == 0:
            return None
        elif len(matching_ports) == 1:
            return matching_ports[0]
        else:
            raise exc.CannotConverge(
                f"When creating a port for router '{refs['device_ref']['name']}', multiple "
                "existing ports were found owning addresses that should "
                f"belong to a single port on the router. The ports are: {matching_ports}"
            )

    def _port_needs_update(self, other):
        self_trimmed = self._data_without_info()
        other_trimmed = other._data_without_info()
        del self_trimmed["params"]["device_owner"]
        del self_trimmed["params"]["device_ref"]
        del other_trimmed["params"]["device_owner"]
        del other_trimmed["params"]["device_ref"]
        return self_trimmed != other_trimmed

    @staticmethod
    def _update_port(conn, port_id, sdk_params):
        return conn.network.update_port(port_id, **sdk_params)

    @staticmethod
    def _create_port(conn, sdk_params):
        return conn.network.create_port(**sdk_params)

    @staticmethod
    def _refs_from_sdk(conn, sdk_res):
        refs = {}

        refs["fixed_ips"] = sdk_res["fixed_ips"]
        refs["fixed_ips_refs"] = []
        for fixed_ip in sdk_res["fixed_ips"]:
            refs["fixed_ips_refs"].append(
                {
                    "ip_address": fixed_ip["ip_address"],
                    "subnet_ref": reference.subnet_ref(conn, fixed_ip["subnet_id"]),
                }
            )
        refs["device_id"] = sdk_res["device_id"]
        refs["device_ref"] = reference.router_ref(conn, sdk_res["device_id"])
        refs["network_id"] = sdk_res["network_id"]
        refs["network_ref"] = reference.network_ref(conn, sdk_res["network_id"])

        return refs

    def _refs_from_ser(self, conn):
        refs = {}
        params = self.params()

        refs["fixed_ips_refs"] = params["fixed_ips_refs"]
        refs["fixed_ips"] = []
        for fixed_ip in params["fixed_ips_refs"]:
            refs["fixed_ips"].append(
                {
                    "ip_address": fixed_ip["ip_address"],
                    "subnet_id": reference.subnet_id(conn, fixed_ip["subnet_ref"]),
                }
            )
        refs["device_ref"] = params["device_ref"]
        refs["device_id"] = reference.router_id(conn, params["device_ref"])
        refs["network_ref"] = params["network_ref"]
        refs["network_id"] = reference.network_id(conn, params["network_ref"])

        return refs
