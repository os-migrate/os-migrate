from __future__ import absolute_import, division, print_function

__metaclass__ = type

import unittest
from unittest import mock

from ansible_collections.os_migrate.os_migrate.plugins.module_utils import (
    const,
    reference,
)


class AttrDict(dict):
    """Dict that also supports attribute access, like openstacksdk resources
    (which are accessed both as res['x'] and res.x in reference.py)."""

    def __getattr__(self, name):
        try:
            return self[name]
        except KeyError:
            raise AttributeError(name)


def make_conn(current_user_id="cur-user", current_project_id="cur-proj"):
    conn = mock.Mock()
    conn.current_user_id = current_user_id
    conn.current_project_id = current_project_id
    return conn


def http_exc(code):
    e = reference.HttpException("boom")
    e.status_code = code
    return e


class TestReferenceAuthShortcuts(unittest.TestCase):

    def test_user_id_with_auth(self):
        ref = {"project_name": None, "name": "%auth%", "domain_name": "%auth%"}
        conn = make_conn(current_user_id="current_user_id")
        self.assertEqual(reference.user_id(conn, ref), "current_user_id")
        self.assertEqual(reference.user_id(conn, ref, none_if_auth=True), None)

    def test_user_ref_with_auth(self):
        expected_ref = {"project_name": None, "name": "%auth%", "domain_name": "%auth%"}
        conn = make_conn(current_user_id="current_user_id")
        self.assertEqual(reference.user_ref(conn, "current_user_id"), expected_ref)

    def test_user_ref_allow_auth_false(self):
        # With allow_auth=False the %auth% shortcut is skipped and a real
        # lookup happens even for the authenticated user.
        conn = make_conn(current_user_id="uid")
        conn.identity.find_user.return_value = AttrDict(name="admin", domain_id="d1")
        conn.identity.find_domain.return_value = AttrDict(name="Default")
        ref = reference.user_ref(conn, "uid", allow_auth=False)
        self.assertEqual(ref["name"], "admin")
        self.assertEqual(ref["domain_name"], "Default")


class TestReferenceFetchId(unittest.TestCase):

    def test_fetch_id_none_ref(self):
        self.assertIsNone(reference.network_id(make_conn(), None))

    def test_fetch_id_simple(self):
        conn = make_conn()
        conn.network.find_network.return_value = AttrDict(id="net-1", name="n")
        ref = {"name": "n", "project_name": None, "domain_name": None}
        self.assertEqual(reference.network_id(conn, ref), "net-1")
        conn.network.find_network.assert_called_once_with("n", ignore_missing=False)

    def test_fetch_id_not_found_returns_none(self):
        conn = make_conn()
        conn.network.find_network.return_value = None
        ref = {"name": "n", "project_name": None, "domain_name": None}
        self.assertIsNone(reference.network_id(conn, ref, required=False))

    def test_fetch_id_with_project_and_domain_filters(self):
        conn = make_conn()
        conn.identity.find_domain.return_value = AttrDict(id="dom-id")
        conn.identity.find_project.return_value = AttrDict(id="proj-id")
        conn.network.find_subnet.return_value = AttrDict(id="sub-1")
        ref = {"name": "s", "project_name": "proj", "domain_name": "dom"}
        self.assertEqual(reference.subnet_id(conn, ref), "sub-1")
        conn.network.find_subnet.assert_called_once_with(
            "s", ignore_missing=False, project_id="proj-id"
        )

    def test_various_id_resolvers_use_right_sdk_method(self):
        conn = make_conn()
        ref = {"name": "x", "project_name": None, "domain_name": None}
        for fn, attr in [
            (reference.router_id, conn.network.find_router),
            (reference.security_group_id, conn.network.find_security_group),
            (reference.segment_id, conn.network.find_segment),
            (reference.subnet_pool_id, conn.network.find_subnet_pool),
            (reference.qos_policy_id, conn.network.find_qos_policy),
            (reference.network_flavor_id, conn.network.find_flavor),
            (reference.flavor_id, conn.compute.find_flavor),
            (reference.domain_id, conn.identity.find_domain),
            (reference.project_id, conn.identity.find_project),
            (reference.role_id, conn.identity.find_role),
        ]:
            attr.reset_mock()
            attr.return_value = AttrDict(id="the-id")
            self.assertEqual(fn(conn, ref), "the-id", msg=fn.__name__)
            attr.assert_called_once_with("x", ignore_missing=False)


