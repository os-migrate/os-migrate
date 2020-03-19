from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

import openstack

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


def security_group_rule_refs():
    return {
        'security_group_name': 'default',
        'remote_group_name': 'default',
    }


def sdk_security_group():
    return openstack.network.v2.security_group.SecurityGroup(
        description='Default security group',
        name='default',
        id='uuid',
        project_id='uuid-project',
        created_at='2020-01-30T14:49:06Z',
        updated_at='2020-01-30T14:49:06Z',
        tenant_id='uuid-tenant',
        revision_number='1',
    )


def serialized_security_group():
    return {
        const.RES_PARAMS: {
            'description': 'Default security group',
            'name': 'default',
        },
        const.RES_INFO: {
            'id': 'uuid',
            'project_id': 'uuid-project',
            'created_at': '2020-01-30T14:49:06Z',
            'updated_at': '2020-01-30T14:49:06Z',
            'tenant_id': 'uuid-tenant',
            'revision_number': '0',
        },
        const.RES_TYPE: 'openstack.network.SecurityGroup',
    }


def sdk_security_group_rule():
    return openstack.network.v2.security_group_rule.SecurityGroupRule(
        id='uuid',
        security_group_id='uuid-sec-group',
        security_group_name='default',
        remote_group_id='uuid-group',
        remote_group_name='default',
        project_id='uuid-project',
        created_at='2020-01-30T14:49:06Z',
        updated_at='2020-01-30T14:49:06Z',
        revision_number='0',
        description='null',
        direction='ingress',
        port_range_max='100',
        port_range_min='10',
        protocol='null',
        remote_ip_prefix='null',
    )


def serialized_security_group_rule():
    return {
        const.RES_PARAMS: {
            'description': 'null',
            'direction': 'ingress',
            'port_range_max': '100',
            'port_range_min': '10',
            'protocol': 'null',
            'remote_ip_prefix': 'null',
        },
        const.RES_INFO: {
            'id': 'uuid',
            'security_group_id': 'uuid-sec-group',
            'remote_group_id': 'uuid-group',
            'project_id': 'uuid-project',
            'created_at': '2020-01-30T14:49:06Z',
            'updated_at': '2020-01-30T14:49:06Z',
            'revision_number': '0',
        },
        const.RES_TYPE: 'openstack.network.SecurityGroupRule',
    }
