from __future__ import absolute_import, division, print_function

__metaclass__ = type

DOCUMENTATION = r"""
name: stringfilter
short_description: Filter a list of strings or dicts by match queries
version_added: "1.0.0"
description:
  - Filter a list of items according to a list of queries.
  - Values from the input list are kept if they match at least one query.
  - Supports exact string matching and regex matching.
  - When I(attribute) is provided, items are treated as dicts and
    the query is tested against the value at the given key path.
positional: _input
options:
  _input:
    description: The list of strings or dicts to filter.
    type: list
    elements: raw
    required: true
  queries:
    description:
      - A list of match queries. Each query can be a plain string
        (exact match) or a dict with a single C(regex) key whose
        value is a Python regular expression.
    type: list
    elements: raw
    required: true
  attribute:
    description:
      - Dot-separated key path into each dict item.
      - When provided, the query is tested against the value found
        at this path rather than the item itself.
    type: str
"""

EXAMPLES = r"""
- name: Keep only networks whose name matches
  ansible.builtin.set_fact:
    filtered: "{{ networks | os_migrate.os_migrate.stringfilter(queries) }}"
  vars:
    queries:
      - my-network
      - regex: '^test-.*'

- name: Filter dicts by a nested attribute
  ansible.builtin.set_fact:
    filtered: >-
      {{ items | os_migrate.os_migrate.stringfilter(queries,
         attribute='params.name') }}
  vars:
    queries:
      - target-name
"""

RETURN = r"""
_value:
  description: The filtered subset of the input list.
  type: list
  elements: raw
"""

from pprint import pformat
import re

from ansible import errors


def stringfilter(items, queries, attribute=None):
    """Filter a `items` list according to a list of `queries`. Values from
    `items` are kept if they match at least one query. The original
    `items` list is untouched but the result list uses the same data
    (not a deep copy).

    If `attribute` is None, it is assumed that `items` is a list of
    strings to be filtered directly. If `attribute` is provided, it is
    assumed that `items` is a list of dicts, and `queries` will tested
    against value under `attribute` key in each dict.

    `attribute` can point into a nested dictionary, individual keys of
    the nested key path are separated by '.' character.

    `queries` is a list where each item can be:

    - string: String equality match is performed.

    - dict with single key `regex`: The value of `regex` is a Python
      regular expression, and a regex match is performed.

    Returns: a list - subset of `strings` where each item matched one
    or more `queries`

    """
    result = []
    if attribute is not None:
        key_path = attribute.split(".")
    else:
        key_path = None

    for item in items:
        if key_path is not None:
            string = _get_nested_value(item, key_path)
            if not isinstance(string, str):
                raise errors.AnsibleFilterError(
                    f"stringfilter: value under '{attribute}' in '{pformat(item)}' is not string: {pformat(string)}"
                )
        else:
            if not isinstance(item, str):
                raise errors.AnsibleFilterError(
                    f"stringfilter: list item is not string: {pformat(item)}"
                )
            string = item

        for query in queries:
            if isinstance(query, str):
                if query == string:
                    result.append(item)
                    break
            elif isinstance(query, dict) and query.get("regex"):
                if re.search(query["regex"], string):
                    result.append(item)
                    break
            else:
                raise errors.AnsibleFilterError(
                    f"stringfilter: unrecognized query: {pformat(query)}"
                )
    return result


def _get_nested_value(dct, key_path):
    """Get value under `key_path` key in `dct` dictionary.

    `key_path` is a list of keys to be traversed into a potentially
    nested `dct` dictionary.
    """
    key = key_path[0]
    if not isinstance(dct, dict):
        raise errors.AnsibleFilterError(
            f"stringfilter: looking for key '{key}' "
            f"but list item is not dict: {pformat(dct)}"
        )
    if key not in dct:
        raise errors.AnsibleFilterError(
            f"stringfilter: key is '{key}' "
            f"but it was not found in dict: {pformat(dct)}"
        )
    value = dct[key]
    if len(key_path) > 1:
        return _get_nested_value(value, key_path[1:])
    else:
        return value


class FilterModule(object):

    def filters(self):
        return {
            "stringfilter": stringfilter,
        }
