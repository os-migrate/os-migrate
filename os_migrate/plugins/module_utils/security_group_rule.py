from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

import openstack

from ansible_collections.os_migrate.os_migrate.plugins.module_utils \
    import const, reference, resource


class SecurityGroupRule(resource.Resource):

    resource_type = const.RES_TYPE_SECURITYGROUPRULE
    sdk_class = openstack.network.v2.security_group_rule.SecurityGroupRule

    info_from_sdk = [
        'id',
        'security_group_id',
        'remote_group_id',
        'project_id',
        'created_at',
        'updated_at',
        'revision_number',
    ]
    params_from_sdk = [
        'description',
        'direction',
        'ether_type',
        'port_range_max',
        'port_range_min',
        'protocol',
        'remote_ip_prefix',
    ]

    params_from_refs = [
        'security_group_name',
        'remote_group_name',
    ]

    sdk_params_from_refs = [
        'security_group_id',
        'remote_group_id',
    ]

    @classmethod
    def from_sdk(cls, conn, sdk_resource):
        obj = super(SecurityGroupRule, cls).from_sdk(conn, sdk_resource)
        return obj

    # there is no API method for updating security group rules.  if you
    # attempt to create a rule that exists, a ConflictException is raised.
    def create_or_update(self, conn, filters=None):
        refs = self._refs_from_ser(conn, filters)
        sdk_params = self._to_sdk_params(refs)
        try:
            conn.network.create_security_group_rule(**sdk_params)
            return True
        except openstack.exceptions.ConflictException:
            # TODO: Log that the security group rule already exists
            return False

    @staticmethod
    def _refs_from_sdk(conn, sdk_res):
        refs = {}
        refs['security_group_id'] = sdk_res['security_group_id']
        refs['security_group_name'] = reference.security_group_name(
            conn, sdk_res['security_group_id'])
        refs['remote_group_name'] = reference.security_group_name(
            conn, sdk_res['remote_group_id'])
        refs['remote_group_id'] = reference.security_group_id(
            conn, sdk_res['security_group_id'])
        return refs

    def _refs_from_ser(self, conn, filters=None):
        refs = {}
        refs['security_group_name'] = self.params()['security_group_name']
        refs['security_group_id'] = reference.security_group_id(
            conn, self.params()['security_group_name'], filters)
        refs['remote_group_name'] = self.params()['remote_group_name']
        refs['remote_group_id'] = reference.security_group_id(
            conn, self.params()['remote_group_name'], filters)

        return refs
