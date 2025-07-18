Upgrading
=========

This document describes the recommended method of upgrading OS Migrate
from Ansible Galaxy.

Collection upgrade
------------------

To upgrade to the latest release if you already have the OS Migrate
collection installed, make sure to pass the ``-f`` flag to the
installation command, which will force installing the (latest)
collection even if it is already present:

.. code:: bash

   ansible-galaxy collection install -f os_migrate.os_migrate

To upgrade/downgrade to a particular release:

.. code:: bash

   ansible-galaxy collection install os_migrate.os_migrate:<VERSION>

You can find available releases at `OS Migrate Galaxy page
<https://galaxy.ansible.com//os_migrate>`_.

Usage notes related to upgrading
--------------------------------

-  OS Migrate presently does not guarantee any forward compatibility of
   exported data. **The same version of OS Migrate should be used during
   export and import.**

-  After upgrading, **clear any potential existing data files** from
   your ``os_migrate_data_dir``, or use a different one.

   During export, OS Migrate will attempt to parse exsiting data files
   (with the intention of adding new resources to them), and an error
   will be raised if the existing data files were created with a
   different OS Migrate version.
