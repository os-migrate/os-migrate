The role import_workloads
will validate the serialized data of
the exported workloads, and it will read the exported
metadata.
Then it will start the actual workload migration, it will
first check that both conversion hosts are reachable, then
it will export the selected source guests by exposing its volumes,
transfering them to the destination tenant, and creating a new guest booting
from the recently imported volume.

For further information about the role import_workloads refer to the
[official docs](https://os-migrate.github.io/os-migrate/roles/role-import_workloads.html).
