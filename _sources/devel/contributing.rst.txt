Become a Contributor
====================

As an open source project, OS-Migrate welcomes contributions from the
community at large. The following guide provides information on how to
add a new role to the project and where additional testing or
documentation artifacts should be added. This isn’t an exhaustive
reference and is a living document subject to change as needed when the
project formalizes any practice or pattern.

Adding a New Role
-----------------

The most common contribution to OS-Migrate is adding a new role to
support the export or import of resources. The construction of the roles
will likely follow a similar pattern. Each role also has specific unit
and functional test requirements. The most common pattern for adding a
new role will follow these steps:

-  Add a resource class to ``os_migrate/plugins/module_utils`` that
   inherits from
   ``ansible_collections.os_migrate.os_migrate.plugins.module_utils.resource.Resource``

-  Add a unit test to ``os_migrate/tests/unit`` to test serializing and
   de-serializing data, and any other functionality your class may have.

-  Create a new module in ``os_migrate/plugins/modules`` to facilitate
   the import or export of the resource.

-  Add a new playbook to ``os_migrate/playbooks``.

-  Add a new role to ``os_migrate/roles``.

-  Add functional tests to ``tests/func`` support primary use,
   idempotency, updates as a minimum. Additional tests as necessary.

-  Add documentation within classes and roles/playbooks as required.
   Update developer or user documentation as needed.

Resources
---------

Resources are the primary data that is exported from and imported to
clouds. In the ``os-migrate/os_migrate/plugins/module_utils`` directory,
there is a ``Resource`` class provided for your new resource to inherit
from. It provides a way to quickly build an organized class that uses
openstacksdk to retrieve, create and update data within a connected
OpenStack tenant.

Two very important properties are the ‘params’ and ‘info’, as these are
the primary data fields that will be exported and imported. At a
minimum, the name property of any resource should be in params_from_sdk,
and most likely addresses should be there too. The difference between
info and params is:

-  A property that would be an ‘info’ type is something that we don’t
   want or cannot “make the same” in the destination cloud. For example,
   typically UUIDs can’t be the same between two tenants so an ‘id’
   property should remain in info.

-  A property that would be in a ‘params’ type are things that we do
   want to copy to the destination cloud. These typically also get
   looked at when we’re making sure the import behavior is idempotent.
   I.e. when we re-run import playbooks, things that already got
   imported before are not attempted to be imported again.

The workload migration will probably not “fit existing molds” in some
ways so we will probably be ironing things out over time and finding new
patterns, but at the very least name should move into params
(params_from_sdk).

Roles
-----

To create an import or export role, start by adding a [role].yml file to
``os_migrate\playbooks\``. Next, add your directory to
``os_migrate\roles`` with the following layout:

-  [role]

   -  defaults

      -  main.yml

   -  meta

      -  main.yml

   -  tasks

      -  main.yml

   -  README.md

Export Roles
------------

In the ``defaults/main.yml`` file, at a minimum you will need to define
the ``export_[role]_name_filter`` variable to support filtering of
resources by the name property.

In the ``meta/main.yml`` file you will likely just need to add the
following default content:

.. code:: yaml

   ---
   galaxy_info:
     author: os-migrate
     description: os-migrate resource
     company: Red Hat
     license: Apache-2.0
     min_ansible_version: 2.9
     platforms:
       - name: Fedora
         versions:
           - 30
     galaxy_tags: ["os-migrate"]
   dependencies:
     - role: os_migrate.os_migrate.prelude_src

In the ``tasks/main.yml`` file, add your Ansible tasks for exporting the
data. A common pattern is retrieving data from an OpenStack tenant via a
`cloud
module <https://docs.ansible.com/ansible/latest/modules/list_of_cloud_modules.html#openstack>`__
, creating a collection of name/id pairs for export, filtering the names
for specific resources, and then calling the module you created for
export.

Import Roles
------------

In the ``defaults/main.yml`` file, at a minimum you will need to define
the ``import_[role]_validate_file: true`` variable to set whether or not
the import data file should be validated for this role. In most cases,
it should be set to ``true``.

.. code:: yaml

   import_[role]_validate_file: true

In the ``meta/main.yml`` file you will likely just need to add the
following default content:

.. code:: yaml

   ---
   galaxy_info:
     author: os-migrate
     description: os-migrate resource
     company: Red Hat
     license: Apache-2.0
     min_ansible_version: 2.9
     platforms:
       - name: Fedora
         versions:
           - 30
     galaxy_tags: ["os-migrate"]
   dependencies:
     - role: os_migrate.os_migrate.prelude_dst

In the ``tasks/main.yml`` file, add your Ansible tasks for importing the
data. A common pattern is validating the data file created by the
associated export role, reading the data file and then calling the
module you created for import.


Commit Messages
---------------

For every pull request we request contributors to be compliant with the
following notation to help generating automatically the project's changelog.

Format
^^^^^^

.. code-block:: console

    <feat>: <add an awesome feature>
    ^----^  ^----------------------^
    |       |
    |       +-> Summary in present tense.
    |
    +-------> Type: [Nn]ew, [cC]hg, [fF]ix.

    <body> ----> The commit's body.

Accepted types:

- `new` or `New`: newly implemented features
- `chg` or `Chg`: changes in the CI automation, documentation or any other change not presented as a new feature
- `fix` or `Fix`: a bugfix

Message Subject (First Line)
^^^^^^^^^^^^^^^^^^^^^^^^^^^^

The first line should not be longer than 70 characters, the second line is always
blank and other lines should be wrapped at 80 characters.

Ignoring the Message Subject
^^^^^^^^^^^^^^^^^^^^^^^^^^^^

If the commit message subject starts with `dev:` or `Dev:` it will be
ommited when rendering the changelog. 

Message Body
^^^^^^^^^^^^

Uses the imperative, present tense: “change” not “changed” nor “changes” and
includes motivation for the change and contrasts with previous behavior.

Documentation
-------------

If this is your first time adding a pull request to the os-migrate
repository, add your author information to ``galaxy.yml``.

Please ensure you comment your code. If you deviate from the provided
patterns already in the code base, add an explanation.

In each Ansible module in ``os_migrate\plugins\modules``, there is a
``DOCUMENTATION`` constant where you must provide standard documentation
on what the module does and an example of how you would use it in a
playbook.
