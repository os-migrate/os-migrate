Development Environment Setup
=============================

Prerequisites
-------------

-  Local clone of the os-migrate git repo from https://github.com/os-migrate/os-migrate
-  `Podman <https://podman.io/>`_ and `Buildah <https://buildah.io/>`_ for running rootless development environment
   containers.

Development environment
-----------------------

Build a container image with tools to be used for building and testing
the project:

::

   make toolbox-build

All further ``make`` commands etc. should be run from a container
using this image. You can start a bash shell within the development
container like so:

::

   ./toolbox/run

Alternatively, you can run each development-related command in an
ephemeral container using the provided wrapper, if you provide the
command as parameter(s) to the `./toolbox/run` script:

::

   ./toolbox/run echo "Hello from os-migrate toolbox."

Sanity and unit tests
---------------------

You can run sanity tests this way:

::

   ./toolbox/run make test-sanity

And unit tests this way:

::

   ./toolbox/run make test-unit

To run sanity tests and then unit tests together, a shorthand target
“test-fast” can be used:

::

   ./toolbox/run make test-fast

Vagrant for functional tests
----------------------------

To run functional tests, you’ll need to connect to OpenStack cloud(s)
where tenant resources can be managed. As a developer, the easiest way
is to run a local virtualized all-in-one OpenStack cloud. OS Migrate has
Vagrant+Devstack setup for this purpose.

If you have Vagrant-libvirt installed on your machine, you can use it
directly, but OS Migrate tooling does not assume that, the customary
way is to run it via the OS Migrate toolbox container. Special
``vagrant-run`` wrapper scripts are provided for this purpose.

Note that the Vagrant container cannot run in rootless mode since it
controls libvirt. When the wrapper script is first run, it will copy
the rootless `os-migrate-toolbox` image into the system's (`root`
user's) container images automatically.

Launch the Vagrant-capable containerized shell:

::

   ./toolbox/vagrant-run

Within that shell, run the script which brings up Vagrant+Devstack:

::

   # we are already in toolbox/vagrant dir when we launch vagrant-run
   ./vagrant-up

Assuming the creation succeeded, it is now recommended to take a
snapshot of the environment so you can revert it back into a known-good
state later:

::

   ./vagrant-snapshot-create

**Important:** the life of the Vagrant VM is tied to the life of the
container started by ``./toolbox/vagrant-run``. That means you should
keep the shell open, and run functional tests via ``./toolbox/run make
test-func`` from a different terminal. If you close the
``vagrant-run``, the Vagrant VM will get killed. If that happens, you
can start it again and use ``./vagrant-snapshot-revert`` to revive
the VM.

If you need to revert the VM at any time, run:

::

   ./vagrant-snapshot-revert

When you’re done developing, halt Vagrant and close ``vagrant-run``
shell:

::

   ./vagrant-halt
   exit

When you want to develop again, you will be able to reuse the
snapshotted Vagrant environment:

::

   ./toolbox/vagrant-run
   ./vagrant-snapshot-revert

To destroy the Vagrant VM, e.g. when you want to recreate it from
scratch later, run:

::

   ./vagrant-destroy

Running functional tests
------------------------

Functional tests expect ``tests/func/auth.yml`` file to exist and
contain ``os_migrate_src_auth`` and ``os_migrate_dst_auth`` variables
with credentials for connecting to OpenStack cloud(s). The tests will
connect to wherever these auth parameters point and create/delete
resources there.

Run a make target which will set up the aforementioned
``tests/func/auth.yml`` file to connect to your Vagrant+Devstack
instance:

::

   ./toolbox/run make test-setup-vagrant-devstack

Finally, run the functional tests:

::

   ./toolbox/run make test-func

To run functional tests for just the resource you’re working on, run
e.g.:

::

   OS_MIGRATE_FUNC_TEST_ARGS='--tags test_network,test_subnet' ./toolbox/run make test-func

To explore imported resoruces, skip the after-test cleanup of resources,
e.g.:

::

   OS_MIGRATE_FUNC_TEST_ARGS='--tags test_network,test_subnet --skip-tags test_clean_after' ./toolbox/run make test-func
