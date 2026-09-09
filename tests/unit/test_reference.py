from __future__ import absolute_import, division, print_function

__metaclass__ = type

import unittest
from unittest import mock

from ansible_collections.os_migrate.os_migrate.plugins.module_utils import const
from ansible_collections.os_migrate.os_migrate.plugins.module_utils import reference
from ansible_collections.os_migrate.os_migrate.plugins.module_utils.reference import (
    HttpException,
)


class TestFetchRef(unittest.TestCase):

    def test_none_id_returns_none(self):
        self.assertIsNone(reference._fetch_ref(mock.Mock(), mock.Mock(), None))

    def test_missing_resource_returns_none(self):
        get_method = mock.Mock(return_value=None)
        self.assertIsNone(
            reference._fetch_ref(mock.Mock(), get_method, "uuid-x", required=False)
        )
        get_method.assert_called_once_with("uuid-x", ignore_missing=True)

    def test_without_project_info(self):
        resource = {"name": "net1", "project_id": "uuid-proj"}
        get_method = mock.Mock(return_value=resource)
        ref = reference._fetch_ref(
            mock.Mock(), get_method, "uuid-net", get_project_info=False
        )
        self.assertEqual(
            ref,
            {"name": "net1", "project_name": None, "domain_name": None},
        )

    def test_with_project_info(self):
        resource = mock.MagicMock()
        resource.__getitem__.side_effect = lambda k: {"name": "net1"}[k]
        resource.project_id = "uuid-proj"
        get_method = mock.Mock(return_value=resource)
        conn = mock.Mock()
        with mock.patch.object(
            reference,
            "_fetch_project_name_and_domain_name",
            return_value=("proj", "Default"),
        ) as fetch_proj:
            ref = reference._fetch_ref(conn, get_method, "uuid-net")
        self.assertEqual(
            ref,
            {"name": "net1", "project_name": "proj", "domain_name": "Default"},
        )
        fetch_proj.assert_called_once_with(conn, "uuid-proj")


class TestFetchId(unittest.TestCase):

    def test_none_ref_returns_none(self):
        self.assertIsNone(reference._fetch_id(mock.Mock(), mock.Mock(), None))

    def test_returns_id(self):
        get_method = mock.Mock(return_value={"id": "uuid-found"})
        conn = mock.Mock()
        ref = {
            "name": "net1",
            "project_name": None,
            "domain_name": None,
        }
        with mock.patch.object(reference, "_project_id_filters", return_value={}):
            self.assertEqual(reference._fetch_id(conn, get_method, ref), "uuid-found")
        get_method.assert_called_once_with("net1", ignore_missing=False)

    def test_missing_returns_none(self):
        get_method = mock.Mock(return_value=None)
        ref = {"name": "missing", "project_name": None, "domain_name": None}
        with mock.patch.object(reference, "_project_id_filters", return_value={}):
            self.assertIsNone(
                reference._fetch_id(mock.Mock(), get_method, ref, required=False)
            )


class TestProjectIdFilters(unittest.TestCase):

    def test_auth_project(self):
        conn = mock.Mock()
        conn.current_project_id = "uuid-auth-proj"
        ref = {
            "name": "net1",
            "project_name": const.REF_AUTH,
            "domain_name": const.REF_AUTH,
        }
        self.assertEqual(
            reference._project_id_filters(conn, ref),
            {"project_id": "uuid-auth-proj"},
        )

    def test_named_project_with_domain(self):
        conn = mock.Mock()
        conn.identity.find_domain.return_value = {"id": "uuid-domain"}
        conn.identity.find_project.return_value = {"id": "uuid-proj"}
        ref = {
            "name": "net1",
            "project_name": "myproj",
            "domain_name": "mydomain",
        }
        self.assertEqual(
            reference._project_id_filters(conn, ref),
            {"project_id": "uuid-proj"},
        )
        conn.identity.find_domain.assert_called_once_with("mydomain")
        conn.identity.find_project.assert_called_once_with(
            "myproj", domain_id="uuid-domain"
        )

    def test_no_project_returns_empty(self):
        conn = mock.Mock()
        ref = {"name": "net1", "project_name": None, "domain_name": None}
        self.assertEqual(reference._project_id_filters(conn, ref), {})

    def test_403_on_project_lookup_returns_empty(self):
        conn = mock.Mock()
        err = HttpException()
        err.status_code = 403
        conn.identity.find_project.side_effect = err
        ref = {
            "name": "net1",
            "project_name": "secret",
            "domain_name": None,
        }
        self.assertEqual(reference._project_id_filters(conn, ref), {})


class TestFetchProjectNameAndDomainName(unittest.TestCase):

    def test_auth_project(self):
        conn = mock.Mock()
        conn.current_project_id = "uuid-auth"
        self.assertEqual(
            reference._fetch_project_name_and_domain_name(conn, "uuid-auth"),
            (const.REF_AUTH, const.REF_AUTH),
        )

    def test_other_project(self):
        conn = mock.Mock()
        conn.current_project_id = "uuid-auth"
        project = mock.MagicMock()
        project.__getitem__.side_effect = lambda k: {"name": "other"}[k]
        project.domain_id = "uuid-domain"
        conn.identity.get_project.return_value = project
        conn.identity.get_domain.return_value = {"name": "Default"}
        self.assertEqual(
            reference._fetch_project_name_and_domain_name(conn, "uuid-other"),
            ("other", "Default"),
        )

    def test_403_returns_nones(self):
        conn = mock.Mock()
        conn.current_project_id = "uuid-auth"
        err = HttpException()
        err.status_code = 403
        conn.identity.get_project.side_effect = err
        self.assertEqual(
            reference._fetch_project_name_and_domain_name(conn, "uuid-other"),
            (None, None),
        )