class TestReferenceFetchRef(unittest.TestCase):

    def test_fetch_ref_none_id(self):
        self.assertIsNone(reference.network_ref(make_conn(), None))

    def test_fetch_ref_not_found(self):
        conn = make_conn()
        conn.network.find_network.return_value = None
        self.assertIsNone(reference.network_ref(conn, "id", required=False))

    def test_fetch_ref_auth_project(self):
        conn = make_conn(current_project_id="cur-proj")
        conn.network.find_network.return_value = AttrDict(
            name="net1", project_id="cur-proj"
        )
        self.assertEqual(
            reference.network_ref(conn, "net-id"),
            {"name": "net1", "project_name": "%auth%", "domain_name": "%auth%"},
        )

    def test_fetch_ref_other_project(self):
        conn = make_conn(current_project_id="cur-proj")
        conn.network.find_network.return_value = AttrDict(
            name="net1", project_id="other-proj"
        )
        conn.identity.get_project.return_value = AttrDict(name="projX", domain_id="domY")
        conn.identity.get_domain.return_value = AttrDict(name="DomainY")
        self.assertEqual(
            reference.network_ref(conn, "net-id"),
            {"name": "net1", "project_name": "projX", "domain_name": "DomainY"},
        )

    def test_fetch_ref_no_project_info(self):
        # flavor_ref passes get_project_info=False
        conn = make_conn()
        conn.compute.find_flavor.return_value = AttrDict(name="m1.small")
        self.assertEqual(
            reference.flavor_ref(conn, "fl-id"),
            {"name": "m1.small", "project_name": None, "domain_name": None},
        )
        # get_project must not be consulted
        conn.identity.get_project.assert_not_called()

    def test_image_ref_uses_owner_id(self):
        conn = make_conn(current_project_id="cur-proj")
        img = AttrDict(name="cirros", owner_id="other-proj")
        # make it an image instance for the isinstance() branch
        with mock.patch.object(reference, "OPENSTACK_IMAGE_CLASS", AttrDict):
            conn.image.find_image.return_value = img
            conn.identity.get_project.return_value = AttrDict(
                name="imgproj", domain_id="d"
            )
            conn.identity.get_domain.return_value = AttrDict(name="imgdom")
            ref = reference.image_ref(conn, "img-id")
        self.assertEqual(ref["name"], "cirros")
        self.assertEqual(ref["project_name"], "imgproj")


class TestReferenceImageId(unittest.TestCase):

    def test_image_id_single_match(self):
        conn = make_conn()
        conn.image.images.return_value = [AttrDict(id="img-1")]
        ref = {"name": "cirros", "project_name": None, "domain_name": None}
        self.assertEqual(reference.image_id(conn, ref), "img-1")

    def test_image_id_none_ref(self):
        self.assertIsNone(reference.image_id(make_conn(), None))

    def test_image_id_owner_filter_from_auth(self):
        conn = make_conn(current_project_id="cur-proj")
        conn.image.images.return_value = [AttrDict(id="img-1")]
        ref = {"name": "cirros", "project_name": "%auth%", "domain_name": "%auth%"}
        reference.image_id(conn, ref)
        conn.image.images.assert_called_once_with(name="cirros", owner="cur-proj")

    def test_image_id_duplicate_raises(self):
        conn = make_conn()
        conn.image.images.return_value = [AttrDict(id="a"), AttrDict(id="b")]
        ref = {"name": "dup", "project_name": None, "domain_name": None}
        with self.assertRaises(reference.DuplicateResource):
            reference.image_id(conn, ref)

    def test_image_id_not_found_required_raises(self):
        conn = make_conn()
        conn.image.images.return_value = []
        ref = {"name": "missing", "project_name": None, "domain_name": None}
        with self.assertRaises(reference.ResourceFailure):
            reference.image_id(conn, ref, required=True)

    def test_image_id_not_found_optional_none(self):
        conn = make_conn()
        conn.image.images.return_value = []
        ref = {"name": "missing", "project_name": None, "domain_name": None}
        self.assertIsNone(reference.image_id(conn, ref, required=False))


class TestReferenceProjectIdFilters(unittest.TestCase):

    def test_auth_project(self):
        conn = make_conn(current_project_id="cur-proj")
        ref = {"name": "x", "project_name": "%auth%", "domain_name": "%auth%"}
        self.assertEqual(
            reference._project_id_filters(conn, ref), {"project_id": "cur-proj"}
        )

    def test_empty_when_no_project(self):
        conn = make_conn()
        ref = {"name": "x", "project_name": None, "domain_name": None}
        self.assertEqual(reference._project_id_filters(conn, ref), {})

    def test_project_with_domain(self):
        conn = make_conn()
        conn.identity.find_domain.return_value = AttrDict(id="dom-id")
        conn.identity.find_project.return_value = AttrDict(id="proj-id")
        ref = {"name": "x", "project_name": "proj", "domain_name": "dom"}
        self.assertEqual(
            reference._project_id_filters(conn, ref), {"project_id": "proj-id"}
        )
        conn.identity.find_project.assert_called_once_with("proj", domain_id="dom-id")

    def test_domain_403_swallowed(self):
        conn = make_conn()
        conn.identity.find_domain.side_effect = http_exc(403)
        conn.identity.find_project.return_value = AttrDict(id="proj-id")
        ref = {"name": "x", "project_name": "proj", "domain_name": "dom"}
        # domain lookup forbidden -> project looked up without domain filter
        self.assertEqual(
            reference._project_id_filters(conn, ref), {"project_id": "proj-id"}
        )

    def test_domain_non_403_reraised(self):
        conn = make_conn()
        conn.identity.find_domain.side_effect = http_exc(500)
        ref = {"name": "x", "project_name": "proj", "domain_name": "dom"}
        with self.assertRaises(reference.HttpException):
            reference._project_id_filters(conn, ref)

    def test_project_403_swallowed(self):
        conn = make_conn()
        conn.identity.find_project.side_effect = http_exc(403)
        ref = {"name": "x", "project_name": "proj", "domain_name": None}
        self.assertEqual(reference._project_id_filters(conn, ref), {})


