<h1 align="center">
  <br>
  <a href="http://github.com/os-migrate/os-migrate">
    <img src="https://raw.githubusercontent.com/os-migrate/os-migrate/main/media/logo.svg?sanitize=true" alt="OS Migrate" width="200">
  </a>
  <br>
  OS Migrate
  <br>
</h1>

<h4 align="center">OpenStack tenant migration tooling - an Ansible collection.</h4>

<p align="center">
  <img src="https://img.shields.io/badge/Python-v3.7+-blue.svg">
  <img src="https://img.shields.io/badge/Ansible-v2.9-blue.svg">
  <a href="https://opensource.org/licenses/Apache-2.0">
    <img src="https://img.shields.io/badge/License-Apache2.0-blue.svg">
  </a>
  <a href="https://github.com/os-migrate/os-migrate/actions?workflow=consistency-functional">
    <img src="https://github.com/os-migrate/os-migrate/workflows/consistency-functional/badge.svg?event=push">
  </a>
  <a href="https://github.com/os-migrate/os-migrate/actions?workflow=container-image-build">
    <img src="https://github.com/os-migrate/os-migrate/workflows/container-image-build/badge.svg?event=push">
  </a>
  <a href="https://github.com/os-migrate/os-migrate/actions?workflow=docs-build">
    <img src="https://github.com/os-migrate/os-migrate/workflows/docs-build/badge.svg?event=push">
  </a>
</p>

OS Migrate is an open source toolbox for parallel cloud migration
between OpenStack clouds. Parallel cloud migration is a way to
modernize an OpenStack deployment. Instead of upgrading an OpenStack
cluster in place, a second OpenStack cluster is deployed alongside,
and tenant content is migrated from the original cluster to the new
one. As hardware resources free up in the original cluster, they can
be gradually added to the new cluster.

OS Migrate provides a framework for exporting and importing resources
between two clouds. It's a collection of Ansible playbooks that
provide the basic functionality, but may not fit each use case out of
the box. You can craft custom playbooks using the OS Migrate
collection pieces (roles and modules) as building blocks.

OS Migrate strictly uses the official OpenStack API and does not
utilize direct database access or other methods to export or import
data. The Ansible playbooks contained in OS Migrate are idempotent. If
a command fails, you can retry with the same command.

## Documentation

Refer to the official [documentation website](https://os-migrate.github.io/os-migrate/)
for both
[usage](https://os-migrate.github.io/os-migrate/user/README.html) and
[developer](https://os-migrate.github.io/os-migrate/devel/README.html) documentation.
