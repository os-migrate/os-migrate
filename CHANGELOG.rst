Changelog
=========

This project follows a simple changelog to satisfy collection metadata validation.

1.0.2
-----

- Maintenance updates for CI, linting, and sanity checks.

1.0.3
-----

- Change openstacksdk version in AEE to 4.5.0 to stop github CI from failing

1.0.4
-----

- Remove mention to OCP in the readme
- Revert make file change for submodule
- Add pylint, create bindep in root repo and remove useless dep in galaxy.yml
- Remove community.general dependency
- Cert checks
- update checksum to usedforsecurity=false

1.0.5
-----

- Add documentation for stringFilter module
- Add galaxy ignore file and fix links in the README
- Move import on top the module

1.1.0
-----

- Add KVM/hypervisor as a migration source, exporting disks with qemu-nbd
- Migrate ephemeral disks and attached Cinder volumes together in a single run
- Expose NBD multi-connection for hypervisor to OpenStack volume migration
- Allow disabling the source conversion host for NBD migrations
- Preserve volume_image_metadata on destination boot volumes
- Fetch flavor extra_specs for older cloud environments
- Add json_query filter and jmespath requirement
- Bump openstacksdk to 4.21.0 and Ansible cloud collection to 2.6.0
- Switch functional tests to gostack and add unit tests
- Fix Automation Hub certification lint and sanity checks

1.1.1
-----

- Remove upper version constraint for openstacksdk
