OS Migrate Design
=================

High-level development goals
----------------------------

-  I/O-based. Fetch metadata and/or content from source cloud -> write
   them as outputs -> read them as inputs -> push it to the destination
   cloud. This allows other tools to enter the phase between the "write
   output" and "read input".

   -  E.g. arbitrary/custom yaml-parsing tools can be used as a smart
      filter to analyze the exported contents from source cloud and
      choose what (not) to import into the destination cloud.

   -  Sometimes (e.g. in workload migration) only metadata may be
      written out and editable on the migrator machine, and the actual
      binary data is transferred in a direct path between the clouds
      for performance reasons.

-  Logging. When contributing code, don't forget about logging and how
   will information be presented to the user. Try to think about what
   can potentially fail and what kind of log output might help figuring
   out what went wrong, and on the contrary, what kind of log output
   would add clutter without much information value.

-  Testing. Unit-test semantics of small parts wherever possible.
   Emphasize automated functional tests (end-to-end, talking to a real
   OpenStack backend). Functional tests are closest to the real use
   cases and provide at least basic level of comfort that the software
   does what it should.

   -  Avoid excessive mocking in unit tests. Focus on writing unit
      tests for self-contained (pure) functions/methods, and structure
      the code so that as much as possible is written as pure
      functions/methods. When this is not possible, consider writing
      functional/end-to-end tests instead of unit tests.

-  Always talking to OpenStack via API. The tool must be able to be
   deployed externally to both source and destination clouds. No looking
   at DBs or other hacks. If we hit a hurdle due to no-hacks approach,
   it could mean that OpenStack's capabilities for tenant-to-tenant
   content migration are lacking, and an RFE for OpenStack might be
   required.

-  Idempotency where possible. When a command fails, it should be
   possible to retry with the same command.

-  Whenever simplicity / understandability / clarity gets into conflict
   with convenience / ease-of-use, we prefer simplicity /
   understandability / clarity.

   -  Prefer running several CLI commands to do something where each
      command is simple and human can enter the process by amending
      inputs/outputs e.g. with additional tools or a text editor,
      rather than one magical command which aims to satisfy all use
      cases and eventually turns out to satisfy very few, and tends to
      fail in mysterious ways with partial completion and limited
      re-runnability.

-  OS Migrate is intended to be a building block for tenant migrations
   rather than a push-button solution. The assumption is that to cover
   needs of a particular tenant migration, a knowledgeable human is
   running OS Migrate manually and/or has tweaked it to their needs.

Challenges of the problem domain
--------------------------------

-  Generally, admins can view resources of all projects, but cannot
   create resources in those projects (unless they have a role in the
   project). To create a resource under a project, either credentials of
   the target non-admin user have to be used for importing, or the admin
   user has to be added into the project for the duration of the import.

   -  This is not true for *some* resources. As of January 2020,
      e.g. networking resources can be created under arbitrary
      domain/project by admin using Networking API v2, but it's not the
      case for e.g. volumes, servers, keypairs. At least initially, we
      will assume the general scenario that we're running the migration
      as the tenant who owns the resources on both src/dst sides.

-  OpenStack doesn't have strict requirements on resource naming
   (doesn't require non-empty, unique names). The migration tool will
   enforce names which are non-empty, and unique per resource type. This
   is to allow idempotent imports, which is necessary for retrying
   imports on failure. The tool should allow to export/serialize
   resources that are not properly named, but the exported data should
   fail validation and be refused when fed into the import command.

   -  In the future, if we implement running all migrations as admin
      (might need OpenStack RFEs) instead of the tenant, we'd perhaps
      require uniqueness per resource type per tenant, rather than just
      per resource type.

Basic Ansible workflow design
-----------------------------

-  The challenge and a goal here is to give meaningful Ansible log
   output for debugging. This means, for example, that we shouldn't have
   a single Ansible task (one module call) to export/import the whole
   tenant, and we should also consider not having a single task to
   export/import all resources of some type. Ideally, each resource
   export/import would have its own module call (own task in Ansible
   playbook), so if the export or import fails, we can easily tell which
   resource was the one that caused a failure.

   -  We have a YAML file per resource type. Export modules are able to
      add a resource (idempotently) to an existing YAML file without
      affecting the rest. There is reusable code for this idempotence.

-  Example workflow: export networks. Provided playbook.

   -  Ansible task, provided: fetch metadata (at least name and ID, but
      perhaps the more the better for advanced filtering) of all
      networks that are visible for the tenant, register a list
      variable.

   -  Ansible task(s) optionally added by user into our playbook on
      per-environment basis: filter the metadata according to custom
      needs, re-register the list var.

      -  Eventually we may want to provide some hooks here, but
         initially we'd be fine with users simply editing the provided
         playbook.

   -  Ansible task, provided: filter networks by names, either via exact
      matches or via regexes.

   -  Anisble task, provided, calling our custom module: Iterate
      (``loop``) over the list of metadata, and call our module which
      will fetch the data and write a YAML with our defined format for
      Network resources. If necessary, do any data mangling here to
      satisfy the format requirements.

-  Example workflow: transform networks.

   -  Initially we will not provide any tooling here, but at this point
      the user should have a YAML file (or a bunch of them) with the
      serialized resources. They can use any automation (Ansible, yq,
      sed, …) to go through them and edit as they please before
      importing.

-  Example workflow: import networks. Provided playbook.

   -  Ansible task, provided: read the serialized YAML networks into
      memory, register a list variable.

   -  Anisble task, provided: Iterate (``loop``) over the list of
      networks, and call an Ansible module to create each network. We'll
      want to create our own module here to deal with our file format
      specifics, but underneath we may be calling the community
      OpenStack Ansible module if that proves helpful.

-  We may want to consider using ``tags`` on our tasks to allow some
   sub-executions. However, it may be that chunking up the code and
   using ``import_playbook`` might be more clear and safe to use than
   ``tags`` in many cases. If we do happen to add ``tags``, they
   shouldn't be added wildly, use cases should be thought through and
   documented for both users and developers. Tags need clarity and
   disciplined use in order to be helpful.

   - The above talks about tags in end-user code. We do use tags in
     our test suites, and it's much less sensitive there as we can
     change those tags any time without breaking user expectations.

Misc
----

-  Naming conventions - `underscores rather than hyphens in
   Ansible <https://github.com/ansible/galaxy/issues/1128#issuecomment-454519526>`__.

   -  Github does not support underscores in organization URLs though.
      So we have repo named os-migrate/os-migrate, and inside we have
      os_migrate Ansible collection.

-  Distribution - the preference is to distribute os-migrate via Ansible
   Galaxy.
