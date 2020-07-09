# Configuring variables in os-migrate

The goal of this document is to guide users to correctly
configure the variables requires to migrate resources from
one tenant/project to another.
Depending on the environment, parameters like the flavor that
will be used to deploy the conversion host must be configured
prior to a migration, these parameters can vary as they depend
on how each tenant was configured.
All these parameters are centered over the conversion host
configuration.

## Conversion host parameters

The following parameters are those that need to be configured
prior to running os_migrate.

### Conversion host external network

The external network configuration allows the connection of the
conversion host router for external access, this external network
must be able to allocate floating IPs reachable between both
conversion hosts.

The parameters to be configured are:

* os_migrate_src_conversion_external_network_name
* os_migrate_dst_conversion_external_network_name

Usually, these parameters can be configured to 'public' or
'external_network' but it depends on how they were configured
by the administrators of the system.

### Conversion host flavor name

The conversion host flavor defines the compute, memory, and
storage capacity that will be allocated in this guest. It needs
to have at least a volume with 20GB.

The parameters to be configured are:

* os_migrate_src_conversion_flavor_name
* os_migrate_dst_conversion_flavor_name

Usually, 'm1.medium' will suffice this requirement, but again,
it can be different between deployments.

### Conversion host image name

The conversion host image is the guest configure to execute the
instances migrations.

The parameters to be configured are:

* os_migrate_src_conversion_image_name
* os_migrate_dst_conversion_image_name

This image must be pre-uploaded to both tenants/projects prior to
executing the os-migrate playbooks.