class TestReferenceProjectNameAndDomain(unittest.TestCase):

    def test_auth_match(self):
        conn = make_conn(current_project_id="cur-proj")
        self.assertEqual(
            reference._fetch_project_name_and_domain_name(conn, "cur-proj"),
            (const.REF_AUTH, const.REF_AUTH),
        )

    def test_lookup(self):
        conn = make_conn(current_project_id="cur-proj")
        conn.identity.get_project.return_value = AttrDict(name="p", domain_id="d")
        conn.identity.get_domain.return_value = AttrDict(name="dom")
        self.assertEqual(
            reference._fetch_project_name_and_domain_name(conn, "other"), ("p", "dom")
        )

    def test_403_returns_none(self):
        conn = make_conn(current_project_id="cur-proj")
        conn.identity.get_project.side_effect = http_exc(403)
        self.assertEqual(
            reference._fetch_project_name_and_domain_name(conn, "other"), (None, None)
        )

    def test_non_403_reraised(self):
        conn = make_conn(current_project_id="cur-proj")
        conn.identity.get_project.side_effect = http_exc(500)
        with self.assertRaises(reference.HttpException):
            reference._fetch_project_name_and_domain_name(conn, "other")


class TestReferenceIdentityRefs(unittest.TestCase):

    def test_user_ref_non_auth_with_domain(self):
        conn = make_conn(current_user_id="cur-user")
        conn.identity.find_user.return_value = AttrDict(name="bob", domain_id="d1")
        conn.identity.find_domain.return_value = AttrDict(name="Default")
        self.assertEqual(
            reference.user_ref(conn, "other-user"),
            {"name": "bob", "project_name": None, "domain_name": "Default"},
        )

    def test_user_id_non_auth(self):
        conn = make_conn()
        conn.identity.find_user.return_value = AttrDict(id="uid-9")
        ref = {"name": "bob", "project_name": None, "domain_name": None}
        self.assertEqual(reference.user_id(conn, ref), "uid-9")

    def test_role_ref_with_domain(self):
        conn = make_conn()
        conn.identity.find_role.return_value = AttrDict(name="member", domain_id="d1")
        conn.identity.find_domain.return_value = AttrDict(name="Default")
        self.assertEqual(
            reference.role_ref(conn, "role-id"),
            {"name": "member", "project_name": None, "domain_name": "Default"},
        )

    def test_project_ref_with_domain(self):
        conn = make_conn()
        conn.identity.find_project.return_value = AttrDict(name="proj", domain_id="d1")
        conn.identity.find_domain.return_value = AttrDict(name="Default")
        self.assertEqual(
            reference.project_ref(conn, "proj-id"),
            {"name": "proj", "project_name": None, "domain_name": "Default"},
        )

    def test_domain_ref_no_project_info(self):
        conn = make_conn()
        conn.identity.find_domain.return_value = AttrDict(name="Default")
        self.assertEqual(
            reference.domain_ref(conn, "dom-id"),
            {"name": "Default", "project_name": None, "domain_name": None},
        )


class TestReferenceNetworkRefWrappers(unittest.TestCase):
    """The remaining single-line *_ref wrappers (project-scoped resources)."""

    def test_network_ref_wrappers(self):
        conn = make_conn(current_project_id="cur-proj")
        for fn, attr in [
            (reference.network_flavor_ref, conn.network.find_flavor),
            (reference.qos_policy_ref, conn.network.find_qos_policy),
            (reference.router_ref, conn.network.find_router),
            (reference.security_group_ref, conn.network.find_security_group),
            (reference.subnet_ref, conn.network.find_subnet),
            (reference.segment_ref, conn.network.find_segment),
            (reference.subnet_pool_ref, conn.network.find_subnet_pool),
        ]:
            attr.reset_mock()
            # project_id == current -> ref gets the %auth% shortcut
            attr.return_value = AttrDict(name="res", project_id="cur-proj")
            self.assertEqual(
                fn(conn, "the-id"),
                {"name": "res", "project_name": "%auth%", "domain_name": "%auth%"},
                msg=fn.__name__,
            )
