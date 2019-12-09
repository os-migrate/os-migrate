import os


def str2bool(x):
    if isinstance(x, bool):
        return x
    if x in ['True', 'true', 1, 'T', 't', '1']:
        return True
    if x in ['False', 'false', 0, 'F', 'f', '0']:
        return False
    raise Exception("Please pass False or True instead of %s" % x)


PREFIX = "TRANSIBLE_"

# Plugin config
DUMP_NETWORKS = str2bool(os.environ.get(PREFIX + "DUMP_NETWORKS", True))
DUMP_STORAGE = str2bool(os.environ.get(PREFIX + "DUMP_STORAGE", True))
DUMP_SERVERS = str2bool(os.environ.get(PREFIX + "DUMP_SERVERS", True))
DUMP_IDENTITY = str2bool(os.environ.get(PREFIX + "DUMP_IDENTITY", False))

# # Paths config
# Path to playbook
PLAYS = os.environ.get(
    PREFIX + "PLAYS", os.path.join(os.path.curdir, "transible"))
# Path to variables file
VARS_PATH = os.environ.get(
    PREFIX + "VARS_PATH", os.path.join(PLAYS, "vars", "main.yml"))

# # Storage config
# Volumes can be created without names, but current os_volume ansible module
# doesn't allow create unnamed volumes. In case you need them anyway, configure
# this variable to True, in this case volumes ID will be used instead of names.
SKIP_UNNAMED_VOLUMES = str2bool(os.environ.get(
    PREFIX + "SKIP_UNNAMED_VOLUMES", True))
# It's possible to configure images in playbooks both as names and IDs, the
# default is names because it's more readable.
IMAGES_AS_NAMES = str2bool(os.environ.get(PREFIX + "IMAGES_AS_NAMES", True))
# Server can be booted both from volume and image, in case you don't need to
# boot it from volume and don't need to create a volume, just set this
# parameter to True. In case you want your volume to be kept in configuraion,
# set it to False
USE_SERVER_IMAGES = str2bool(os.environ.get(PREFIX + "USE_SERVER_IMAGES", True))
# Use this parameter when you want to create new servers from boot volumes
CREATE_NEW_BOOT_VOLUMES = str2bool(os.environ.get(
    PREFIX + "CREATE_NEW_BOOT_VOLUMES", False))
# When managing cloud you usually don't want to recreate volumes and servers,
# then you set this parameter to True. In case you need to redeploy the current
# configuration on a new cloud and you need to boot from volumes, set this
# parameter to False and new boot volumes will be created.
USE_EXISTING_BOOT_VOLUMES = str2bool(os.environ.get(
    PREFIX + "USE_EXISTING_BOOT_VOLUMES", False))

# # Network config
# Set this parameter to True when you want servers to get their IP from DHCP
# in the network and not to set them to fixed IPs that they have now.
NETWORK_AUTO = str2bool(os.environ.get(PREFIX + "NETWORK_AUTO", False))
# When setting this parameter to True, you'll assign to servers exact the same
# IP addresses that they have now, and not to get them from DHCP server on net.
STRICT_NETWORK_IPS = not NETWORK_AUTO
# Set it to True if you want to allocate and assign floating IP to server
# automatically. Set it to False if you don't need a floating IP on server.
FIP_AUTO = str2bool(os.environ.get(PREFIX + "FIP_AUTO", True))
# When using previous config with Auto floating IP it will be alocated from
# available floating IP pool randomly. Use this parameter if you need to set
# floating IP of server to exactly the same it has now. Be aware that if the
# given IP is not available the playbook will fail.
STRICT_FIPS = not FIP_AUTO

# # Variables optimization configuration
# Set to True any of current variables to have all date for a specific resource
# in vars/ and not in playbook.
VARS_OPT_NETWORKS = False
VARS_OPT_SUBNETS = True
VARS_OPT_ROUTERS = False
VARS_OPT_SECGROUPS = True
VARS_OPT_IMAGES = True
VARS_OPT_VOLUMES = False
VARS_OPT_KEYPAIRS = True
VARS_OPT_SERVERS = False
VARS_OPT_FLAVORS = False
VARS_OPT_USERS = False
VARS_OPT_DOMAINS = False
VARS_OPT_PROJECTS = False
