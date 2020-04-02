from __future__ import (absolute_import, division, print_function)
__metaclass__ = type


from ansible_collections.os_migrate.os_migrate.plugins.module_utils \
    import const


def minimal_resource():
    return {
        const.RES_TYPE: 'openstack.Minimal',
        const.RES_PARAMS: {
            'name': 'minimal',
            'description': 'minimal resource',
        },
        const.RES_INFO: {
            'id': 'id-minimal',
            'detail': 'not important for import and idempotence',
        },
    }


def minimal_resource_file_struct():
    return {
        'os_migrate_version': const.OS_MIGRATE_VERSION,
        'resources': [minimal_resource()],
    }


def resource_with_nested():
    return {
        const.RES_TYPE: 'openstack.WithNested',
        const.RES_PARAMS: {
            'name': 'with-nested',
            'description': 'resource with nested resources',
            'subresources': [
                {
                    const.RES_TYPE: 'openstack.Nested',
                    const.RES_PARAMS: {
                        'name': 'nested-1',
                    },
                    const.RES_INFO: {
                        'id': 'id-nested-1',
                        'nested-detail': 'not important',
                    },
                },
                {
                    const.RES_TYPE: 'openstack.Nested',
                    const.RES_PARAMS: {
                        'name': 'nested-2',
                    },
                    const.RES_INFO: {
                        'id': 'id-nested-2',
                        'nested-detail': 'also not important',
                    },
                },
            ],
        },
        const.RES_INFO: {
            'id': 'id-with-nested',
            'detail': 'not important for import and idempotence',
        },
    }
