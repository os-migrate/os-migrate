from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

from ansible_collections.os_migrate.os_migrate.plugins.module_utils \
    import const, exc


class Resource():

    # OS-Migrate resource type, checked in from_data constructor
    resource_type = 'UNDEFINED'
    # OpenStack SDK class, checked in from_sdk constructor
    sdk_class = 'UNDEFINED'

    # Properties of SDK resource object that are added to _info
    # section when serializing.
    info_from_sdk = []
    # Items of refs dict (mainly contains names/ids) that are added
    # to _info section when serializing.
    info_from_refs = []
    # Properties of SDK resource object that are added to params
    # section when serializing.
    params_from_sdk = []
    # Items of refs dict (mainly contains names/ids) that are added
    # to params section when serializing.
    params_from_refs = []
    # Serialized params (from params section) that are used as SDK
    # call kwargs when issuing a create/update REST API request. If
    # sdk_params_from_params is kept None, then the params_from_sdk
    # are used instead of it.
    sdk_params_from_params = None
    # Items of refs dict that are used as SDK call kwargs when
    # issuing a create/update REST API request.
    sdk_params_from_refs = []
    # some parameters are allowed when creating a resource but not when
    # updating it.  This list of parameter names is purged from the parameter
    # list before calling update.
    readonly_sdk_params = []

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
        # Disable as per pylint bug, this should be OK.
        # pylint: disable=isinstance-second-argument-not-valid-type
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

    # Must be overriden in child class if `create_or_update` isn't
    # overriden.
    @classmethod
    def _create_sdk_res(cls, conn, sdk_params):
        """Create the OpenStack resource which matches a Resource subclass,
        use `sdk_params` for the creation method call.

        Returns: OpenStack SDK object

        """
        raise NotImplementedError("_create_sdk_res not implemented for {0}."
                                  .format(cls))

    # Must be overriden in child class if `create_or_update` isn't
    # overriden.
    @classmethod
    def _find_sdk_res(cls, conn, name_or_id, filters=None):
        """Find the OpenStack resource of given `name_or_id` which matches a
        Resource subclass.

        Returns: OpenStack SDK object
        """
        raise NotImplementedError("_find_sdk_res not implemented for {0}."
                                  .format(cls))

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

    # Not meant to be overriden in majority of subclasses.
    @staticmethod
    def _sort_dicts(list_of_dicts, by_keys):
        """Sort `list_of_dicts` by dict keys in `by_keys`."""
        def keyfn(dct):
            dct_compound_key = []
            for by_key in by_keys:
                dct_compound_key.append(dct[by_key])
            return dct_compound_key
        return sorted(list_of_dicts, key=keyfn)

    # Must be overriden in child class if `create_or_update` isn't
    # overriden.
    @classmethod
    def _update_sdk_res(cls, conn, name_or_id, sdk_params):
        """Update the OpenStack resource which matches a Resource subclass and
        is identified by `name_or_id`, use `sdk_params` for the
        update method call.

        Returns: OpenStack SDK object
        """
        raise NotImplementedError("_update_sdk_res not implemented for {0}."
                                  .format(cls))

    # ===== PUBLIC INSTANCE METHODS (alphabetic sort) =====

    # Meant to be reused in child classes, but can be overriden
    # completely.
    def create_or_update(self, conn, filters=None):
        """Create the resource `self` in the target OpenStack cloud connection
        `conn`, or update it if it already exists but needs to be
        updated, or do nothing if it already matches desired
        state. Existing resources to be looked up for idempotence
        purposes will be filtered by `filters`.

        Returns: True if any change was made, False otherwise
        """
        refs = self._refs_from_ser(conn, filters)
        sdk_params = self._to_sdk_params(refs)
        existing = self._find_sdk_res(conn, sdk_params['name'], filters)
        if existing:
            if self._needs_update(self.from_sdk(conn, existing)):
                self._remove_readonly_params(sdk_params)
                self._update_sdk_res(conn, sdk_params['name'], sdk_params)
                return True
        else:
            self._create_sdk_res(conn, sdk_params)
            return True
        return False  # no change done

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

    # Not meant to be overriden in majority of subclasses.
    def _remove_readonly_params(self, sdk_params):
        """Remove readonly parameters from the `sdk_params` collection that
        cannot be used for update.

        Returns: filtered dict of parameters
        """
        for name in self.readonly_sdk_params:
            if name in sdk_params:
                sdk_params.pop(name)

    # Used when creating params for SDK calls, should be overriden in
    # majority of child classes.
    def _refs_from_ser(self, conn, filters=None):
        """Create a dictionary of references of `self` using OpenStack SDK
        connection `conn` to fetch any necessary info. Get names from
        `self` and fetch IDs from `conn`. Project-scoped resources to
        be looked up will be filtered by `filters`.

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

        if self.sdk_params_from_params is None:
            sdk_params_from_params = self.params_from_sdk
        else:
            sdk_params_from_params = self.sdk_params_from_params

        self._set_sdk_params_same_name(self.params(), sdk_params, sdk_params_from_params)
        self._set_sdk_params_same_name(refs, sdk_params, self.sdk_params_from_refs)

    # Not meant to be overriden in majority of subclasses.
    def _sort_info(self, info_name, by_keys=None):
        """Sort internal info `info_name`."""
        if by_keys:
            self.info()[info_name] = self._sort_dicts(self.info()[info_name], by_keys)
        else:
            self.info()[info_name] = sorted(self.info()[info_name])

    # Not meant to be overriden in majority of subclasses.
    def _sort_param(self, param_name, by_keys=None):
        """Sort internal param `param_name`."""
        if by_keys:
            self.params()[param_name] = self._sort_dicts(self.params()[param_name], by_keys)
        else:
            self.params()[param_name] = sorted(self.params()[param_name])

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
        contents to save memory (it is not a deep copy). Only lists
        and dicts are fresh instances.
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
