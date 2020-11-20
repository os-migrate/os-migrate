OS Migrate User Documentation
=============================

OS Migrate is a tool to migrate tenant content from one OpenStack cloud
to another.

.. toctree::
   :maxdepth: 2

   install-from-galaxy.rst
   install-from-source.rst
   walkthrough.rst
   variables-guide.rst

General usage notes
-------------------

-  Run against testing/staging clouds first, verify that you are getting
   the expected results.

-  OS Migrate may not fit each use case out of the box. You can craft
   custom playbooks using the OS Migrate collection pieces (roles and
   modules) as building blocks.

-  Use the same version of OS Migrate for export and import. We
   currently do not guarantee that data files are compatible across
   versions.
