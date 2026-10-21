from __future__ import absolute_import, division, print_function

__metaclass__ = type

import unittest
from unittest import mock

from ansible_collections.os_migrate.os_migrate.plugins.module_utils import (
    const,
    reference,
    network,
    router,
    subnet,
    user,
    project,
    security_group,
    security_group_rule,
    user_project_role_assignment,
    keypair,
    flavor,
)


class AttrDict(dict):
    def __getattr__(self, name):
        try:
            return self[name]
        except KeyError:
            raise AttributeError(name)


# (class, connection service attr, sdk resource name)
STANDARD_WRAPPERS = [
    (network.Network, "network", "network"),
    (router.Router, "network", "router"),
    (user.User, "identity", "user"),
    (project.Project, "identity", "project"),
    (security_group.SecurityGroup, "network", "security_group"),
]


class TestSdkWrappers(unittest.TestCase):
    """_create_sdk_res / _find_sdk_res / _update_sdk_res call the right SDK method."""

    def test_standard_create_find_update(self):
        for cls, svc, name in STANDARD_WRAPPERS:
            conn = mock.Mock()
            svcmock = getattr(conn, svc)
            cls._create_sdk_res(conn, {"a": 1})
            getattr(svcmock, f"create_{name}").assert_called_once_with(a=1)

            cls._find_sdk_res(conn, "nm", {"project_id": "p"})
            getattr(svcmock, f"find_{name}").assert_called_once_with("nm", project_id="p")

            cls._update_sdk_res(conn, "SDK", {"b": 2})
            getattr(svcmock, f"update_{name}").assert_called_once_with("SDK", b=2)

    def test_find_without_filters(self):
        conn = mock.Mock()
        network.Network._find_sdk_res(conn, "nm")
        conn.network.find_network.assert_called_once_with("nm")

    def test_subnet_create_defaults_gateway_ip(self):
        conn = mock.Mock()
        subnet.Subnet._create_sdk_res(conn, {"name": "s"})
        conn.network.create_subnet.assert_called_once_with(name="s", gateway_ip=None)

        conn = mock.Mock()
        subnet.Subnet._create_sdk_res(conn, {"name": "s", "gateway_ip": "1.2.3.4"})
        conn.network.create_subnet.assert_called_once_with(
            name="s", gateway_ip="1.2.3.4"
        )

    def test_subnet_find_update(self):
        conn = mock.Mock()
        subnet.Subnet._find_sdk_res(conn, "s", {"project_id": "p"})
        conn.network.find_subnet.assert_called_once_with("s", project_id="p")
        subnet.Subnet._update_sdk_res(conn, "SDK", {"x": 1})
        conn.network.update_subnet.assert_called_once_with("SDK", x=1)

    def test_keypair_wrappers(self):
        conn = mock.Mock()
        keypair.Keypair._create_sdk_res(
            conn, {"name": "k", "public_key": "x", "type": "ssh"}
        )
        conn.compute.create_keypair.assert_called_once_with(
            name="k", public_key="x", type="ssh"
        )

        keypair.Keypair._find_sdk_res(conn, "k", {"user_id": "u"})
        conn.compute.find_keypair.assert_called_once_with("k", user_id="u")

        # keypairs don't support update: _update_sdk_res returns the resource as-is
        self.assertEqual(keypair.Keypair._update_sdk_res(conn, "SDK", {}), "SDK")

    def test_keypair_create_retries_without_type_on_bad_request(self):
        conn = mock.Mock()
        conn.compute.create_keypair.side_effect = [
            keypair.OPENSTACK_BAD_REQUEST("unsupported type"),
            "KP",
        ]
        result = keypair.Keypair._create_sdk_res(
            conn, {"name": "k", "public_key": "x", "type": "ssh"}
        )
        self.assertEqual(result, "KP")
        self.assertEqual(conn.compute.create_keypair.call_count, 2)
        # second call drops the unsupported "type" kwarg
        kwargs = conn.compute.create_keypair.call_args.kwargs
        self.assertNotIn("type", kwargs)


