from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

import hashlib
import openstack
import os

from ansible_collections.os_migrate.os_migrate.plugins.module_utils \
    import const, reference, resource


class Image(resource.Resource):

    resource_type = const.RES_TYPE_IMAGE
    sdk_class = openstack.image.v2.image.Image

    info_from_sdk = [
        'checksum',
        'created_at',
        'direct_url',
        'file',
        'id',
        'instance_uuid',
        'kernel_id',
        'locations',
        'metadata',
        'owner_id',  # like project_id in other resources
        'ramdisk_id',
        'schema',
        'size',
        'status',
        'store',
        'updated_at',
        'url',
        'virtual_size',
    ]
    params_from_sdk = [
        'architecture',
        'container_format',
        'disk_format',
        'has_auto_disk_config',
        'hash_algo',
        'hash_value',
        'hw_cpu_cores',
        'hw_cpu_policy',
        'hw_cpu_sockets',
        'hw_cpu_thread_policy',
        'hw_cpu_threads',
        'hw_disk_bus',
        'hw_machine_type',
        'hw_qemu_guest_agent',
        'hw_rng_model',
        'hw_scsi_model',
        'hw_serial_port_count',
        'hw_video_model',
        'hw_video_ram',
        'hw_vif_model',
        'hw_watchdog_action',
        'hypervisor_type',
        'instance_type_rxtx_factor',
        'is_hidden',
        'is_hw_boot_menu_enabled',
        'is_hw_vif_multiqueue_enabled',
        'is_protected',
        'min_disk',
        'min_ram',
        'name',
        'needs_config_drive',
        'needs_secure_boot',
        'os_admin_user',
        'os_command_line',
        'os_distro',
        'os_require_quiesce',
        'os_shutdown_timeout',
        'os_type',
        'os_version',
        'properties',
        'visibility',
        'vm_mode',
        'vmware_adaptertype',
        'vmware_ostype',
    ]
    params_from_refs = [
        'kernel_ref',
        'ramdisk_ref',
    ]
    sdk_params_from_refs = [
        'kernel_id',
        'ramdisk_id',
    ]

    # Some parameters are allowed when reading an image resource but not when
    # creating or updating it.  This list of parameter names is purged from the parameter
    # list before calling create or update and removed from object properties when reading from sdk
    # Attribute 'stores' is read-only now. Due to bug https://bugs.launchpad.net/glance/+bug/1889676 glance now
    # sets stores as a read only property. As such we should remove it from any create or update calls.
    # An existing pattern is to use the readonly_sdk_params list to do this.
    readonly_sdk_params = ["store", "stores"]

    @classmethod
    def from_sdk(cls, conn, sdk_resource):
        obj = super().from_sdk(conn, sdk_resource)
        params = obj.params()
        # We need to remove 'self' from properties as it would break
        # idempotency check and it's not really a property anyway.
        if 'self' in (params.get('properties') or {}).keys():
            del params['properties']['self']
        return obj

    def create_or_update(self, conn, blob_path, filters=None):
        refs = self._refs_from_ser(conn, filters)
        sdk_params = self._to_sdk_params(refs)
        sdk_params['filename'] = blob_path
        existing = self._find_sdk_res(conn, sdk_params['name'], filters)
        if existing:
            if self._needs_update(self.from_sdk(conn, existing)):
                self._remove_readonly_params(sdk_params)
                self._update_sdk_res(conn, existing, sdk_params)
                return True
        else:
            self._create_sdk_res(conn, sdk_params)
            return True
        return False  # no change done

    @classmethod
    def _create_sdk_res(cls, conn, sdk_params):
        # Some params are missing from Glance's automatic type
        # conversion (typically booleans) and just passing
        # e.g. is_protected as kwarg will fail. It seems that it's
        # just better to feed whatever we can via meta.
        meta_keys = set(cls.params_from_sdk)
        meta_keys.remove('name')
        meta = {}
        for key in meta_keys:
            if key in sdk_params:
                meta[key] = sdk_params.pop(key)

        return conn.image.create_image(**sdk_params, meta=meta)

    @staticmethod
    def _find_sdk_res(conn, name_or_id, filters=None):
        # Glance filter require owner instead of project_id.
        glance_filters = dict(filters or {})
        if 'project_id' in glance_filters:
            glance_filters['owner'] = glance_filters.pop('project_id')

        # Unlike other find methods, find_image doesn't support
        # filters, our best option is probably to do a filtered list
        # and then match on name or id.
        images = conn.image.images(**glance_filters)
        for image in images:
            if image['id'] == name_or_id or image['name'] == name_or_id:
                return image
        return None

    @staticmethod
    def _refs_from_sdk(conn, sdk_res):
        refs = {}
        refs['kernel_id'] = sdk_res['kernel_id']
        refs['kernel_ref'] = reference.image_ref(conn, sdk_res['kernel_id'])
        refs['ramdisk_id'] = sdk_res['ramdisk_id']
        refs['ramdisk_ref'] = reference.image_ref(conn, sdk_res['ramdisk_id'])
        return refs

    def _refs_from_ser(self, conn, filters=None):
        refs = {}
        params = self.params()
        refs['kernel_ref'] = params['kernel_ref']
        refs['kernel_id'] = reference.image_id(conn, params['kernel_ref'])
        refs['ramdisk_ref'] = params['ramdisk_ref']
        refs['ramdisk_id'] = reference.image_id(conn, params['ramdisk_ref'])
        return refs

    @staticmethod
    def _update_sdk_res(conn, sdk_res, sdk_params):
        return conn.image.update_image(sdk_res, **sdk_params)

    def _to_sdk_params(self, refs):
        sdk_params = super()._to_sdk_params(refs)
        # Special Glance thing - properties should be specified as
        # kwargs.
        for key, val in (sdk_params.get('properties') or {}).items():
            if key not in self.readonly_sdk_params:
                sdk_params[key] = val
        return sdk_params


def export_blob(conn, sdk_res, path):
    if os.path.exists(path):
        return False

    chunk_size = 1024 * 1024  # 1 MiB
    checksum = hashlib.md5()
    try:
        with open(path, "wb") as image_file:
            response = conn.image.download_image(sdk_res, stream=True)

            for chunk in response.iter_content(chunk_size=chunk_size):
                checksum.update(chunk)
                image_file.write(chunk)

            if response.headers["Content-MD5"] != checksum.hexdigest():
                raise Exception("Downloaded image checksum mismatch")
    except:  # noqa: E722
        # Do not keep incomplete downloads as the idempotence
        # mechanism would consider them successfully downloaded.
        os.remove(path)
        raise

    return True
