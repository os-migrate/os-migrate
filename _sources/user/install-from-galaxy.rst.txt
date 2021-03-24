Installation from Galaxy (recommended)
======================================

This document describes the recommended method of installing OS Migrate,
from Ansible Galaxy. Alternatively, you can `install from
source <install-from-source.md>`__.

Prerequisites
-------------

-  Ansible 2.9

-  Additional package requirements from Ansible modules:
   ``iputils python3-openstackclient python3-openstacksdk``

-  OpenStack SDK version should be 0.36 or newer.  (There is a `bug in
   0.53 <https://storyboard.openstack.org/#!/story/2008577>`_. For this
   reason we currently test with SDK 0.36 and 0.52.)

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

Using virtualenv
----------------

If your distribution doesn't ship the required dependency versions,
you can use virtualenv, e.g.::

   python3 -m venv $HOME/os_migrate_venv
   source $HOME/os_migrate_venv/bin/activate
   pip install --upgrade 'openstacksdk>=0.36,<0.53'
   pip install --upgrade 'ansible>=2.9.1,<2.10'