class TestRouterRefs(unittest.TestCase):

    def test_refs_from_sdk_with_gateway(self):
        conn = mock.Mock()
        sdk = AttrDict(
            external_gateway_info={"network_id": "net-1"}, flavor_id="fl-1"
        )
        with mock.patch.object(reference, "network_ref", return_value="NETREF"), \
                mock.patch.object(reference, "network_flavor_ref", return_value="FLREF"):
            refs = router.Router._refs_from_sdk(conn, sdk)
        self.assertEqual(refs["flavor_id"], "fl-1")
        self.assertEqual(refs["flavor_ref"], "FLREF")
        self.assertEqual(refs["external_gateway_info"], {"network_id": "net-1"})
        self.assertEqual(refs["external_gateway_refinfo"], {"network_ref": "NETREF"})

    def test_refs_from_sdk_no_gateway(self):
        conn = mock.Mock()
        sdk = AttrDict(external_gateway_info=None, flavor_id=None)
        with mock.patch.object(reference, "network_flavor_ref", return_value=None):
            refs = router.Router._refs_from_sdk(conn, sdk)
        self.assertIsNone(refs["external_gateway_refinfo"])
        self.assertIsNone(refs["external_gateway_info"])

    def test_refs_from_ser(self):
        data = {
            const.RES_TYPE: router.Router.resource_type,
            const.RES_INFO: {},
            const.RES_PARAMS: {
                "external_gateway_refinfo": {"network_ref": {"name": "public"}},
                "flavor_ref": {"name": "fl"},
            },
        }
        r = router.Router.from_data(data)
        with mock.patch.object(reference, "network_id", return_value="NID"), \
                mock.patch.object(reference, "network_flavor_id", return_value="FLID"):
            refs = r._refs_from_ser(mock.Mock())
        self.assertEqual(refs["external_gateway_info"], {"network_id": "NID"})
        self.assertEqual(refs["flavor_id"], "FLID")

    def test_refs_from_ser_no_gateway(self):
        data = {
            const.RES_TYPE: router.Router.resource_type,
            const.RES_INFO: {},
            const.RES_PARAMS: {"external_gateway_refinfo": None, "flavor_ref": None},
        }
        r = router.Router.from_data(data)
        with mock.patch.object(reference, "network_flavor_id", return_value=None):
            refs = r._refs_from_ser(mock.Mock())
        self.assertIsNone(refs["external_gateway_info"])


class TestSubnetRefs(unittest.TestCase):

    def test_refs_from_sdk(self):
        conn = mock.Mock()
        sdk = AttrDict(
            network_id="net-1", segment_id="seg-1", subnet_pool_id="pool-1"
        )
        with mock.patch.object(reference, "network_ref", return_value="NETREF"), \
                mock.patch.object(reference, "segment_ref", return_value="SEGREF"), \
                mock.patch.object(reference, "subnet_pool_ref", return_value="POOLREF"):
            refs = subnet.Subnet._refs_from_sdk(conn, sdk)
        self.assertEqual(refs["network_id"], "net-1")
        self.assertEqual(refs["network_ref"], "NETREF")
        self.assertEqual(refs["segment_ref"], "SEGREF")
        self.assertEqual(refs["subnet_pool_ref"], "POOLREF")

    def test_refs_from_ser(self):
        data = {
            const.RES_TYPE: subnet.Subnet.resource_type,
            const.RES_INFO: {},
            const.RES_PARAMS: {
                "network_ref": {"name": "n"},
                "segment_ref": None,
                "subnet_pool_ref": None,
            },
        }
        s = subnet.Subnet.from_data(data)
        with mock.patch.object(reference, "network_id", return_value="NID"), \
                mock.patch.object(reference, "segment_id", return_value=None), \
                mock.patch.object(reference, "subnet_pool_id", return_value=None):
            refs = s._refs_from_ser(mock.Mock())
        self.assertEqual(refs["network_id"], "NID")


