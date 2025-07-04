from __future__ import absolute_import, division, print_function

__metaclass__ = type

import openstack

from ansible_collections.os_migrate.os_migrate.plugins.module_utils import (
    common,
    const,
    reference,
    resource,
)


class Subnet(resource.Resource):
    resource_type = const.RES_TYPE_SUBNET
    sdk_class = openstack.network.v2.subnet.Subnet

    info_from_sdk = [
        "created_at",
        "id",
        "network_id",
        "prefix_length",
        "project_id",
        "revision_number",
        "segment_id",
        "subnet_pool_id",
        "updated_at",
    ]

    params_from_sdk = [
        "allocation_pools",
        "cidr",
        "description",
        "dns_nameservers",
        "gateway_ip",
        "host_routes",
        "ip_version",
        "ipv6_address_mode",
        "ipv6_ra_mode",
        "is_dhcp_enabled",
        "name",
        "service_types",
        "tags",
        "use_default_subnet_pool",
    ]

    sdk_params_from_params = [x for x in params_from_sdk if x not in ["tags"]]

    params_from_refs = ["network_ref", "segment_ref", "subnet_pool_ref"]

    sdk_params_from_refs = [
        "network_id",
        "segment_id",
        "subnet_pool_id",
    ]

    readonly_sdk_params = ["network_id", "project_id"]

    @classmethod
    def from_sdk(cls, conn, sdk_resource):
        obj = super(Subnet, cls).from_sdk(conn, sdk_resource)
        obj._sort_param("allocation_pools", by_keys=["start", "end"])
        obj._sort_param("dns_nameservers")
        obj._sort_param("host_routes", by_keys=["destination", "nexthop"])
        return obj

    @staticmethod
    def _create_sdk_res(conn, sdk_params):
        return conn.network.create_subnet(**sdk_params)

    @staticmethod
    def _find_sdk_res(conn, name_or_id, filters=None):
        return conn.network.find_subnet(name_or_id, **(filters or {}))

    def _hook_after_update(self, conn, sdk_res, is_create):
        common.neutron_set_tags(conn, sdk_res, self.params()["tags"])

    @staticmethod
    def _update_sdk_res(conn, sdk_res, sdk_params):
        return conn.network.update_subnet(sdk_res, **sdk_params)

    @staticmethod
    def _refs_from_sdk(conn, sdk_res):
        refs = {}
        refs["network_id"] = sdk_res["network_id"]
        refs["network_ref"] = reference.network_ref(conn, sdk_res["network_id"])
        refs["segment_id"] = sdk_res["segment_id"]
        refs["segment_ref"] = reference.segment_ref(conn, sdk_res["segment_id"])
        refs["subnet_pool_id"] = sdk_res["subnet_pool_id"]
        refs["subnet_pool_ref"] = reference.subnet_pool_ref(
            conn, sdk_res["subnet_pool_id"]
        )
        return refs

    def _refs_from_ser(self, conn):
        refs = {}
        refs["network_ref"] = self.params()["network_ref"]
        refs["network_id"] = reference.network_id(conn, self.params()["network_ref"])
        refs["segment_ref"] = self.params()["segment_ref"]
        refs["segment_id"] = reference.segment_id(conn, self.params()["segment_ref"])
        refs["subnet_pool_ref"] = self.params()["subnet_pool_ref"]
        refs["subnet_pool_id"] = reference.subnet_pool_id(
            conn, self.params()["subnet_pool_ref"]
        )
        return refs
