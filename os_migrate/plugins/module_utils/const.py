OS_MIGRATE_VERSION = '0.4.0'  # updated by build.sh

# Main serialization sections
RES_PARAMS = 'params'
RES_TYPE = 'type'
RES_INFO = '_info'

# Supported resource types
RES_TYPE_NETWORK = 'openstack.network.Network'
RES_TYPE_ROUTER = 'openstack.network.Router'
RES_TYPE_ROUTER_INTERFACE = 'openstack.network.RouterInterface'
RES_TYPE_SECURITYGROUPRULE = 'openstack.network.SecurityGroupRule'
RES_TYPE_SECURITYGROUP = 'openstack.network.SecurityGroup'
RES_TYPE_SERVER = 'openstack.compute.Server'
RES_TYPE_SUBNET = 'openstack.subnet.Subnet'
RES_TYPE_KEYPAIR = 'openstack.compute.Keypair'
