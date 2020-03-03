from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

import ansible_collections.os_migrate.os_migrate.plugins.module_utils \
    as collection_utils

class Resource():

    resource_type = 'UNDEFINED'

    # Took the idea of property lists for serialization from Ryan's
    # code, will mark the patch co-authored.

    # Serialization
    params_from_sdk = []
    params_from_ref = []
    info_from_sdk = []
    info_from_refs = []

    # Seserialization
    sdk_params_from_params = []
    sdk_params_from_ref = []

    # This method should only be called by when creating subclasses
    # and Resource should not be instantiated directly, not sure if we
    # have a way to enforce that in Python.
    def __init__():
        self.data = {
            const.RES_TYPE: None,
            const.RES_PARAMS: {},
            const.RES_INFO: {},
        }

    # This constructor will not have to be overriden by child classes,
    # will work OOTB.
    @classmethod
    def from_data(cls, data):
        res_type = data.get('type', None)
        if res_type != self.resource_type:
            raise UnexpectedResourceType(self.resource_type, res_type)

        obj = cls()
        # Barring resource type errors, we allow Resource subclass
        # construction with invalid data so that we don't break on
        # loading a data file, but we explicitly fail with full list
        # of errors (rather than a single exception) when all
        # resources are validated with is_data_valid() and/or
        # data_errors().
        obj.data = data
        # Just in case the data didn't contain those keys (invalid
        # data), set to empty defaults so that all other methods can
        # rely on these existing rather than calling dict.get().
        obj.data.set_default(const.RES_PARAMS, {})
        obj.data.set_default(const.RES_INFO, {})
        return obj

    # I'd rather opt for intra-method composition of superclass
    # private methods than calling the superclass method of the same
    # name.
    @classmethod
    def from_sdk(cls, sdk_resource, conn):
        raise NotImplemented("This method needs to be provided by a subclass")

    def import_or_update(self, conn):
        raise NotImplemented("This method needs to be provided by a subclass")

    def is_data_valid(self):
        len(data_errors()) == 0

    # Common interface for validating the resource definition. If
    # someone edited the resource by hand and made a wrong YAML
    # nesting for example, we should be catching it here.
    def data_errors(self):
        errors = []
        # ... here we validate that params and info exist

    # This is a bit of scifi right now but i could see e.g. Router
    # class being able to validate that the Network/Subnet resoruces
    # referenced from it already exist in the target cloud.
    def are_import_prerequisites_met(self, conn):
        # SCIFI!

    def needs_update(self, target):
        # Check if `sdk_res` needs to be updated to match the state
        # defined in `self`. We just need to move `_trim_info` from
        # serialization.py.
        current_trimmed = _trim_info(current)
        target_trimmed = _trim_info(target)
        return current_trimmed != target_trimmed

    def _data_from_sdk_and_refs(self, sdk_res, refs):
        # we could move these methods from serialization.py to private
        # under Resource
        set_ser_params_same_name(params, sdk_res, self.params_from_sdk)
        set_ser_params_same_name(params, refs, self.params_from_sdk)
        set_ser_params_same_name(info, sdk_res, self.info_from_sdk)
        set_ser_params_same_name(info, refs, self.info_from_refs)

    def _sdk_params_from_params_and_refs(self, sdk_params, refs):
        # we could move these methods from serialization.py to private
        # under Resource
        set_sdk_params_same_name(self.params(), sdk_params, self.sdk_params_from_params)
        set_sdk_params_same_name(refs, sdk_params, self.sdk_params_from_refs)

    def type(self):
        return self.data[const.RES_TYPE]

    def params(self):
        return self.data[const.RES_PARAMS]

    def info(self):
        return self.data[const.RES_INFO]

    def params_and_info(self):
        return (self.params(), self.info())

    def _sort_param(self, param_name):
        self.params()[param_name] = sorted(self.params()[param_name])

    def _sort_param(self, param_name):
        self.info()[param_name] = sorted(self.info()[param_name])


# This would obviously go to network.py but i want to keep the "idea
# pull request" simple.
class Network(Resource):

    params_from_sdk = [
        'description',
        'dns_domain',
        'is_admin_state_up',
        'is_default',
        'is_port_security_enabled',
        'is_router_external',
        'is_shared',
        'is_vlan_transparent',
        'mtu',
        'name',
        'provider_network_type',
        'provider_physical_network',
        'provider_segmentation_id',
        'segments',
    ]
    params_from_refs = [
        'qos_policy_name',
    ]
    info_from_sdk = [
        'availability_zones',
        'created_at',
        'id',
        'project_id',
        'qos_policy_id',
        'revision_number',
        'status',
        'updated_at',
    ]

    sdk_params_from_params = [
        'description',
        'dns_domain',
        'is_admin_state_up',
        'is_default',
        'is_port_security_enabled',
        'is_router_external',
        'is_shared',
        'is_vlan_transparent',
        'mtu',
        'name',
        'provider_network_type',
        'provider_physical_network',
        'provider_segmentation_id',
        'segments',
    ]
    sdk_params_from_refs = [
        'qos_policy_id',
    ]


    @classmethod
    def from_sdk(cls, sdk_resource, conn):
        # >>> Internal composition over inheritance! <<<
        # This is more future-proof, composable, less restrictive
        # approach than calling the same method via super.
        obj = cls()
        obj._data_from_sdk_and_refs(sdk_resource, _refs_from_sdk(sdk_resource, conn))
        # Let's not make special lists for sorted params/info, just sort them?
        obj._sort_param('availability_zone_hints')
        obj._sort_info('subnet_ids')
        return obj

    ## TBD: SOME MORE DRY HERE? Can we refactor something more into reusable bits?
    def import_or_update(self, conn):
        # Again composition over inheritance.
        refs = self._refs_from_ser(conn)
        sdk_params = self._to_sdk_params(net_refs, conn)
        existing = conn.network.find_network(sdk_params['name'])
        if existing:
            if self.needs_update(Network.from_sdk(existing, conn)):
                conn.network.update_network(sdk_params['name'], **sdk_params)
                return True
        else:
            conn.network.create_network(**sdk_params)
            return True
        return False  # no change done
    ### END TBD

    def _to_sdk_params(self, refs):
        # Same here re composition over inheritance. We don't make
        # much use of it here but more complex resources probably
        # will.
        sdk_params = {}
        self._sdk_params_from_params_and_refs(sdk_params, refs)
        return sdk_params

    def _refs_from_sdk(sdk_resource, conn):
        # would be just the same as what we already have in network.py

    def _refs_from_ser(self, conn):
        # would be just the same as what we already have in network.py




# EXAMPLE in import_network module which gets 'data' as a parameter:
net = Network.from_data(data)
# there would be more if/else around this, checking existing network
# perhaps but you get the idea
conn.network.create_network(net.sdk_params(conn))
# perhaps we could even expand to somthing like
net.import_or_update(conn)


# EXAMPLE in export_network which gets name/id
sdk_net = conn.network.find_network(module.params['name'], ignore_missing=False)
net = Network.from_sdk(sdk_net, conn)
filesystem.write_or_replace_resource(module.params['path'], net)