class TestSecurityGroupRuleRefs(unittest.TestCase):

    def test_refs_from_sdk(self):
        conn = mock.Mock()
        sdk = AttrDict(security_group_id="sg-1", remote_group_id="sg-2")
        with mock.patch.object(
            reference, "security_group_ref", side_effect=["SGREF", "REMREF"]
        ):
            refs = security_group_rule.SecurityGroupRule._refs_from_sdk(conn, sdk)
        self.assertEqual(refs["security_group_id"], "sg-1")
        self.assertEqual(refs["security_group_ref"], "SGREF")
        self.assertEqual(refs["remote_group_id"], "sg-2")
        self.assertEqual(refs["remote_group_ref"], "REMREF")

    def test_refs_from_ser(self):
        data = {
            const.RES_TYPE: security_group_rule.SecurityGroupRule.resource_type,
            const.RES_INFO: {},
            const.RES_PARAMS: {
                "security_group_ref": {"name": "sg"},
                "remote_group_ref": None,
            },
        }
        r = security_group_rule.SecurityGroupRule.from_data(data)
        with mock.patch.object(
            reference, "security_group_id", side_effect=["SGID", None]
        ):
            refs = r._refs_from_ser(mock.Mock())
        self.assertEqual(refs["security_group_id"], "SGID")
        self.assertIsNone(refs["remote_group_id"])


class TestUserProjectRoleAssignmentRefs(unittest.TestCase):

    def test_refs_from_sdk(self):
        conn = mock.Mock()
        sdk = AttrDict(
            scope={"project": {"id": "proj-1"}},
            role={"id": "role-1"},
            user={"id": "user-1"},
        )
        with mock.patch.object(reference, "project_ref", return_value="PREF"), \
                mock.patch.object(reference, "role_ref", return_value="RREF"), \
                mock.patch.object(reference, "user_ref", return_value="UREF"):
            refs = user_project_role_assignment.UserProjectRoleAssignment._refs_from_sdk(
                conn, sdk
            )
        self.assertEqual(refs["project_id"], "proj-1")
        self.assertEqual(refs["project_ref"], "PREF")
        self.assertEqual(refs["role_id"], "role-1")
        self.assertEqual(refs["user_ref"], "UREF")

    def test_refs_from_ser(self):
        data = {
            const.RES_TYPE: user_project_role_assignment.UserProjectRoleAssignment.resource_type,
            const.RES_INFO: {},
            const.RES_PARAMS: {
                "project_ref": {"name": "p"},
                "role_ref": {"name": "r"},
                "user_ref": {"name": "u"},
            },
        }
        a = user_project_role_assignment.UserProjectRoleAssignment.from_data(data)
        with mock.patch.object(reference, "project_id", return_value="PID"), \
                mock.patch.object(reference, "role_id", return_value="RID"), \
                mock.patch.object(reference, "user_id", return_value="UID"):
            refs = a._refs_from_ser(mock.Mock())
        self.assertEqual(refs["project_id"], "PID")
        self.assertEqual(refs["role_id"], "RID")
        self.assertEqual(refs["user_id"], "UID")


class TestKeypairRefs(unittest.TestCase):

    def test_refs_from_sdk(self):
        conn = mock.Mock()
        sdk = AttrDict(user_id="user-1")
        with mock.patch.object(reference, "user_ref", return_value="UREF"):
            refs = keypair.Keypair._refs_from_sdk(conn, sdk)
        self.assertEqual(refs["user_id"], "user-1")
        self.assertEqual(refs["user_ref"], "UREF")

    def test_refs_from_ser(self):
        data = {
            const.RES_TYPE: keypair.Keypair.resource_type,
            const.RES_INFO: {},
            const.RES_PARAMS: {"user_ref": {"name": "%auth%"}},
        }
        kp = keypair.Keypair.from_data(data)
        with mock.patch.object(reference, "user_id", return_value=None) as uid:
            refs = kp._refs_from_ser(mock.Mock())
        # keypair resolves the user id with none_if_auth=True
        uid.assert_called_once()
        self.assertEqual(refs["user_ref"], {"name": "%auth%"})
        self.assertIsNone(refs["user_id"])


