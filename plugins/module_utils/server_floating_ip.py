from __future__ import absolute_import, division, print_function

__metaclass__ = type

import openstack
import time

from ansible_collections.os_migrate.os_migrate.plugins.module_utils import (
    exc,
    const,
    reference,
    resource,
)


def server_floating_ips(conn, server_ports):
    sdk_fips = []

    # Typically a server will have one or a few ports, while there can
    # be many listable FIPs. It is expected to be better to query FIPs
    # attached to a given port, rather than to query all FIPs visible
    # to the user and filter them on client side.
    for port in server_ports:
        port_fips = list(conn.network.ips(port_id=port.info()["id"]))
        sdk_fips.extend(port_fips)

    return sdk_fips


class ServerFloatingIP(resource.Resource):

    resource_type = const.RES_TYPE_SERVER_FLOATING_IP
    sdk_class = openstack.network.v2.floating_ip.FloatingIP

    info_from_sdk = [
        "created_at",
        "floating_network_id",
        "id",
        "port_id",
        "qos_policy_id",
        "router_id",
        "tags",
        "updated_at",
    ]
    params_from_sdk = [
        "description",
        "dns_domain",
        "dns_name",
        "fixed_ip_address",
        "floating_ip_address",
    ]
    params_from_refs = [
        "floating_network_ref",
        "qos_policy_ref",
    ]
    sdk_params_from_params = [
        "description",
        "dns_domain",
        "dns_name",
        "fixed_ip_address",
    ]
    sdk_params_from_refs = [
        "floating_network_id",
        "qos_policy_id",
    ]

    def create_or_update(self, conn, filters=None):
        raise exc.Unsupported(
            "Direct ServerFloatingIP.create_or_update call is unsupported."
        )

    def create(self, conn, sdk_srv, mode):
        mode_choices = ["auto", "skip", "new", "existing"]
        if mode not in mode_choices:
            raise exc.UnexpectedChoice("floating_ip_mode", mode_choices, mode)

        my_port = self._find_my_server_port(conn, sdk_srv)
        if mode == "skip":
            return None
        elif mode == "existing":
            return self._attach_existing(conn, my_port, sdk_srv, required=True)
        elif mode == "new":
            return self._create_new(conn, my_port, sdk_srv)
        elif mode == "auto":
            return self._create_auto(conn, my_port, sdk_srv)

    def _create_auto(self, conn, my_port, sdk_srv):
        attached = self._attach_existing(conn, my_port, sdk_srv, required=False)
        if attached:
            return attached
        else:
            return self._create_new(conn, my_port, sdk_srv)

    def _create_new(self, conn, my_port, sdk_srv):
        sdk_params = self._to_sdk_params(self._refs_from_ser(conn))
        sdk_params["port_id"] = my_port["id"]
        return conn.network.create_ip(**sdk_params)

    def _attach_existing(self, conn, my_port, sdk_srv, required=False):
        existing = self._find_specified_detached_floating_ip(conn, required=required)
        if existing:
            conn.compute.add_floating_ip_to_server(
                sdk_srv,
                existing["floating_ip_address"],
                self.params()["fixed_ip_address"],
            )
            return existing
        return None

    def _find_my_server_port(self, conn, sdk_srv, delay=5, retries=5):
        params = self.params()
        for try_number in range(retries):
            srv_ports = conn.network.ports(device_id=sdk_srv["id"])
            for port in srv_ports:
                port_fixed_ips = [item["ip_address"] for item in port["fixed_ips"]]
                if params["fixed_ip_address"] in port_fixed_ips:
                    return port

            # wait and retry
            time.sleep(delay)

        # still failing after max retries
        raise exc.CannotConverge(
            f"Floating IP for server '{sdk_srv['name']}' ('{sdk_srv['id']}') is meant to attach "
            f"to a port with fixed IP '{params['fixed_ip_address']}', but no such port was found "
            "on that server."
        )

    def _find_specified_detached_floating_ip(self, conn, required=False):
        fip_address = self.params()["floating_ip_address"]
        query = {"floating_ip_address": fip_address}
        fips = list(conn.network.ips(**query))
        if len(fips) == 1:
            fip = fips[0]
        elif len(fips) > 1:
            raise exc.InconsistentState(
                f"More than one floating IP found with address {fip_address}"
            )
        elif required:  # but not found
            raise exc.CannotConverge(
                f"No floating IPs found with address {fip_address}"
            )
        else:  # not found and not required
            return None

        if fip["port_id"] is not None:
            raise exc.CannotConverge(
                f"Floating IP with address {fip_address} is already"
                f"attached to port {fip['port_id']}"
            )
        return fip

    @staticmethod
    def _refs_from_sdk(conn, sdk_res):
        refs = {}
        refs["floating_network_id"] = sdk_res["floating_network_id"]
        refs["floating_network_ref"] = reference.network_ref(
            conn, sdk_res["floating_network_id"]
        )
        refs["qos_policy_id"] = sdk_res["qos_policy_id"]
        refs["qos_policy_ref"] = reference.qos_policy_ref(
            conn, sdk_res["qos_policy_id"]
        )
        return refs

    def _refs_from_ser(self, conn):
        refs = {}
        refs["floating_network_ref"] = self.params()["floating_network_ref"]
        refs["floating_network_id"] = reference.network_id(
            conn, self.params()["floating_network_ref"]
        )
        refs["qos_policy_ref"] = self.params()["qos_policy_ref"]
        refs["qos_policy_id"] = reference.qos_policy_id(
            conn, self.params()["qos_policy_ref"]
        )
        return refs
