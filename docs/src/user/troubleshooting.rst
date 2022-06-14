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

- ``AnsibleCensoringStringIssue: workloads.yml setup task altering
  log_file path during preliminary import workload steps. (As a 
  result susequent import tasks are failing due to non-existent path
  error.)``

  OS Migrate uses OpenStack modules to build their argument spec by 
  using a function in OpenStack module utils. When project names are
  marked as ``no_log`` it causes values to be censored in the 
  response. This is seen here in the import workloads setup task  where
  ``/home/project_name/workloads/import_workloads.yml`` becomes 
  ``/home/******/workloads/import_workloads.yml``. 

  OS Migrate cannot specify that only the password in the credentials 
  dictionary should be treated as a secret, instead the whole 
  credentials dictionary is marked as a secret.

  A workaround to this is to sanitize the project name with something
  in a pre-migration playbook that sets up storage directories for 
  OS Migrate variables or data. This can prove beneficial in the 
  event of users running into censored string issues relating to 
  ansible.
