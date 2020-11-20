Variables Guide
===============

The goal of this document is to guide users to correctly configure the
most important variables in OS Migrate. For a complete listing of
variables configurable for each Ansible role, refer to the
documentation of the individual roles.

Conversion host parameters
--------------------------

The following parameters are those that need to be configured prior to
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

The parameters to be configured are:

-  ``os_migrate_src_conversion_flavor_name``
-  ``os_migrate_dst_conversion_flavor_name``

Usually, ‘m1.medium’ will suffice this requirement, but again, it can
be different between deployments.

Conversion host image name
~~~~~~~~~~~~~~~~~~~~~~~~~~

The conversion host image is the guest configure to execute the
instances migrations.

The parameters to be configured are:

-  ``os_migrate_src_conversion_image_name``
-  ``os_migrate_dst_conversion_image_name``

This image must be accessible to both tenants/projects prior to
executing the conversion host deployment playbook. The variables
default to ``os_migrate_conv``, so if a conversion host image is
uploaded to Glance as public image with this name (in both src and dst
clouds), these variables do not need to be configured explicitly.
