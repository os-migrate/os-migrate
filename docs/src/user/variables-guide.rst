Variables Guide
===============

The goal of this document is to guide users to correctly configure the
most important variables in OS Migrate. For a complete listing of
variables configurable for each Ansible role, refer to the
documentation of the individual roles.

General variables
-----------------

Resource filters
~~~~~~~~~~~~~~~~

Resource filters allow the user to control which resources will be
exported (and thus which resources will be migrated). The filters
match against resource **names**.

The value of a filter variable is a list, where each item can be a
string (exact match) or a dictionary with ``regex`` key (regular
expression match). A resource is exported if it matches at least one
of the list items.

.. code:: yaml

   os_migrate_networks_filter:
     - my_net
     - other_net
     - regex: myprefix_.*

The above example says: Export only networks named ``my_net`` **or**
``other_net`` **or** starting with ``myprefix_``.

The filters default to:

.. code:: yaml

   - regex: .*

meaning "export all resources". (The set of resources exported will
still be limited to those you can see with the authentication
variables you used.)

Sometimes two roles use the same variable where this makes sense,
especially for attached resources. E.g. roles
``export_security_groups`` and ``export_security_group_rules`` both
use ``os_migrate_security_groups_filter``. Similarly,
``export_routers`` and ``export_router_interfaces`` both use
``os_migrate_routers_filter``.

List of the currently implemented filters with default values you can
copy into your variables file and customize:

.. code:: yaml

   os_migrate_flavors_filter:
     - regex: .*
   os_migrate_images_filter:
     - regex: .*
   os_migrate_keypairs_filter:
     - regex: .*
   os_migrate_networks_filter:
     - regex: .*
   os_migrate_projects_filter:
     - regex: .*
   os_migrate_routers_filter:
     - regex: .*
   os_migrate_security_groups_filter:
     - regex: .*
   os_migrate_subnets_filter:
     - regex: .*
   os_migrate_users_filter:
     - regex: .*
   os_migrate_workloads_filter:
     - regex: .*


Conversion host variables
-------------------------

The following variables are those that need to be configured prior to
running os_migrate.

Conversion host external network
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The external network configuration allows the connection of the
conversion host router for external access, this external network must
be able to allocate floating IPs reachable between both conversion
hosts.

Set the name of the external (public) network to which conversion host
private subnet will be attached via its router, for source and
destination clouds respectively, via these variables:

-  ``os_migrate_src_conversion_external_network_name``
-  ``os_migrate_dst_conversion_external_network_name``

Conversion host flavor name
~~~~~~~~~~~~~~~~~~~~~~~~~~~

The conversion host flavor defines the compute, memory, and storage
capacity that will be allocated for the conversion hosts. It needs to
have at least a volume with 20GB.

The variables to be configured are:

-  ``os_migrate_src_conversion_flavor_name``
-  ``os_migrate_dst_conversion_flavor_name``

Usually, ‘m1.medium’ will suffice this requirement, but again, it can
be different between deployments.

Conversion host image name
~~~~~~~~~~~~~~~~~~~~~~~~~~

The conversion host image is the guest configure to execute the
instances migrations.

The variables to be configured are:

-  ``os_migrate_src_conversion_image_name``
-  ``os_migrate_dst_conversion_image_name``

This image must be accessible to both tenants/projects prior to
executing the conversion host deployment playbook. The variables
default to ``os_migrate_conv``, so if a conversion host image is
uploaded to Glance as public image with this name (in both src and dst
clouds), these variables do not need to be configured explicitly.
