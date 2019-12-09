
DEFAULTS = {
    'network': {
        'is_shared': False,
        'is_admin_state_up': True,
        'is_router_external': False,
        'is_port_security_enabled': True,
        'mtu': 1450,
    },
    'subnet': {
        'ip_version': 4
    },
    'security_group_rule': {
        'description': '',
        'direction': 'ingress',
        'ethertype': 'IPv4',
    },
    'security_group': {
        'description': '',
    },
    'router': {
        'is_admin_state_up': True,
    },
    'volume': {
        'description': '',
        'name': '',
    },
    'image': {
        'disk_format': 'qcow2',
        'container_format': 'bare',
        'min_disk': 0,
        'min_ram': 0,
        'visibility': 'private',
        'is_protected': False,
    },
    'keypair': {},
    'flavor': {
        'swap': 0,
        'rxtx_factor': 1.0,
        'is_public': True,
        'ephemeral': 0,
    },
    'server': {
        'security_groups': [{'name': 'default'}],
        'config_drive': '',
        'auto_ip': True,
        'boot_from_volume': False,
        'terminate_volume': False,
        'delete_fip': False,
        'reuse_ips': True,
    },
    'user': {
        'is_enabled': True,
    },
    'domain': {
        'is_enabled': True,
    },
    'project': {
        'is_enabled': True,
    },
}

PLAYBOOK = """
---
- hosts: localhost
  connection: local
  gather_facts: no
  tasks:

    - include_vars: vars/main.yml
"""
NET_PLAYBOOK = """
    - import_tasks: networks/networks.yml
    - import_tasks: networks/subnets.yml
    - import_tasks: networks/security_groups.yml
    - import_tasks: networks/routers.yml
"""
STORAGE_PLAYBOOK = """
    - import_tasks: storage/images.yml
    - import_tasks: storage/volumes.yml
"""
COMPUTE_PLAYBOOK = """
    - import_tasks: compute/keypairs.yml
    - import_tasks: compute/flavors.yml
    - import_tasks: compute/servers.yml
"""
IDENTITY_PLAYBOOK = """
    - import_tasks: identity/users.yml
"""

FILE_NETWORKS = 'networks.yml'
FILE_SUBNETS = 'subnets.yml'
FILE_SECURITY_GROUPS = 'security_groups.yml'
FILE_ROUTERS = 'routers.yml'
FILE_IMAGES = 'images.yml'
FILE_VOLUMES = 'volumes.yml'
FILE_KEYPAIRS = 'keypairs.yml'
FILE_SERVERS = 'servers.yml'
FILE_FLAVORS = "flavors.yml"
FILE_USERS = "users.yml"
FILE_DOMAINS = "domains.yml"
FILE_PROJECTS = "projects.yml"