class TestProjectRefs(unittest.TestCase):

    def test_refs_from_sdk_parent_is_project(self):
        conn = mock.Mock()
        sdk = AttrDict(domain_id="dom-1", parent_id="par-1")
        with mock.patch.object(reference, "domain_ref", return_value="DREF"), \
                mock.patch.object(reference, "project_ref", return_value="PARENTPROJ"):
            refs = project.Project._refs_from_sdk(conn, sdk)
        self.assertEqual(refs["domain_id"], "dom-1")
        self.assertEqual(refs["domain_ref"], "DREF")
        self.assertEqual(refs["parent_id"], "par-1")
        self.assertEqual(refs["parent_ref"], "PARENTPROJ")

    def test_refs_from_sdk_parent_is_domain(self):
        conn = mock.Mock()
        sdk = AttrDict(domain_id="dom-1", parent_id="par-1")
        # project_ref returns None -> fall back to domain_ref for the parent
        with mock.patch.object(reference, "domain_ref", return_value="DREF"), \
                mock.patch.object(reference, "project_ref", return_value=None):
            refs = project.Project._refs_from_sdk(conn, sdk)
        self.assertEqual(refs["parent_ref"], "DREF")

    def test_refs_from_ser(self):
        data = {
            const.RES_TYPE: project.Project.resource_type,
            const.RES_INFO: {},
            const.RES_PARAMS: {
                "domain_ref": {"name": "d"},
                "parent_ref": {"name": "p"},
            },
        }
        p = project.Project.from_data(data)
        with mock.patch.object(reference, "domain_id", return_value="DID"), \
                mock.patch.object(reference, "project_id", return_value="PID"):
            refs = p._refs_from_ser(mock.Mock())
        self.assertEqual(refs["domain_id"], "DID")
        self.assertEqual(refs["parent_id"], "PID")


class TestUserRefs(unittest.TestCase):

    def test_refs_from_sdk(self):
        conn = mock.Mock()
        sdk = AttrDict(default_project_id="proj-1", domain_id="dom-1")
        with mock.patch.object(reference, "project_ref", return_value="PREF"), \
                mock.patch.object(reference, "domain_ref", return_value="DREF"):
            refs = user.User._refs_from_sdk(conn, sdk)
        self.assertEqual(refs["default_project_id"], "proj-1")
        self.assertEqual(refs["default_project_ref"], "PREF")
        self.assertEqual(refs["domain_ref"], "DREF")

    def test_refs_from_ser(self):
        data = {
            const.RES_TYPE: user.User.resource_type,
            const.RES_INFO: {},
            const.RES_PARAMS: {
                "default_project_ref": {"name": "p"},
                "domain_ref": {"name": "d"},
            },
        }
        u = user.User.from_data(data)
        with mock.patch.object(reference, "project_id", return_value="PID"), \
                mock.patch.object(reference, "domain_id", return_value="DID"):
            refs = u._refs_from_ser(mock.Mock())
        self.assertEqual(refs["default_project_id"], "PID")
        self.assertEqual(refs["domain_id"], "DID")


class TestFlavor(unittest.TestCase):

    def test_wrappers(self):
        conn = mock.Mock()
        flavor.Flavor._create_sdk_res(conn, {"name": "m1", "ram": 1})
        conn.compute.create_flavor.assert_called_once_with(name="m1", ram=1)
        flavor.Flavor._find_sdk_res(conn, "m1", {"a": 1})
        conn.compute.find_flavor.assert_called_once_with("m1", a=1)
        # flavors are immutable: _update_sdk_res returns the resource unchanged
        self.assertEqual(flavor.Flavor._update_sdk_res(conn, "SDK", {}), "SDK")

    def test_hook_after_update_syncs_extra_specs(self):
        conn = mock.Mock()
        sdk_res = AttrDict(id="fl-1", extra_specs={"keep": "1", "stale": "x"})
        data = {
            const.RES_TYPE: flavor.Flavor.resource_type,
            const.RES_INFO: {},
            const.RES_PARAMS: {"extra_specs": {"keep": "2", "new": "3"}},
        }
        fl = flavor.Flavor.from_data(data)
        fl._hook_after_update(conn, sdk_res, is_create=False)

        # "stale" was removed
        conn.compute.delete_flavor_extra_specs_property.assert_called_once_with(
            "fl-1", "stale"
        )
        # "keep" changed (1 -> 2) and "new" added are both pushed
        updated = {
            c.args[1] for c in conn.compute.update_flavor_extra_specs_property.call_args_list
        }
        self.assertEqual(updated, {"keep", "new"})
