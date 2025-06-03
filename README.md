# OpenStack to Openstack/Openshift migration tooling
OS Migrate is an open source toolbox for parallel cloud migration
between OpenStack/Openshift clouds.

## Description

Parallel cloud migration is a way to
modernize an OpenStack/Openshift deployment. Instead of upgrading an OpenStack
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


## Requirements

This section must list the required minimum versions of Ansible and Python, and any Python or external collection dependencies. Include additional information on other prerequisite tasks needed, if applicable.


## Installation

Before using this collection, you need to install it with the Ansible Galaxy command-line tool:

```
ansible-galaxy collection install NAMESPACE.COLLECTION_NAME
```

You can also include it in a requirements.yml file and install it with ansible-galaxy collection install -r requirements.yml, using the format:


```yaml
collections:
  - name: NAMESPACE.COLLECTION_NAME
```

Note that if you install any collections from Ansible Galaxy, they will not be upgraded automatically when you upgrade the Ansible package.
To upgrade the collection to the latest available version, run the following command:

```
ansible-galaxy collection install NAMESPACE.COLLECTION_NAME --upgrade
```

You can also install a specific version of the collection, for example, if you need to downgrade when something is broken in the latest version (please report an issue in this repository). Use the following syntax to install version 1.0.0:

```
ansible-galaxy collection install NAMESPACE.COLLECTION_NAME:==1.0.0
```

See [using Ansible collections](https://docs.ansible.com/ansible/devel/user_guide/collections_using.html) for more details.


In addition to the above boilerplate, this section should include any additional details specific to your collection, and what to expect at each step and after installation. Be sure to include any information that supports the installation process, such as information about authentication and credentialing. 

## Use Cases

This section should outline in detail 3-5 common use cases for the collection. These should be informative examples of how the collection has been used, or how you’d like to see it be used. 


## Testing

This section should include information on how the collection was tested and how it performed. Include information on what environments it’s been tested against, and any known exceptions or workarounds necessary for its use.


## Contributing
As an open source project, OS Migrate welcomes contributions from the community at large. The following guide provides information on how to add a new role to the project and where additional testing or documentation artifacts should be added. This isn’t an exhaustive reference and is a living document subject to change as needed when the project formalizes any practice or pattern. See the
[OS Migrate developer documentation](https://os-migrate.github.io/os-migrate/devel/README.html).


## Support

Please report any issues into the
[GitHub issue tracker](https://github.com/os-migrate/os-migrate/issues).


## Release Notes and Roadmap

See the [Official Changelog](https://os-migrate.github.io/os-migrate/changelog.html).


## License Information

Link to the license that the collection is published under. All links must be full URLs, not GitHub relative links.