from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

from ansible_collections.os_migrate.os_migrate.plugins.module_utils \
    import const, exc


class Resource():

    resource_type = 'UNDEFINED'
    sdk_class = 'UNDEFINED'

    info_from_sdk = []
    info_from_refs = []
    params_from_sdk = []
    params_from_refs = []
    sdk_params_from_refs = []

    # ===== PUBLIC CLASS/STATIC METHODS (alphabetic sort) =====

    # This constructor should work OOTB in all cases, shouldn't be
    # overriden in child classes.
    @classmethod
    def from_data(cls, data):
        """Returns: a new Resource instance with internal data set from `data`
        parameter.
        """
        res_type = data.get('type', None)
        if res_type != cls.resource_type:
            raise exc.UnexpectedResourceType(cls.resource_type, res_type)

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
        obj.data.setdefault(const.RES_PARAMS, {})
        obj.data.setdefault(const.RES_INFO, {})
        return obj

    # Meant to be extended in child classes, but can be overriden
    # completely.
    @classmethod
    def from_sdk(cls, conn, sdk_resource):
        """Returns: a new Resource instance intitalized from `sdk_resource`,
        using `conn` OpenStack SDK connection to fetch any additional
        information.
        """
        if not isinstance(sdk_resource, cls.sdk_class):
            raise exc.UnexpectedResourceType(
                cls.sdk_class, sdk_resource.__class__)

        obj = cls()
        obj._data_from_sdk_and_refs(
            sdk_resource, cls._refs_from_sdk(conn, sdk_resource))
        obj.data['type'] = cls.resource_type
        return obj

    # === PRIVATE CLASS/STATIC METHODS (alphabetic sort) ===

    # Used when creating Resource from SDK object, should be overriden
    # in majority of child classes.
    @staticmethod
    def _refs_from_sdk(conn, sdk_res):
        """Create a dictionary of references from OpenStack SDK resource
        instance `sdk_res` and OpenStack SDK connection `conn`. Get
        IDs from `sdk_res` and fetch names from `conn`.

        Returns: dict with names and ids
        """
        return {}

    # Not meant to be overriden in majority of subclasses.
    @classmethod
    def _set_sdk_params_same_name(cls, ser_params, sdk_params, param_names):
        """Copy values from `ser_params` into `sdk_params` for all keys in
        `param_names` (list of strings), only for values in `ser_params`
        which aren't None.
        """
        for p_name in param_names:
            cls._set_sdk_param(ser_params, p_name, sdk_params, p_name)

    # Not meant to be overriden in majority of subclasses.
    @staticmethod
    def _set_sdk_param(ser_params, ser_key, sdk_params, sdk_key):
        """Assign value from `ser_key` in `ser_params` dict as value for
        `sdk_key` in `sdk_params`, but only if it isn't None.
        """
        if ser_params.get(ser_key, None) is not None:
            sdk_params[sdk_key] = ser_params[ser_key]

    # Not meant to be overriden in majority of subclasses.
    @staticmethod
    def _set_ser_params_same_name(ser_params, sdk_params, param_names):
        """Copy values from `sdk_params` to `ser_params` for keys listed in
        `param_names` (list of strings).
        """
        for p_name in param_names:
            ser_params[p_name] = sdk_params[p_name]

    # ===== PUBLIC INSTANCE METHODS (alphabetic sort) =====

    # Meant to be reused in child classes, but can be overriden
    # completely.
    def create_or_update(self, conn):
        """Create the resource `self` in the target OpenStack cloud connection
        `conn`, or update it if it already exists but needs to be
        updated, or do nothing if it already matches desired state.

        Returns: True if any change was made, False otherwise
        """
        # TODO: It would be nice to provide a default implementation
        # here, we'll have to do some dynamic method lookup though,
        # because we need to reference methods under conn (runtime
        # object), so AFAICT we cannot simply point to something
        # static in OpenStack SDK.
        return False

    def info(self):
        return self.data[const.RES_INFO]

    def params(self):
        return self.data[const.RES_PARAMS]

    def params_and_info(self):
        return (self.params(), self.info())

    def type(self):
        return self.data[const.RES_TYPE]

    # TODO add validation
    # def is_data_valid(self):
    # def data_errors(self):
    # def are_prerequisites_met(self, conn):

    # === PRIVATE INSTANCE METHODS (alphabetic sort) ===

    # This method should only be called by when creating subclasses
    # and Resource should not be instantiated directly, not sure if we
    # have a way to enforce that in Python.
    def __init__(self):
        self.data = {
            const.RES_TYPE: None,
            const.RES_PARAMS: {},
            const.RES_INFO: {},
        }

    # Not meant to be overriden in majority of subclasses.
    def _data_from_sdk_and_refs(self, sdk_res, refs):
        """Fill `self` internal params and info structures with values from
        `sdk_res` and `refs`.
        """
        params, info = self.params_and_info()
        self._set_ser_params_same_name(params, sdk_res, self.params_from_sdk)
        self._set_ser_params_same_name(params, refs, self.params_from_refs)
        self._set_ser_params_same_name(info, sdk_res, self.info_from_sdk)
        self._set_ser_params_same_name(info, refs, self.info_from_refs)

    # Not meant to be overriden in majority of subclasses.
    def _needs_update(self, target):
        """Check if `target` resource needs to be updated to match the state
        defined in `self`.

        Returns: True if `target` needs to be updated, False otherwise
        """
        return self._data_without_info() != target._data_without_info()

    # Used when creating params for SDK calls, should be overriden in
    # majority of child classes.
    def _refs_from_ser(self, conn):
        """Create a dictionary of references of `self` using OpenStack SDK
        connection `conn` to fetch any necessary info. Get names from
        `self` and fetch IDs from `conn`.

        Returns: dict with names and ids
        """
        return {}

    # Not meant to be overriden in majority of subclasses.
    def _sdk_params_from_params_and_refs(self, sdk_params, refs):
        """Fill `sdk_params` with values from `self` internal parameters and
        from `refs`.
        """
        # we could move these methods from serialization.py to private
        # under Resource
        self._set_sdk_params_same_name(self.params(), sdk_params, self.params_from_sdk)
        self._set_sdk_params_same_name(refs, sdk_params, self.sdk_params_from_refs)

    # Not meant to be overriden in majority of subclasses.
    def _sort_param(self, param_name):
        """Sort internal param `param_name`."""
        self.params()[param_name] = sorted(self.params()[param_name])

    # Not meant to be overriden in majority of subclasses.
    def _sort_info(self, info_name):
        """Sort internal info `info_name`."""
        self.info()[info_name] = sorted(self.info()[info_name])

    # Not meant to be overriden in majority of subclasses.
    def _to_sdk_params(self, refs):
        """Returns: dict - `self` formatted as creation/update params for
        OpenStack SDK API call.
        """
        sdk_params = {}
        self._sdk_params_from_params_and_refs(sdk_params, refs)
        return sdk_params

    # Not meant to be overriden in majority of subclasses.
    def _data_without_info(self):
        """Returns: serialized `self.data` with all the '_info' keys removed,
        even from nested resources. The original `self.data` structure
        is untouched, but the returned structure does reuse data
        contents to save memory (it is not a deep copy).
        """
        def _recursive_trim(obj):
            if isinstance(obj, dict):
                result_dict = {}
                for k, v in obj.items():
                    if k == const.RES_INFO:
                        continue
                    result_dict[k] = _recursive_trim(v)
                return result_dict
            elif isinstance(obj, list):
                result_list = []
                for item in obj:
                    result_list.append(_recursive_trim(item))
                return result_list
            else:
                return obj

        return _recursive_trim(self.data)
