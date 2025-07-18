Contributing Code
=================

As an open source project, OS Migrate welcomes contributions from the
community at large. The following guide provides information on how to
add a new role to the project and where additional testing or
documentation artifacts should be added. This isn't an exhaustive
reference and is a living document subject to change as needed when
the project formalizes any practice or pattern.

Adding a New Role
-----------------

The most common contribution to OS Migrate is adding a new role to
support the export or import of resources. The construction of the roles
will likely follow a similar pattern. Each role also has specific unit
and functional test requirements. The most common pattern for adding a
new role will follow these steps:

-  Add a resource class to `/plugins/module_utils` that
   inherits from
   `ansible_collections.os_migrate.os_migrate.plugins.module_utils.resource.Resource`

-  Add a unit test to `/tests/unit` to test serializing and
   de-serializing data, and any other functionality your class may have.

-  Create a new module in `/plugins/modules` to facilitate
   the import or export of the resource.

-  Add a new playbook to `/playbooks`.

-  Add a new role to `roles`.

-  Add functional tests to `tests/func` that test primary use,
   idempotency, and updates as a minimum. Additional tests as necessary.

-  Add documentation within classes and roles/playbooks as required.
   Update developer or user documentation as needed.


Creating the role skeleton automatically
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Adding roles into os-migrate can be easily achieved by
creating the role structure skeleton automatically.


From the repository root directory execute:

.. code:: bash

   ansible-playbook \
      -i 'localhost,' \
      ./scripts/role-addition.yml \
      -e ansible_connection=local \
      -e role_name=import_example_resource

This command will generate the role, the default variables file,
and the documentation stub.


Resources
~~~~~~~~~

Resources are the primary data structures that are exported from and
imported to clouds. In
`/plugins/module_utils/resource.py`, there is a
`Resource` class provided for your new resource to inherit from. It
provides a way to quickly build an organized class that uses
openstacksdk to retrieve, create and update data within a connected
OpenStack tenant. See how other classes in the `module_utils`
directory inherit from `Resource` for inspiration.

Two very important properties are the 'params' and '_info', as these are
the primary data fields that will be exported and imported. At a
minimum, the name property of any resource should be in params_from_sdk,
and most likely addresses should be there too. The difference between
info and params is:

-  A property that would be an '_info' type is something that we don't
   want or cannot "make the same" in the destination cloud. For example,
   typically UUIDs can't be the same between two tenants so an 'id'
   property should remain in info.

-  A property that would be in a 'params' type are things that we do
   want to copy to the destination cloud. These typically also get
   looked at when we're making sure the import behavior is idempotent.
   I.e. when we re-run import playbooks, things that already got
   imported before are not attempted to be imported again.

Export Roles
~~~~~~~~~~~~

In the `defaults/main.yml` file, at a minimum you will need to
define the `os_migrate_[resource]_filter` variable to support
filtering of resources by the name property.

In the `meta/main.yml` file you will likely just need to add the
following default content:

.. code:: yaml

   ---
   galaxy_info:
     author: os-migrate
     description: os-migrate resource
     company: Red Hat
     license: Apache-2.0
     min_ansible_version: "2.9"
     platforms:
       - name: Fedora
         versions:
           - "34"
     galaxy_tags: ["osmigrate"]
   dependencies:
     - role: os_migrate.os_migrate.prelude_src

In the `tasks/main.yml` file, add your Ansible tasks for exporting the
data. A common pattern is retrieving data from an OpenStack tenant via a
`cloud
module <https://docs.ansible.com/ansible/latest/collections/openstack/cloud/index.html>`__
, creating a collection of name/id pairs for export, filtering the names
for specific resources, and then calling the module you created for
export.

Import Roles
~~~~~~~~~~~~

In the `defaults/main.yml` file, at a minimum you will need to
define the same `os_migrate_[resource]_filter` variable as with
export, and `import_[resource]_validate_file: true` variable to set
whether or not the import data file should be validated for this
role. In most cases, it should be set to `true`.

In the `meta/main.yml` file you will likely just need to add the
following default content:

.. code:: yaml

   ---
   galaxy_info:
     author: os-migrate
     description: os-migrate resource
     company: Red Hat
     license: Apache-2.0
     min_ansible_version: "2.9"
     platforms:
       - name: Fedora
         versions:
           - "34"
     galaxy_tags: ["osmigrate"]
   dependencies:
     - role: os_migrate.os_migrate.prelude_dst

In the `tasks/main.yml` file, add your Ansible tasks for importing the
data. A common pattern is validating the data file created by the
associated export role, reading the data file and then calling the
module you created for import.

Writing Tests
-------------

For newly implemented resources, ensure comprehensive test coverage by following this checklist:

Functional Tests
~~~~~~~~~~~~~~~~

-  Ensure both import and export functionalities are tested, not just idempotency.
-  Include tests for admin-only resources, ensuring they are renamed before import.
-  Test resources as a tenant whenever possible to ensure broader coverage.
-  For resources with special properties like `links` or `extra_specs`, write detailed tests inspecting these properties closely.

Unit Tests
~~~~~~~~~~

-  Write unit tests for each new module created, focusing on the logic within the module.
-  Ensure that edge cases and error handling paths are covered in unit tests.

Integration Tests
~~~~~~~~~~~~~~~~~

-  Add integration tests that cover the entire process of exporting and then importing the resource, verifying the integrity and consistency of the data.
-  Verify that the resource behaves as expected in the context of the os-migrate ecosystem.

Documentation and Examples
~~~~~~~~~~~~~~~~~~~~~~~~~~

-  In the `DOCUMENTATION` constant of each module, include examples of how to use the module in a playbook.
-  Ensure that the `README.md` file for the new role is comprehensive, covering the role's purpose, usage, and any dependencies.

Test Execution in CI
~~~~~~~~~~~~~~~~~~~~

-  Confirm that all tests are executed in the Continuous Integration (CI) environment before merging.
-  If a feature is merged without proper tests due to specific circumstances, create a technical debt tracking card to follow up.

Review and Inspection
~~~~~~~~~~~~~~~~~~~~~

-  Conduct thorough reviews, especially when introducing new resources, to catch potential issues early.
-  Implement policies or checklists in development documentation to ensure test soundness and coverage.

Location of Tests
~~~~~~~~~~~~~~~~~

-  Place functional and integration tests in the `tests/e2e` or `tests/func` directory respectively, following the existing structure for similar resources.
-  Unit tests should reside alongside the modules they are testing, in the `/tests/` directory.

Special Considerations
~~~~~~~~~~~~~~~~~~~~~~

-  For resources that are only accessible by admin users, ensure tests reflect this by running them with appropriate permissions.
-  Address any known issues from previous retrospectives, such as fixing the handling of Nova keypairs or ensuring resources are tested in tenant context.

Necessary Documentation
~~~~~~~~~~~~~~~~~~~~~~~

If this is your first time adding a pull request to the os-migrate
repository, add your author information to `galaxy.yml`.

In each Ansible module in `/plugins/modules`, there is a
`DOCUMENTATION` constant where you must provide standard
documentation on what the module does and an example of how you would
use it in a playbook.

Each new role must have a `README.md` file as a requirement for
Ansible Galaxy publishing.
