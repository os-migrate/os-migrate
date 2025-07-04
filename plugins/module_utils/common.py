from __future__ import absolute_import, division, print_function

__metaclass__ = type


def neutron_set_tags(conn, sdk_res, tags):
    """Function to be used with Neutron service resources. Use `conn`
    connection to set `tags` on `sdk_res`, only if the current set of
    tags on `sdk_res` differs from `tags`.
    """
    sorted_actual = sorted(sdk_res["tags"])
    sorted_expected = sorted(tags)
    if sorted_actual != sorted_expected:
        conn.network.set_tags(sdk_res, sorted_expected)
