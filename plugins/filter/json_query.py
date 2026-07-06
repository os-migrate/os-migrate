from __future__ import absolute_import, division, print_function

__metaclass__ = type

from ansible import errors

try:
    import jmespath
    HAS_JMESPATH = True
except ImportError:
    HAS_JMESPATH = False

DOCUMENTATION = r'''
---
name: json_query
short_description: Select elements from a data structure using a JMESPath expression
version_added: "1.0.0"
description:
  - Query a data structure (list or dict) using a JMESPath expression.
  - Requires the jmespath Python library.
options:
  _input:
    description:
      - The data structure to query.
    type: raw
    required: true
  expr:
    description:
      - A valid JMESPath expression.
    type: str
    required: true
author:
  - os-migrate (@os-migrate)
requirements:
  - jmespath
'''

EXAMPLES = r'''
- name: Extract name and id from a list of dicts
  ansible.builtin.set_fact:
    result: "{{ items | os_migrate.os_migrate.json_query('[*].{name: name, id: id}') }}"

- name: Filter list by attribute value
  ansible.builtin.set_fact:
    result: "{{ items | os_migrate.os_migrate.json_query('[?status==`active`]') }}"
'''

RETURN = r'''
_value:
  description:
    - Result of the JMESPath query.
  type: raw
'''


def json_query(data, expr):
    if not HAS_JMESPATH:
        raise errors.AnsibleFilterError(
            "json_query filter requires the 'jmespath' Python library. "
            "Install it with: pip install jmespath"
        )
    try:
        return jmespath.search(expr, data)
    except jmespath.exceptions.JMESPathError as e:
        raise errors.AnsibleFilterError(
            "json_query: invalid JMESPath expression '%s': %s" % (expr, str(e))
        )


class FilterModule(object):

    def filters(self):
        return {
            "json_query": json_query,
        }
