from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

import json
from os import path


class Manifest():

    manifest = None

    def __init__(self):
        if not self.manifest:
            with open(path.join(
                    path.dirname(__file__), '..', '..', 'MANIFEST.json')) as f:
                self.manifest = json.load(f)

    def os_migrate_version(self):
        return self.manifest['collection_info']['version']
