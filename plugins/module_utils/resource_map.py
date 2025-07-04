from __future__ import absolute_import, division, print_function

__metaclass__ = type

from ansible_collections.os_migrate.os_migrate.plugins.module_utils import (
    flavor,
    image,
    keypair,
    network,
    project,
    router,
    router_interface,
    security_group,
    security_group_rule,
    server,
    server_floating_ip,
    server_port,
    server_volume,
    subnet,
    user,
)
from ansible_collections.os_migrate.os_migrate.plugins.module_utils import const

RESOURCE_MAP = {
    const.RES_TYPE_FLAVOR: flavor.Flavor,
    const.RES_TYPE_IMAGE: image.Image,
    const.RES_TYPE_KEYPAIR: keypair.Keypair,
    const.RES_TYPE_NETWORK: network.Network,
    const.RES_TYPE_PROJECT: project.Project,
    const.RES_TYPE_ROUTER: router.Router,
    const.RES_TYPE_ROUTER_INTERFACE: router_interface.RouterInterface,
    const.RES_TYPE_SECURITYGROUP: security_group.SecurityGroup,
    const.RES_TYPE_SECURITYGROUPRULE: security_group_rule.SecurityGroupRule,
    const.RES_TYPE_SERVER: server.Server,
    const.RES_TYPE_SERVER_FLOATING_IP: server_floating_ip.ServerFloatingIP,
    const.RES_TYPE_SERVER_PORT: server_port.ServerPort,
    const.RES_TYPE_SERVER_VOLUME: server_volume.ServerVolume,
    const.RES_TYPE_SUBNET: subnet.Subnet,
    const.RES_TYPE_USER: user.User,
}
