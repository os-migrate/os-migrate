Troubleshooting
===============

General tips
------------

-  Run ``ansible-playbook`` with ``-v`` parameter to get more detailed
   output.

Common issues
-------------

-  ``DataVersionMismatch: OS Migrate runtime is version 'X.Y.Z', but
   tried to parse data file 'abc.yml' with os_migrate_version field
   set to 'A.B.C'. (Exported data is not guaranteed to be compatible
   across versions. After upgrading OS Migrate, make sure to remove
   the old YAML exports from the data directory.)``

   When OS Migrate export playbooks run, the existing data files
   aren't automatically truncated. OS Migrate gradually adds each
   resource serialization to the (perhaps existing) YAML file, or it
   updates a resource serialization if one with the same ID is already
   present in the file.

   OS Migrate will refuse to parse YAML files which were created with
   a different version. In many cases such parsing would "just work",
   but not always, so OS Migrate is being defensive and requires
   clearing out the data directory when upgrading to a new version,
   and re-running the export playbooks.

   Alternatively, an advanced user can verify that the previous and
   new OS Migrate does not include any change in export data
   structures, and can edit the ``os_migrate_version`` field in the
   data files. This option should be used with caution, but it may
   prove useful in special scenarios, e.g. if external causes prevent
   re-exporting the data.
