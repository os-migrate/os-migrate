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
migrated. The filters match against resource **names**.

The filters work **both during export and during import**, and it is
not required that the same value is used during export and
import. This feature can be used e.g. to export a subset of the
existing resources, and then during import further limit the subset of
resources being imported into batches.

The value of a filter variable is a list, where each item can be a
string (exact match) or a dictionary with ``regex`` key (regular
expression match). A resource is exported if it matches at least one
of the list items.

.. code:: yaml

   os_migrate_networks_filter:
     - my_net
     - other_net
     - regex: ^myprefix_.*

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

Conversion host name
~~~~~~~~~~~~~~~~~~~~

The conversion hosts might be configured using different names,
this is in case an operator needs to have them registered
with the subscription manager and avoid collisions with the names.

The conversion hosts names can be customized using the
following variables::

    os_migrate_src_conversion_host_name
    os_migrate_dst_conversion_host_name

By default, these variables have the same value
for both conversion hosts `os_migrate_conv_src`
and `os_migrate_conv_dst` respectively.

Conversion host external network
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The external network configuration allows the connection of the
conversion host router for external access, this external network must
be able to allocate floating IPs reachable between both conversion
hosts.

Set the name of the external (public) network to which conversion host
private subnet will be attached via its router, for source and
destination clouds respectively, via these variables::

    os_migrate_src_conversion_external_network_name
    os_migrate_dst_conversion_external_network_name

Conversion host flavor name
~~~~~~~~~~~~~~~~~~~~~~~~~~~

The conversion host flavor defines the compute, memory, and storage
capacity that will be allocated for the conversion hosts. It needs to
have at least a volume with 20GB.

The variables to be configured are::

    os_migrate_src_conversion_flavor_name
    os_migrate_dst_conversion_flavor_name

Usually, ‘m1.medium’ will suffice this requirement, but again, it can
be different between deployments.

Conversion host image name
~~~~~~~~~~~~~~~~~~~~~~~~~~

The conversion host image is the guest configure to execute the
instances migrations.

The variables to be configured are::

    os_migrate_src_conversion_image_name
    os_migrate_dst_conversion_image_name

This image must be accessible to both tenants/projects prior to
executing the conversion host deployment playbook. The variables
default to ``os_migrate_conv``, so if a conversion host image is
uploaded to Glance as public image with this name (in both src and dst
clouds), these variables do not need to be configured explicitly.

Make sure this image exists in Glance on both clouds.  Currently it
should be a
`CentOS 8 Cloud Image <https://cloud.centos.org/centos/8/x86_64/images/CentOS-8-GenericCloud-8.2.2004-20200611.2.x86_64.qcow2>`_
or
`RHEL 8 KVM Guest Image <https://access.redhat.com/downloads/content/479/ver=/rhel---8/8.3/x86_64/product-software>`_.

Conversion host RHEL variables
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

When using RHEL as conversion host, set the SSH user name as follows::

    os_migrate_conversion_host_ssh_user: cloud-user

It is also necessary to set RHEL registration variables. The
variables part of this role are set to ``omit`` by default.

The variables `os_migrate_conversion_rhsm_auto_attach`
and `os_migrate_conversion_rhsm_activationkey` are mutually
exclusive, given that, they are both defaulted to omit.

Typically the only registration variables to set are::

    os_migrate_conversion_rhsm_username
    os_migrate_conversion_rhsm_password

In this case, `os_migrate_conversion_rhsm_auto_attach` should be set to `True`
in order to fetch automatically the content once the node is registered.

or::

    os_migrate_conversion_rhsm_activationkey
    os_migrate_conversion_rhsm_org_id

For this case, `os_migrate_conversion_rhsm_auto_attach` must be left
undefined with its default value of `omit`.

