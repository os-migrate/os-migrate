from __future__ import (absolute_import, division, print_function)
__metaclass__ = type


def qos_policy_name(conn, id_, required=True):
    return _fetch_name(conn.network.find_qos_policy, id_, required)


def qos_policy_id(conn, name, required=True):
    return _fetch_id(conn.network.find_qos_policy, name, required)


def _fetch_name(get_method, id_, required=True):
    if id_ is not None:
        return get_method(id_, ignore_missing=not required)['name']


def _fetch_id(get_method, name, required=True):
    if name is not None:
        return get_method(name, ignore_missing=not required)['id']
