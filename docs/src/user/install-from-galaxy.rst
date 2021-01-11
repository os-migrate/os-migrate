Installation from Galaxy (recommended)
======================================

This document describes the recommended method of installing OS Migrate,
from Ansible Galaxy. Alternatively, you can `install from
source <install-from-source.md>`__.

Prerequisites
-------------

-  Ansible >= 2.9

-  Additional package requirements from Ansible modules:
   ``iputils python3-openstackclient python3-openstacksdk``

.. _installation-1:

Installation
------------

To install latest release:

.. code:: bash

   ansible-galaxy collection install os_migrate.os_migrate

To install a particular release:

.. code:: bash

   ansible-galaxy collection install os_migrate.os_migrate:<VERSION>

You can find available releases at `OS Migrate Galaxy page
<https://galaxy.ansible.com/os_migrate/os_migrate>`_.