The complete list of registration variables corresponds to the
`redhat_subscription <https://docs.ansible.com/ansible/latest/collections/community/general/redhat_subscription_module.html>`_
Ansible module. In OS Migrate they are named as follows::

    os_migrate_conversion_rhsm_activationkey
    os_migrate_conversion_rhsm_auto_attach
    os_migrate_conversion_rhsm_consumer_id
    os_migrate_conversion_rhsm_consumer_name
    os_migrate_conversion_rhsm_consumer_type
    os_migrate_conversion_rhsm_environment
    os_migrate_conversion_rhsm_force_register
    os_migrate_conversion_rhsm_org_id
    os_migrate_conversion_rhsm_password
    os_migrate_conversion_rhsm_pool
    os_migrate_conversion_rhsm_pool_ids
    os_migrate_conversion_rhsm_release
    os_migrate_conversion_rhsm_rhsm_baseurl
    os_migrate_conversion_rhsm_rhsm_repo_ca_cert
    os_migrate_conversion_rhsm_server_hostname
    os_migrate_conversion_rhsm_server_insecure
    os_migrate_conversion_rhsm_server_proxy_hostname
    os_migrate_conversion_rhsm_server_proxy_password
    os_migrate_conversion_rhsm_server_proxy_port
    os_migrate_conversion_rhsm_server_proxy_user
    os_migrate_conversion_rhsm_syspurpose
    os_migrate_conversion_rhsm_username

Additionally is possible to enable specific repositories in the
conversion hosts using the following variable::

    os_migrate_conversion_rhsm_repositories

The `os_migrate_conversion_rhsm_repositories` variable is a
list of those repositories that will be enabled on the conversion
host.

Enabling password-based SSH access to the conversion hosts
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

When required, a user can configure password-based SSH access to
the conversion hosts, this feature might be useful for debugging
when the private key of the hosts is not available anymore.

The variables required in order to configure the password-based
access are named as follows::

    os_migrate_conversion_host_ssh_user_enable_password_access
    os_migrate_conversion_host_ssh_user_password

The variable `os_migrate_conversion_host_ssh_user_enable_password_access`
is set by default to `false`, and the variable
`os_migrate_conversion_host_ssh_user_password` is set by default to the
following string `weak_password_disabled_by_default`.

The user enabled to access the conversion hosts with password-based authentication
is the one defined in the `os_migrate_conversion_host_ssh_user` variable.

Running custom bash scripts in the conversion hosts
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

It is possible to run custom bash scripts in the conversion
hosts before and after configuring their content.
The content of the conversion hosts is a set of required packages
and in the case of using RHEL then the configuration of the
subscription manager.

The variables allowing to run the custom scripts are::

    os_migrate_src_conversion_host_pre_content_hook
    os_migrate_src_conversion_host_post_content_hook
    os_migrate_dst_conversion_host_pre_content_hook
    os_migrate_dst_conversion_host_post_content_hook

The Ansible module used to achieve this is shell,
so users can execute a simple one-liner command, or more
complex scripts like the following examples::

    os_migrate_src_conversion_host_pre_content_hook: |
      ls -ltah
      echo "hello world"
      df -h

or::

    os_migrate_src_conversion_host_pre_content_hook: "echo 'this is a simple command'"

Disabling the subscription manager tasks
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

It is possible to disable the subscription manager
native tasks by setting to false the following variable::

    os_migrate_conversion_rhsm_manage

This will skip the tasks related to RHSM when using RHEL
in the conversion hosts. Disabling RHSM can be useful in
those cases where the operator has custom scripts they
need to use instead the standard Ansible module.

OpenStack REST API TLS variables
--------------------------------

If either of your clouds uses TLS endpoints that are not trusted by
the Migrator host by default (e.g. using self-signed certificates), or
if the Migrator host should authenticate itself via key+cert, you will
need to set TLS-related variables.

-  ``os_migrate_src_validate_certs`` / ``os_migrate_dst_validate_certs`` -
   Setting these to ``false`` disables certificate validity checks of
   the source/destination API endpoints.

-  ``os_migrate_src_ca_cert`` / ``os_migrate_dst_ca_cert`` - These
   variables allow you to specify a custom CA certificate that should
   be used to validate the source/destination API certificates.

-  ``os_migrate_src_client_cert``, ``os_migrate_src_client_key`` /
   ``os_migrate_dst_client_cert``, ``os_migrate_dst_client_key`` - If the
   Migrator host should authenticate itself using a TLS key +
   certificate when talking to source/destination APIs, set these
   variables.
