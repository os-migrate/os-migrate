Installation from Galaxy (recommended)
======================================

This document describes the recommended method of installing OS Migrate,
from Ansible Galaxy. Alternatively, you can `install from
source <install-from-source.html>`__.

Prerequisites
-------------

-  Ansible 2.9 or newer.

-  Ansible must run using Python 3. (When using Ansible from RHEL
   packages, this means running on RHEL 8 or newer.)

-  Additional package requirements from Ansible modules:
   ``iputils python3-openstackclient python3-openstacksdk``

-  OpenStack SDK version should be >=0.36 and <0.99.

   - If you plan to bulk export/import keypairs as admin on behalf of
     other users (playbooks ``export_users_keypairs.yml`` and
     ``import_users_keypairs.yml``), use OpenStack SDK 0.57 or newer.

-  Ansible collection `openstack.cloud`, version <2.0.0. This will get
   handled automatically when installing from Galaxy.

Using virtualenv for prerequisites
----------------------------------

If your distribution doesn't ship the required dependency versions,
you can use virtualenv, e.g.::

   python3 -m venv $HOME/os_migrate_venv
   source $HOME/os_migrate_venv/bin/activate
   python3 -m pip install --upgrade 'openstacksdk>=0.36,<0.99'
   python3 -m pip install --upgrade 'ansible-core'


.. _installation-1:

Installation of OS Migrate collection
-------------------------------------

To install latest release:

.. code:: bash

   ansible-galaxy collection install os_migrate.os_migrate

To install a particular release:

.. code:: bash

   ansible-galaxy collection install os_migrate.os_migrate:<VERSION>

You can find available releases at `OS Migrate Galaxy page
<https://galaxy.ansible.com/os_migrate/os_migrate>`_.
