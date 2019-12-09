High-level development goals
----------------------------

* I/O-based. Fetch metadata and/or content from source cloud -> write
  them as outputs -> read them as inputs -> push it to the destination
  cloud. This allows other tools to enter the phase between the "write
  output" and "read input".

  * E.g. arbitrary/custom yaml-parsing tools can be used as a smart
    filter to analyze the exported contents from source cloud and
    choose what (not) to import into the destination cloud.

* Logging. When contributing code, don't forget about logging and how
  will information be presented to the user. Try to think about what
  can potentially fail and what kind of log output might help figuring
  out what went wrong, and on the contrary, what kind of log output
  would add clutter without much information value.

* Testing. Unit-test semantics of small parts wherever
  possible. Emphasize automated functional tests (end-to-end, talking
  to a real OpenStack backend). Functional tests are closest to the
  real use cases and provide at least basic level of comfort that the
  software does what it should.

* Always talking to OpenStack via API. The tool must be able to be
  deployed externally to both source and destination clouds. No
  looking at DBs or other hacks. If we hit a hurdle due to no-hacks
  approach, it could mean that OpenStack's capabilities for
  tenant-to-tenant content migration are lacking, and an RFE for
  OpenStack might be required.

* Idempotency where possible. When a command fails, it should be
  possible to retry with the same command.

* Whenever simplicity / understandability / clarity gets into conflict
  with convenience / ease-of-use, we prefer simplicity /
  understandability / clarity. Prefer running 20 CLI commands to do
  something where each CLI command is simple and human can enter the
  process by amending inputs/outputs e.g. with additional tools or a
  text editor, rather than one magical command which aims to satisfy
  all use cases and eventually turns out to satisfy very few, and
  tends to fail in mysterious ways with partial completion and limited
  re-runnability.

* OS-Migrate is intended to be a building block for tenant migrations
  rather than a push-button solution. The assumption is that to cover
  needs of a particular tenant migration, a knowledgeable human is
  running OS-Migrate manually and/or has tweaked it to their needs.

Misc
----

* Naming conventions - [underscores over hyphens in
  Ansible](https://github.com/ansible/galaxy/issues/1128#issuecomment-454519526).

  * Github does not support underscores in organization URLs
    though. So we have repo named os-migrate/os-migrate, and inside we
    have os_migrate Ansible collection.
