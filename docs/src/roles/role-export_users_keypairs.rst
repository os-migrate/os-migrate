============================
Role - export_users_keypairs
============================

This role is meant to be run with admin privileges. It imports Nova
keypairs matching ``os_migrate_keypairs_filter`` for all users
matching ``os_migrate_users_filter``.

When using this role, make sure you have recent enough OpenStack SDK
(0.57+).

.. ansibleautoplugin::
  :role: roles/export_users_keypairs
