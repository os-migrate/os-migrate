The role export_users_keypairs is meant to be run with admin
credentials. It iterates over users (respecting
`os_migrate_users_filter`) and for each user it iterates over Nova
keypairs (respecting `os_migrate_keypairs_filter`), and serializes the
keypairs in the output folder.

For further information about the role export_users_keypairs refer to the
[official docs](https://os-migrate.github.io/os-migrate/roles/role-export_users_keypairs.html).
