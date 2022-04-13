from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

from copy import deepcopy

from openstack import exceptions as os_exc
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
    # Some parameters are allowed when creating a resource but not when
    # updating it.  This list of parameter names is purged from the parameter
    # list before calling update.
    readonly_sdk_params = []
    # Some parameters get serialized as e.g. an empty array and it can
    # matter whether they are fed into a create/update request or
    # skipped altogether. Parameters listed here will not be included
    # in sdk_params in case their value is falsey - false, empty
    # array, empty dict etc. (Parameters with None value are skipped
    # anyway and do not need to be listed here.)
    skip_falsey_sdk_params = []
    # Defaults for migration parameters. They are deep-copied into the
    # resource serialization when the resource is being instantiated
    # from_sdk.
    migration_param_defaults = {}

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
        obj.data.setdefault(const.RES_MIGRATION_PARAMS, {})
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
        for k, v in cls.migration_param_defaults.items():
            obj.data[const.RES_MIGRATION_PARAMS][k] = deepcopy(v)
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
        raise NotImplementedError(f"_create_sdk_res not implemented for {cls}.")

    # Must be overriden in child class if `create_or_update` isn't
    # overriden.
    @classmethod
    def _find_sdk_res(cls, conn, name_or_id, filters=None):
        """Find the OpenStack resource of given `name_or_id` which matches a
        Resource subclass.

        Returns: OpenStack SDK object
        """
        raise NotImplementedError(f"_find_sdk_res not implemented for {cls}.")

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
    @classmethod
    def _del_sdk_params_if_falsey(cls, sdk_params, param_names):
        """Delete parameters specified in `param_names` list from `sdk_params`
        dict in case their value is falsey.
        """
        for p_name in param_names:
            if p_name in sdk_params and not sdk_params[p_name]:
                del sdk_params[p_name]

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
    def _update_sdk_res(cls, conn, sdk_res, sdk_params):
        """Update the enclosed OpenStack resource `sdk_res`, use `sdk_params`
        for the update method call.

        Returns: OpenStack SDK object

        """
        raise NotImplementedError(f"_update_sdk_res not implemented for {cls}.")

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
        refs = self._refs_from_ser(conn)
        sdk_params = self._to_sdk_params(refs)
        existing = self._find_sdk_res(conn, sdk_params['name'], filters)
        if existing:
            if self._needs_update(self.from_sdk(conn, existing)):
                self._remove_readonly_params(sdk_params)
                sdk_res = self._update_sdk_res(conn, existing, sdk_params)
                self._hook_after_update(conn, sdk_res, False)
                return True
        else:
            sdk_res = self._create_sdk_res(conn, sdk_params)
            self._hook_after_update(conn, sdk_res, True)
            return True
        return False  # no change done

    def data_errors(self):
        """Get errors in the data structure of a resource, e.g. missing
        fields.

        Returns: list of strings (error messages), empty when the resource is
        well-formed
        """
        errors = self._validation_id_errors()
        errors.extend(self._validation_empty_name_errors())
        errors.extend(self._validation_migration_params_errors())
        errors.extend(self._validation_params_errors())
        return errors

    def debug_id(self):
        """Get best-effort identification of the resource, a string in the
        format 'type:name:id'. Name and id parts can be empty if the
        resource is missing these.

        Returns: string of format 'type:name:id'
        """
        params, info = self.params_and_info()
        name = params.get('name', '')
        id_ = info.get('id', '')
        return f"{self.resource_type}:{name}:{id_}"

    def import_id(self):
        """Get an identity string (somewhat human readable) of the resource
        for import purposes. Trying to import two resources with the
        same import identity means that they would not import as
        separate resources, but rather the 2nd import would try to
        update the resource created by the 1st import (if updating is
        applicable to a given resource type). This generally
        constitues an invalid scenario that should be caught by a
        validation.

        The default ID is constructed from type and name, but some
        resources may need to override this with custom behavior.

        If the ID cannot be constructed, None is returned. This
        generally means that the validation of the resource should
        fail due to a different reason than duplicity, and the message
        about duplicity (e.g. due to multiple resources missing type
        or name fields) would just be distracting from the root cause.

        Returns: string import ID of the resource or None if the ID
        cannot be constructed
        """
        res_type = self.data.get('type', None)
        res_name = self.data.get('params', {}).get('name', None)
        if res_type and res_name:
            return f'{res_type}:{res_name}'
        return None

    def dst_prerequisites_errors(self, conn, filters=None):
        """Get messages for unmet destination cloud prerequisites.

        Returns: list of strings (error messages), empty when prerequisites
        are met
        """
        errors = []
        try:
            self._refs_from_ser(conn)
        except (os_exc.ResourceFailure, os_exc.ResourceNotFound, os_exc.DuplicateResource) as e:
            errors.append(f"Destination prerequisites not met: {e}")
        return errors

    def info(self):
        return self.data[const.RES_INFO]

    def is_data_valid(self):
        """
        Returns: True if resource data is well-formed, False otherwise
        """
        return not self.data_errors()

    # Not meant to be overriden in majority of subclasses.
    def is_same_resource(self, target):
        """Check the `target` dict represents the same data found in the
        resource. Type and id are checked by default.  Custom comparison
        logic can be overridden in _is_same_resource method.

        Returns: True if same, False otherwise
        """
        if isinstance(target, Resource):
            target_data = target.data
        else:
            target_data = target

        # UUID should be enough of a check but just in case we get back to
        # checking by name in the future, let's keep the type check as
        # well, it doesn't hurt.
        if self.data[const.RES_TYPE] != target_data.get(const.RES_TYPE):
            return False

        # if something else than ['type'] && ['_info']['id'] should be the
        # deciding factors for sameness, just override the following method in
        # the specific subclass
        return self._is_same_resource(target_data)

    def migration_params(self):
        return self.data[const.RES_MIGRATION_PARAMS]

    def params(self):
        return self.data[const.RES_PARAMS]

    def params_and_info(self):
        return (self.params(), self.info())

    def type(self):
        return self.data[const.RES_TYPE]

    def update_migration_params(self, params_dict):
        for k, v in params_dict.items():
            # None means we leave the resource class defaults
            if v is not None:
                self.data[const.RES_MIGRATION_PARAMS][k] = v

    # === PRIVATE INSTANCE METHODS (alphabetic sort) ===

    # This method should only be called by when creating subclasses
    # and Resource should not be instantiated directly, not sure if we
    # have a way to enforce that in Python.
    def __init__(self):
        self.data = {
            const.RES_TYPE: None,
            const.RES_PARAMS: {},
            const.RES_INFO: {},
            const.RES_MIGRATION_PARAMS: {},
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
    def _data_without_info(self):
        """Returns: serialized `self.data` with all the '_info' and
        '_migration_params' keys removed, even from nested resources. The
        original `self.data` structure is untouched, but the returned
        structure does reuse data contents to save memory (it is not a
        deep copy). Only lists and dicts are fresh instances.
        """
        def _recursive_trim(obj):
            if isinstance(obj, dict):
                result_dict = {}
                for k, v in obj.items():
                    if k == const.RES_INFO or k == const.RES_MIGRATION_PARAMS:
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

    # May be overridden in subclasses as needed.  The public instance method of
    # the same name without the leading underscore also provides a type
    # comparison before calling this method.
    def _is_same_resource(self, target_data):
        """Check if `target_data` dict is the same resource as self.

        Returns: True if the `target` is the same resource as self.
        """
        # if something else than ['type'] && ['_info']['id'] should be the
        # deciding factors for sameness, just override the following method in
        # the specific subclass
        return (self.data[const.RES_INFO].get('id', '__undefined1__') ==
                target_data[const.RES_INFO].get('id', '__undefined2__'))

    # Meant to be overriden in some subclasses.
    def _hook_after_update(self, conn, sdk_res, is_create):
        """Hook method which runs after the resource has been created or
        updated in the destination cloud. `conn` is SDK connection,
        `sdk_res` is the just created or updated SDK representation of
        the resource, `is_create` tells whether the resource was newly created.
        """
        pass

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

        if self.sdk_params_from_params is None:
            sdk_params_from_params = self.params_from_sdk
        else:
            sdk_params_from_params = self.sdk_params_from_params

        self._set_sdk_params_same_name(self.params(), sdk_params, sdk_params_from_params)
        self._set_sdk_params_same_name(refs, sdk_params, self.sdk_params_from_refs)
        self._del_sdk_params_if_falsey(sdk_params, self.skip_falsey_sdk_params)

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

    # Can be overriden in some subclasses.
    def _validation_id_errors(self):
        """Validate id being present in the resource.

        Returns: list of strings (error messages)
        """
        errors = []
        if 'id' not in self.info():
            errors.append('Missing _info.id.')
        return errors

    # Can be overriden in some subclasses.
    def _validation_migration_params_errors(self):
        """Validate migration params being present in the resource.

        Returns: list of strings (error messages)
        """
        errors = []
        mig_params = self.migration_params()
        for mig_param in self.migration_param_defaults.keys():
            if mig_param not in mig_params:
                errors.append(f'Missing _migration_params.{mig_param}.')
        return errors

    # Can be overriden in some subclasses.
    def _validation_params_errors(self):
        """Validate params being present in the resource.

        Returns: list of strings (error messages)
        """
        errors = []
        params = self.params()
        for param in self.params_from_sdk + self.params_from_refs:
            if param not in params:
                errors.append(f'Missing params.{param}.')
        return errors

    # Can be overridden in some subclasses.
    def _validation_empty_name_errors(self):
        """For resources which have a name property validate that it is non empty

        Returns: list of strings (error messages)
        """
        errors = []
        params = self.params()
        name_param_key = 'name'
        # check to see if this resource has a name
        if name_param_key in self.params_from_sdk:
            # Check to see if name is present and if so is it empty.
            # _validation_params_errors check will catch if it is not present.
            if name_param_key in params.keys() and not params.get(name_param_key, ''):
                errors.append(f'params.{name_param_key} is empty.')
        return errors
