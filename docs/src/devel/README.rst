OS-Migrate Developer Documentation
==================================

-  `Development environment setup <dev-env-setup.rst>`__ - Environment
   configuration to test your patches locally. Emphasizes use of
   containers to keep your workstation clean.

   -  `Using non-containerized
      Vagrant <dev-env-vagrant-non-containerized.rst>`__ - The main
      developer docs talk about using containerized Vagrant, which
      requires running a container as root. You can use
      non-containerized Vagrant if you prefer.

-  `Design doc <design.rst>`__ - Explanation of high-level design goals
   and choices.

-  `Releasing <releasing.rst>`__ - Procedure to release a new version of
   OS Migrate to Ansible Galaxy.

-  `Contributing <contributing.md>`__ - Guide for developers to
   contribute code or documentation to the project.

.. toctree::
   :maxdepth: 2

   dev-env-setup.rst
   dev-env-vagrant-non-containerized.rst
   design.rst
   releasing.rst
   contributing.rst
