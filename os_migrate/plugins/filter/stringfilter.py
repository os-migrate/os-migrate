from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

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

    `queries` is a list where each item can be:

    - string: String equality match is performed.

    - dict with single key `regex`: The value of `regex` is a Python
      regular expression, and a regex match is performed.

    Returns: a list - subset of `strings` where each item matched one
    or more `queries`

    """
    result = []
    for item in items:
        if attribute is not None:
            if not isinstance(item, dict):
                raise errors.AnsibleFilterError(
                    "stringfilter: 'attribute' parameter provided "
                    "but list item is not dict: {0}".format(pformat(item))
                )
            if attribute not in item:
                raise errors.AnsibleFilterError(
                    "stringfilter: 'attribute' is {0} "
                    "but it was not found in list item: {1}"
                    .format(pformat(attribute), pformat(item))
                )
            string = item[attribute]
        else:
            if not isinstance(item, str):
                raise errors.AnsibleFilterError(
                    "stringfilter: list item is not string: {0}"
                    .format(pformat(item))
                )
            string = item

        for query in queries:
            if isinstance(query, str):
                if query == string:
                    result.append(item)
                    break
            elif isinstance(query, dict) and query.get('regex'):
                if re.search(query['regex'], string):
                    result.append(item)
                    break
            else:
                raise errors.AnsibleFilterError(
                    "stringfilter: unrecognized query: {0}"
                    .format(pformat(query))
                )
    return result


class FilterModule(object):

    def filters(self):
        return {
            'stringfilter': stringfilter,
        }
