The role import_workloads
will validate the serialized data of
the exported workloads, and it will read the exported
metadata.
Then it will start the actual workload migration, it will
first check that both conversion hosts are reachable, then
it will export the selected source guests by exposing its volumes,
transfering them to the destination tenant, and creating a new guest booting
from the recently imported volume.

An instance may carry a mix of local hypervisor disks (migrated with nbdkit
direct, requiring the `import_from_hypervisor` role to have run first) and
attached Cinder volumes (migrated through the conversion hosts). In that case a
single `import_workloads` run transfers both: each local disk is copied with
nbdcopy and each Cinder volume is copied with qemu-img convert via the source
conversion host. Migrating the Cinder volumes still requires a reachable source
conversion host even when `use_nbdkit_direct` is enabled.

For further information about the role import_workloads refer to the
[official docs](https://os-migrate.github.io/os-migrate/roles/role-import_workloads.html).
