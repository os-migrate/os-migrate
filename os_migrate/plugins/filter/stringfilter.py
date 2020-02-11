from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

from pprint import pformat
import re

from ansible import errors


def stringfilter(strings, queries):
    """Filter a `strings` list of strigs according to a list of
    `queries`. Values from `strings` are kept if they match at least
    one query. The original `strings` list is untouched but the result
    list uses the same data (not a deep copy).

    `queries` is a list where each item can be:

    - string: String equality match is performed.

    - dict with single key `regex`: The value of `regex` is a Python
      regular expression, and a regex match is performed.

    Returns: a list - subset of `strings` where each item matched one
    or more `queries`
    """
    result = []
    for s in strings:
        for q in queries:
            if isinstance(q, str):
                if q == s:
                    result.append(s)
                    break
            elif isinstance(q, dict) and q.get('regex'):
                if re.search(q['regex'], s):
                    result.append(s)
                    break
            else:
                raise errors.AnsibleFilterError(
                    "stringfilter: unrecognized query: {0}".format(pformat(q))
                )
    return result


class FilterModule(object):

    def filters(self):
        return {
            'stringfilter': stringfilter,
        }
