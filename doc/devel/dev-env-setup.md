OS-Migrate - Development Environment Setup
==========================================

Prerequisites
-------------

* Podman and Buildah for running rootless development environment
  containers.

Development environment
-----------------------

Build a container image with tools to be used for building and testing
the project:

    make toolbox-build

All further `make` commands etc. should be run from a container using
this image. You can start a shell within the development container
like so:

    ./toolbox/shell

Alternatively, you can run each development-related command in an
ephemeral container using the provided wrapper:

    ./toolbox/run echo "Hello from os-migrate toolbox."

Note: the `./toolbox/<cmd>` commands are alternatives to each
other. They shouldn't be nested, e.g. running `./toolbox/run` from
`./toolbox/shell` will deliberately fail.


Sanity and unit tests
---------------------

You can run sanity tests this way:

    ./toolbox/run make test-sanity

And unit tests this way:

    ./toolbox/run make test-unit

To run sanity tests and then unit tests together, a shorthand target
"test-fast" can be used:

    ./toolbox/run make test-fast


Vagrant for functional tests
----------------------------

To run functional tests, you'll need to connect to OpenStack cloud(s)
where tenant resources can be managed. As a developer, the easiest way
is to run a local virtualized all-in-one OpenStack cloud. OS-Migrate
has Vagrant+Devstack setup for this purpose.

If you have Vagrant-libvirt installed on your machine, you can use it
directly, but OS-Migrate tooling does not assume that, the customary
way is to run it via the OS-Migrate toolbox container. Special
`vagrant-shell` and `vagrant-run` wrapper scripts are provided for
this purpose. Note that this container does not run in rootless mode
since it talks to libvirt.

Launch the Vagrant-capable containerized shell:

    ./toolbox/vagrant-shell

Within that shell, run the script which brings up Vagrant+Devstack:

    # we are already in toolbox/vagrant dir when we launch vagrant-shell
    ./vagrant-up

Assuming the creation succeeded, it is now recommended to take a
snapshot of the environment so you can revert it back into a
known-good state later:

    ./vagrant-snapshot-create

**Important:** the life of the Vagrant VM is tied to the life of the
container started by `./toolbox/vagrant-shell`. That means you should
keep the `vagrant-shell` open, and run functional tests via
`./toolbox/run make test-func` from a different terminal. If you close
the `vagrant-shell`, the Vagrant VM will get killed. If that happens,
you can start it again and use `./vagrant-snapshot-revert` to revive
the VM.

If you need to revert the VM at any time, run:

    ./vagrant-snapshot-revert

When you're done developing, halt Vagrant and close `vagrant-shell`:

    ./vagrant-halt
    exit

When you want to develop again, you will be able to reuse the
snapshotted Vagrant environment:

    ./toolbox/vagrant-shell
    ./vagrant-snapshot-revert

To destroy the Vagrant VM, e.g. when you want to recreate it from
scratch later, run:

    ./vagrant-destroy


Running functional tests
------------------------

Functional tests expect `tests/func/clouds.yaml` file to exist and
contain `testsrc` and `testdst` named clouds. The tests will connect
to wherever these clouds.yaml entries point and create/delete
resources there.

Assuming you've set up Vagrant+Devstack for functional testing, go
ahead and enter a virtualenv-enabled toolbox shell:

    ./toolbox/venv-shell

Within it run a make target which will set up the aforementioned
`tests/func/clouds.yaml` file to connect to your Vagrant+Devstack
instance:

    make test-setup-vagrant-devstack

Finally, run the functional tests:

    make test-func

To run functional tests for just the resource you're working on, run
e.g.:

    FUNC_TEST_PLAYBOOK=network make test-func
