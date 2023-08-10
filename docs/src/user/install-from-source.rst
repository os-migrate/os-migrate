Installation from source (when customizing)
===========================================

Install prerequisites as documented in `install from Galaxy
<install-from-galaxy.html>`__. Then install OS Migrate from source:

.. code:: bash

   git clone https://github.com/os-migrate/os-migrate
   cd os-migrate
   # > Here you can checkout a specific commit/branch if desired <

   make toolbox-build
   ./toolbox/run make

   pushd releases
   ansible-galaxy collection install --force os_migrate-os_migrate-latest.tar.gz
   popd
