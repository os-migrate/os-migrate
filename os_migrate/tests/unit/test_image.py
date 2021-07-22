from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

import openstack
import unittest

from ansible_collections.os_migrate.os_migrate.plugins.module_utils \
    import const, image


def sdk_image():
    return openstack.image.v2.image.Image(**{
        'architecture': None,
        'checksum': 'fb49d369b157546e5aeb07327e7666ce',
        'container_format': 'bare',
        'created_at': '2020-06-26T13:50:57Z',
        'direct_url': 'swift+config://ref1/glance/uuid-test-image',
        'disk_format': 'qcow2',
        'file': '/v2/images/uuid-test-image/file',
        'has_auto_disk_config': None,
        'hash_algo': None,
        'hash_value': None,
        'hw_cpu_cores': None,
        'hw_cpu_policy': None,
        'hw_cpu_sockets': None,
        'hw_cpu_thread_policy': None,
        'hw_cpu_threads': None,
        'hw_disk_bus': None,
        'hw_machine_type': None,
        'hw_qemu_guest_agent': None,
        'hw_rng_model': None,
        'hw_scsi_model': None,
        'hw_serial_port_count': None,
        'hw_video_model': None,
        'hw_video_ram': None,
        'hw_vif_model': None,
        'hw_watchdog_action': None,
        'hypervisor_type': None,
        'id': 'uuid-test-image',
        'instance_type_rxtx_factor': None,
        'instance_uuid': None,
        'is_hidden': None,
        'is_hw_boot_menu_enabled': None,
        'is_hw_vif_multiqueue_enabled': None,
        'is_protected': False,
        'kernel_id': 'uuid-test-kernel',
        'locations': None,
        'metadata': None,
        'min_disk': 20,
        'min_ram': 4096,
        'name': 'test-image',
        'needs_config_drive': None,
        'needs_secure_boot': None,
        'os_admin_user': None,
        'os_command_line': None,
        'os_distro': None,
        'os_require_quiesce': None,
        'os_shutdown_timeout': None,
        'os_type': None,
        'os_version': None,
        'owner_id': 'uuid-test-project',
        'ramdisk_id': 'uuid-test-ramdisk',
        'schema': '/v2/schemas/image',
        'size': 1248591872,
        'status': 'active',
        'store': None,
        'tags': [],
        'updated_at': '2020-06-26T13:55:52Z',
        'url': None,
        'virtual_size': None,
        'visibility': 'public',
        'vm_mode': None,
        'vmware_adaptertype': None,
        'vmware_ostype': None,
    })


def serialized_image():
    return {
        const.RES_PARAMS: {
            'architecture': None,
            'container_format': 'bare',
            'disk_format': 'qcow2',
            'has_auto_disk_config': None,
            'hash_algo': None,
            'hash_value': None,
            'hw_cpu_cores': None,
            'hw_cpu_policy': None,
            'hw_cpu_sockets': None,
            'hw_cpu_thread_policy': None,
            'hw_cpu_threads': None,
            'hw_disk_bus': None,
            'hw_machine_type': None,
            'hw_qemu_guest_agent': None,
            'hw_rng_model': None,
            'hw_scsi_model': None,
            'hw_serial_port_count': None,
            'hw_video_model': None,
            'hw_video_ram': None,
            'hw_vif_model': None,
            'hw_watchdog_action': None,
            'hypervisor_type': None,
            'instance_type_rxtx_factor': None,
            'is_hidden': None,
            'is_hw_boot_menu_enabled': None,
            'is_hw_vif_multiqueue_enabled': None,
            'is_protected': False,
            'kernel_ref': {
                'name': 'test-kernel',
                'project_name': 'test-project',
                'domain_name': 'Default',
            },
            'min_disk': 20,
            'min_ram': 4096,
            'name': 'test-image',
            'needs_config_drive': None,
            'needs_secure_boot': None,
            'os_admin_user': None,
            'os_command_line': None,
            'os_distro': None,
            'os_require_quiesce': None,
            'os_shutdown_timeout': None,
            'os_type': None,
            'os_version': None,
            'properties': None,
            'ramdisk_ref': {
                'name': 'test-ramdisk',
                'project_name': 'test-project',
                'domain_name': 'Default',
            },
            'visibility': 'public',
            'vm_mode': None,
            'vmware_adaptertype': None,
            'vmware_ostype': None,
        },
        const.RES_INFO: {
            'checksum': 'fb49d369b157546e5aeb07327e7666ce',
            'created_at': '2020-06-26T13:50:57Z',
            'direct_url': 'swift+config://ref1/glance/uuid-test-image',
            'file': '/v2/images/uuid-test-image/file',
            'id': 'uuid-test-image',
            'instance_uuid': None,
            'kernel_id': 'uuid-test-kernel',
            'locations': None,
            'metadata': None,
            'owner_id': 'uuid-test-project',
            'ramdisk_id': 'uuid-test-ramdisk',
            'schema': '/v2/schemas/image',
            'size': 1248591872,
            'status': 'active',
            'store': None,
            'updated_at': '2020-06-26T13:55:52Z',
            'url': None,
            'virtual_size': None,
        },
        const.RES_TYPE: 'openstack.image.Image',
    }


def image_refs():
    return {
        'kernel_id': 'uuid-test-kernel',
        'kernel_ref': {
            'name': 'test-kernel',
            'project_name': 'test-project',
            'domain_name': 'Default',
        },
        'ramdisk_id': 'uuid-test-ramdisk',
        'ramdisk_ref': {
            'name': 'test-ramdisk',
            'project_name': 'test-project',
            'domain_name': 'Default',
        },
    }


# "Disconnected" variant of Image resource where we make sure not to
# make requests using `conn`.
class Image(image.Image):

    def _refs_from_ser(self, conn):
        return image_refs()

    @staticmethod
    def _refs_from_sdk(conn, sdk_res):
        return image_refs()


class TestImage(unittest.TestCase):

    # see full diffs in test errors
    maxDiff = None

    def test_serialize_image(self):
        image_data = sdk_image()
        serialized = Image.from_sdk(None, image_data)
        params, info = serialized.params_and_info()

        self.assertEqual(serialized.type(), 'openstack.image.Image')
        self.assertEqual(params, serialized_image()['params'])
        self.assertEqual(info, serialized_image()['_info'])

    def test_deserialize_image(self):
        ser = Image.from_data(serialized_image())
        params = ser.params()
        refs = ser._refs_from_ser(None)  # conn=None
        sdk_params = ser._to_sdk_params(refs)

        self.assertEqual(sdk_params['kernel_id'], refs['kernel_id'])
        self.assertEqual(sdk_params['min_disk'], params['min_disk'])
        self.assertEqual(sdk_params['min_ram'], params['min_ram'])
        self.assertEqual(sdk_params['name'], params['name'])
        self.assertEqual(sdk_params['ramdisk_id'], refs['ramdisk_id'])
