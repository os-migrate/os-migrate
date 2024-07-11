OS_MIGRATE_VERSION = '1.0.0'  # updated by build.sh

# Main serialization sections
RES_PARAMS = 'params'
RES_TYPE = 'type'
RES_INFO = '_info'
RES_MIGRATION_PARAMS = '_migration_params'

# Supported resource types
RES_TYPE_FLAVOR = 'openstack.compute.Flavor'
RES_TYPE_IMAGE = 'openstack.image.Image'
RES_TYPE_KEYPAIR = 'openstack.compute.Keypair'
RES_TYPE_NETWORK = 'openstack.network.Network'
RES_TYPE_USER_PROJECT_ROLE_ASSIGNMENT = 'openstack.identity.UserProjectRoleAssignment'
RES_TYPE_PROJECT = 'openstack.identity.Project'
RES_TYPE_ROUTER = 'openstack.network.Router'
RES_TYPE_ROUTER_INTERFACE = 'openstack.network.RouterInterface'
RES_TYPE_SECURITYGROUP = 'openstack.network.SecurityGroup'
RES_TYPE_SECURITYGROUPRULE = 'openstack.network.SecurityGroupRule'
RES_TYPE_SERVER = 'openstack.compute.Server'
RES_TYPE_SERVER_FLOATING_IP = 'openstack.network.ServerFloatingIP'
RES_TYPE_SERVER_PORT = 'openstack.network.ServerPort'
RES_TYPE_SERVER_VOLUME = 'openstack.network.ServerVolume'
RES_TYPE_SUBNET = 'openstack.subnet.Subnet'
RES_TYPE_USER = 'openstack.user.User'

# References
REF_AUTH = '%auth%'  # project/domain we're currently authenticated as
