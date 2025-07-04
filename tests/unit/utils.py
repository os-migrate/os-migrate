from __future__ import absolute_import, division, print_function

__metaclass__ = type

import contextlib
import shutil
import tempfile


@contextlib.contextmanager
def tmp_dir_context():
    tmp_dir = tempfile.mkdtemp()
    try:
        yield tmp_dir
    finally:
        shutil.rmtree(tmp_dir)
