#!/usr/bin/python3


import os
import openstack

from plugins.os_ansible import config as conf
from plugins.os_ansible import const
from plugins.os_ansible.common import value, optimize, write_yaml


class OpenstackAnsible:
    def __init__(self, cloud_name, debug=False):
        self.debug = debug
        self.data = {}
        self.stor_path = None
        self.net_path = None
        self.comp_path = None
        self.iden_path = None
        self.cloud = cloud_name
        self.get_info()

    def run(self):
        self.initialize_directories()
        if conf.DUMP_NETWORKS:
            self.dump_networks()
        if conf.DUMP_STORAGE:
            self.dump_storage()
        if conf.DUMP_SERVERS:
            self.dump_servers()
        if conf.DUMP_IDENTITY:
            self.dump_identity()
        self.write_playbook()

    def get_info(self):
        conn = openstack.connect(cloud=self.cloud)
        # pylint: disable=maybe-no-member
        if self.debug:
            openstack.enable_logging(debug=True)
        if conf.DUMP_NETWORKS:
            self.data['networks'] = list(conn.network.networks())
            self.data['subnets'] = list(conn.network.subnets())
            self.data['secgroups'] = list(conn.network.security_groups())
            self.data['routers'] = list(conn.network.routers())
            self.data['ports'] = list(conn.network.ports())
        if conf.DUMP_STORAGE:
            self.data['images'] = list(conn.image.images())
            self.data['volumes'] = list(conn.volume.volumes())
        if conf.DUMP_SERVERS:
            self.data['servers'] = list(conn.compute.servers())
            self.data['keypairs'] = list(conn.compute.keypairs())
            self.data['flavors'] = list(conn.compute.flavors())
        if conf.DUMP_IDENTITY:
            self.data['users'] = list(conn.identity.users())
            self.data['domains'] = list(conn.identity.domains())
            self.data['projects'] = list(conn.identity.projects())

    def initialize_directories(self):
        if not os.path.exists(conf.PLAYS):
            os.makedirs(conf.PLAYS)
        if not os.path.exists(os.path.dirname(conf.VARS_PATH)):
            os.makedirs(os.path.dirname(conf.VARS_PATH))
        with open(conf.VARS_PATH, "w") as e:
            e.write("---\n")
        if conf.DUMP_NETWORKS:
            self.net_path = os.path.join(conf.PLAYS, "networks")
            if not os.path.exists(self.net_path):
                os.makedirs(self.net_path)
        if conf.DUMP_STORAGE:
            self.stor_path = os.path.join(conf.PLAYS, "storage")
            if not os.path.exists(self.stor_path):
                os.makedirs(self.stor_path)
        if conf.DUMP_SERVERS:
            self.comp_path = os.path.join(conf.PLAYS, "compute")
            if not os.path.exists(self.comp_path):
                os.makedirs(self.comp_path)
        if conf.DUMP_IDENTITY:
            self.iden_path = os.path.join(conf.PLAYS, "identity")
            if not os.path.exists(self.iden_path):
                os.makedirs(self.iden_path)

    def dump_networks(self):
        net_funcs = {
            const.FILE_NETWORKS: self.create_networks,
            const.FILE_SUBNETS: self.create_subnets,
            const.FILE_SECURITY_GROUPS: self.create_security_groups,
            const.FILE_ROUTERS: self.create_routers,
        }
        for net_file, func in net_funcs.items():
            path = os.path.join(self.net_path, net_file)
            dumped_data = func(self.data)
            write_yaml(dumped_data, path)

    def dump_storage(self):
        stor_funcs = {
            const.FILE_IMAGES: self.create_images,
            const.FILE_VOLUMES: self.create_volumes,
        }
        for stor_file, func in stor_funcs.items():
            path = os.path.join(self.stor_path, stor_file)
            dumped_data = func(self.data)
            write_yaml(dumped_data, path)

    def dump_servers(self):
        comp_funcs = {
            const.FILE_KEYPAIRS: self.create_keypairs,
            const.FILE_SERVERS: self.create_servers,
            const.FILE_FLAVORS: self.create_flavors,
        }
        for comp_file, func in comp_funcs.items():
            path = os.path.join(self.comp_path, comp_file)
            dumped_data = func(self.data)
            write_yaml(dumped_data, path)

    def dump_identity(self):
        iden_funcs = {
            const.FILE_USERS: self.create_users,
            const.FILE_DOMAINS: self.create_domains,
            const.FILE_PROJECTS: self.create_projects,
        }
        for iden_file, func in iden_funcs.items():
            path = os.path.join(self.iden_path, iden_file)
            dumped_data = func(self.data)
            write_yaml(dumped_data, path)

    def write_playbook(self):
        playbook = const.PLAYBOOK
        if conf.DUMP_NETWORKS:
            playbook += const.NET_PLAYBOOK
        if conf.DUMP_STORAGE:
            playbook += const.STORAGE_PLAYBOOK
        if conf.DUMP_SERVERS:
            playbook += const.COMPUTE_PLAYBOOK
        if conf.DUMP_IDENTITY:
            playbook += const.IDENTITY_PLAYBOOK
        with open(os.path.join(conf.PLAYS, "playbook.yml"), "w") as f:
            f.write(playbook)

    def create_projects(self, data, force_optimize=conf.VARS_OPT_PROJECTS):
        projects = []
        pre_optimized = []
        for pro in data['projects']:
            p = {'state': 'present'}
            if pro.get('location') and pro['location'].get('cloud'):
                p['cloud'] = pro['location']['cloud']
            p['name'] = pro['name']
            if value(pro, 'project', 'is_enabled'):
                p['enabled'] = pro['is_enabled']
            if value(pro, 'project', 'description'):
                p['description'] = pro['description']
            if value(pro, 'project', 'domain_id'):
                p['domain_id'] = pro['domain_id']
            if force_optimize:
                pre_optimized.append({'os_project': p})
            else:
                projects.append({'os_project': p})
        if force_optimize:
            optimized = optimize(
                pre_optimized,
                var_name="projects")
            if optimized:
                projects.append(optimized)
        return projects

    def create_domains(self, data, force_optimize=conf.VARS_OPT_DOMAINS):
        domains = []
        pre_optimized = []
        for dom in data['domains']:
            d = {'state': 'present'}
            if dom.get('location') and dom['location'].get('cloud'):
                d['cloud'] = dom['location']['cloud']
            d['name'] = dom['name']
            if value(dom, 'domain', 'is_enabled'):
                d['enabled'] = dom['is_enabled']
            if value(dom, 'domain', 'description'):
                d['description'] = dom['description']
            if force_optimize:
                pre_optimized.append({'os_keystone_domain': d})
            else:
                domains.append({'os_keystone_domain': d})
        if force_optimize:
            optimized = optimize(
                pre_optimized,
                var_name="domains")
            if optimized:
                domains.append(optimized)
        return domains

    def create_users(self, data, force_optimize=conf.VARS_OPT_USERS):
        users = []
        pre_optimized = []
        domains_by_id = {d['id']: d['name'] for d in data['domains']}
        projects_by_id = {d['id']: d['name'] for d in data['projects']}
        for user in data['users']:
            u = {'state': 'present'}
            if user.get('location') and user['location'].get('cloud'):
                u['cloud'] = user['location']['cloud']
            u['name'] = user['name']
            if value(user, 'user', 'is_enabled'):
                u['enabled'] = user['is_enabled']
            if value(user, 'user', 'description'):
                u['description'] = user['description']
            if value(user, 'user', 'domain_id'):
                u['domain'] = domains_by_id[user['domain_id']]
            if value(user, 'user', 'default_project_id'):
                u['default_project'] = projects_by_id[user['default_project_id']]
            if value(user, 'user', 'email'):
                u['email'] = user['email']
            if value(user, 'user', 'password'):  # shouldn't be there
                u['password'] = user['password']
            if force_optimize:
                pre_optimized.append({'os_user': u})
            else:
                users.append({'os_user': u})
        if force_optimize:
            optimized = optimize(
                pre_optimized,
                var_name="users")
            if optimized:
                users.append(optimized)
        return users

    def create_flavors(self, data, force_optimize=conf.VARS_OPT_FLAVORS):
        flavors = []
        pre_optimized = []
        for flavor in data['flavors']:
            fl = {'state': 'present'}
            if flavor.get('location') and flavor['location'].get('cloud'):
                fl['cloud'] = flavor['location']['cloud']
            fl['name'] = flavor['name']
            if value(flavor, 'flavor', 'disk'):
                fl['disk'] = flavor['disk']
            if value(flavor, 'flavor', 'ram'):
                fl['ram'] = flavor['ram']
            if value(flavor, 'flavor', 'vcpus'):
                fl['vcpus'] = flavor['vcpus']
            if value(flavor, 'flavor', 'swap'):
                fl['swap'] = flavor['swap']
            if value(flavor, 'flavor', 'rxtx_factor'):
                fl['rxtx_factor'] = flavor['rxtx_factor']
            if value(flavor, 'flavor', 'is_public'):
                fl['is_public'] = flavor['is_public']
            if value(flavor, 'flavor', 'ephemeral'):
                fl['ephemeral'] = flavor['ephemeral']
            if value(flavor, 'flavor', 'extra_specs'):
                fl['extra_specs'] = flavor['extra_specs']
            if force_optimize:
                pre_optimized.append({'os_nova_flavor': fl})
            else:
                flavors.append({'os_nova_flavor': fl})
        if force_optimize:
            optimized = optimize(
                pre_optimized,
                var_name="flavors")
            if optimized:
                flavors.append(optimized)
        return flavors

    def create_subnets(self, data, force_optimize=conf.VARS_OPT_SUBNETS):
        subnets = []
        pre_optimized = []
        net_ids = {i['id']: i['name'] for i in data['networks']}
        for subnet in data['subnets']:
            s = {'state': 'present'}
            if subnet.get('location') and subnet['location'].get('cloud'):
                s['cloud'] = subnet['location']['cloud']
            s['name'] = subnet['name']
            if subnet['network_id'] in net_ids:
                s['network_name'] = net_ids[subnet['network_id']]
            else:
                print("subnet %s id=%s doesn't find its network id=%s" %
                      (subnet['name'], subnet['id'], subnet['network_id']))
                continue
            s['cidr'] = subnet['cidr']
            if value(subnet, 'subnet', 'ip_version'):
                s['ip_version'] = subnet['ip_version']
            if value(subnet, 'subnet', 'enable_dhcp'):
                s['enable_dhcp'] = subnet['is_dhcp_enabled']
            if value(subnet, 'subnet', 'gateway_ip'):
                s['gateway_ip'] = subnet['gateway_ip']
            if value(subnet, 'subnet', 'dns_nameservers'):
                s['dns_nameservers'] = subnet['dns_nameservers']
            if value(subnet, 'subnet', 'ipv6_address_mode'):
                s['ipv6_address_mode'] = subnet['ipv6_address_mode']
            if value(subnet, 'subnet', 'ipv6_ra_mode'):
                s['ipv6_ra_mode'] = subnet['ipv6_ra_mode']
            if value(subnet, 'subnet', 'host_routes'):
                s['host_routes'] = subnet['host_routes']
            if force_optimize:
                pre_optimized.append({'os_subnet': s})
            else:
                subnets.append({'os_subnet': s})
        if force_optimize:
            optimized = optimize(
                pre_optimized,
                var_name="subnets")
            if optimized:
                subnets.append(optimized)
        return subnets

    def create_networks(self, data, force_optimize=conf.VARS_OPT_NETWORKS):
        networks = []
        pre_optimized = []
        for network in data['networks']:
            n = {'state': 'present'}
            if network.get('location') and network['location'].get('cloud'):
                n['cloud'] = network['location']['cloud']
            n['name'] = network['name']
            if value(network, 'network', 'is_admin_state_up'):
                n['admin_state_up'] = network['is_admin_state_up']
            if value(network, 'network', 'is_router_external'):
                n['external'] = network['is_router_external']
            if value(network, 'network', 'is_port_security_enabled'):
                n['port_security_enabled'] = network['is_port_security_enabled']
            if value(network, 'network', 'is_shared'):
                n['shared'] = network['is_shared']
            if value(network, 'network', 'provider_network_type'):
                n['provider_network_type'] = network['provider_network_type']
            if value(network, 'network', 'provider_physical_network'):
                n['provider_physical_network'] = network[
                    'provider_physical_network']
            if value(network, 'network', 'provider_segmentation_id'):
                n['provider_segmentation_id'] = network[
                    'provider_segmentation_id']
            # if value(network, 'network', 'mtu'):
            #    n['mtu'] = network['mtu']
            if value(network, 'network', 'dns_domain'):
                n['dns_domain'] = network['dns_domain']
            if force_optimize:
                pre_optimized.append({'os_network': n})
            else:
                networks.append({'os_network': n})
        if force_optimize:
            optimized = optimize(
                pre_optimized,
                var_name="networks")
            if optimized:
                networks.append(optimized)
        return networks

    def create_security_groups(self, data,
                               force_optimize=conf.VARS_OPT_SECGROUPS):
        secgrs = []
        secgrs_ids = {i['id']: i['name'] for i in data['secgroups']}
        for secgr in data['secgroups']:
            s = {'state': 'present'}
            if secgr.get('location') and secgr['location'].get('cloud'):
                s['cloud'] = secgr['location']['cloud']
            s['name'] = secgr['name']
            secgrs.append({'os_security_group': s})
            if value(secgr, 'security_group', 'description'):
                s['description'] = secgr['description']
            if secgr.get('security_group_rules'):
                pre_optimized = []
                for rule in secgr['security_group_rules']:
                    r = {'security_group': secgr['name']}
                    if s.get('cloud'):
                        r['cloud'] = s['cloud']
                    if value(rule, 'security_group_rule', 'description'):
                        r['description'] = rule['description']
                    if value(rule, 'security_group_rule', 'ethertype'):
                        r['ethertype'] = rule['ethertype']
                    if value(rule, 'security_group_rule', 'direction'):
                        r['direction'] = rule['direction']
                    if value(rule, 'security_group_rule', 'port_range_max'):
                        r['port_range_max'] = rule['port_range_max']
                    if value(rule, 'security_group_rule', 'port_range_min'):
                        r['port_range_min'] = rule['port_range_min']
                    if value(rule, 'security_group_rule', 'protocol'):
                        r['protocol'] = rule['protocol']
                    if value(rule, 'security_group_rule', 'remote_group_id'):
                        r['remote_group'] = secgrs_ids[rule['remote_group_id']]
                    if value(rule, 'security_group_rule', 'remote_ip_prefix'):
                        r['remote_ip_prefix'] = rule['remote_ip_prefix']
                    if force_optimize:
                        pre_optimized.append({'os_security_group_rule': r})
                    else:
                        secgrs.append({'os_security_group_rule': r})
                if force_optimize:
                    optimized = optimize(
                        pre_optimized,
                        var_name=secgr['name'].replace('-', '_') + "_rules")
                    if optimized:
                        secgrs.append(optimized)
        return secgrs

    def create_routers(self, data, strict_ip=False,
                       force_optimize=conf.VARS_OPT_ROUTERS):
        routers = []
        pre_optimized = []
        subnet_ids = {i['id']: i for i in data['subnets']}
        net_ids = {i['id']: i for i in data['networks']}
        for rout in data['routers']:
            r = {'state': 'present'}
            if rout.get('location') and rout['location'].get('cloud'):
                r['cloud'] = rout['location']['cloud']
            r['name'] = rout['name']
            if value(rout, 'router', 'is_admin_state_up'):
                r['admin_state_up'] = rout['is_admin_state_up']
            r['interfaces'] = []
            ports = [i for i in data['ports'] if i['device_id'] == rout['id']]
            for p in ports:
                for fip in p['fixed_ips']:
                    subnet = subnet_ids.get(fip['subnet_id'])
                    if not subnet:
                        raise Exception("No subnet with ID=%s" %
                                        fip['subnet_id'])
                    if subnet['gateway_ip'] == fip['ip_address']:
                        r['interfaces'].append(subnet['name'])
                    else:
                        net = net_ids.get(p['network_id'])
                        if not net:
                            raise Exception("No network with ID=%s" %
                                            p['network_id'])
                        net_name = net['name']
                        subnet_name = subnet['name']
                        portip = fip['ip_address']
                        r['interfaces'].append({
                            'net': net_name,
                            'subnet': subnet_name,
                            'portip': portip,
                        })
            if not r['interfaces']:
                del r['interfaces']
            if rout['external_gateway_info']:
                ext_net = net_ids.get(
                    rout['external_gateway_info']['network_id'])
                if not ext_net:
                    raise Exception("No net with ID=%s" % rout[
                                    'external_gateway_info']['network_id'])
                ext_net_name = ext_net['name']
                r['network'] = ext_net_name
                if len(rout['external_gateway_info']['external_fixed_ips']
                       ) == 1:
                    ext = rout['external_gateway_info']['external_fixed_ips'][0]
                    if strict_ip:
                        ext_sub_id = ext['subnet_id']
                        ext_subnet = subnet_ids.get(ext_sub_id)
                        if not ext_subnet:
                            # raise Exception("No subnet with ID" )
                            ext_sub_name = ext_sub_id
                        else:
                            ext_sub_name = ext_subnet['name']
                        ext_fip = ext['ip_address']
                        r['external_fixed_ips'] = [{
                            'subnet': ext_sub_name,
                            'ip': ext_fip
                        }]
                if len(rout['external_gateway_info']['external_fixed_ips']) > 1:
                    ext_ips = rout['external_gateway_info']['external_fixed_ips']
                    for ext in ext_ips:
                        ext_sub_id = ext['subnet_id']
                        ext_subnet = subnet_ids.get(ext_sub_id)
                        if not ext_subnet:
                            # raise Exception("No subnet with ID=%s" % ext_sub_id)
                            ext_sub_name = ext_sub_id
                        else:
                            ext_sub_name = ext_subnet['name']
                        ext_fip = ext['ip_address']
                        r['external_fixed_ips'] = [{
                            'subnet': ext_sub_name,
                            'ip': ext_fip
                        }]
            if force_optimize:
                pre_optimized.append({'os_router': r})
            else:
                routers.append({'os_router': r})
        if force_optimize:
            optimized = optimize(
                pre_optimized,
                var_name="routers")
            if optimized:
                routers.append(optimized)
        return routers

    def create_servers(self, data, force_optimize=conf.VARS_OPT_SERVERS):

        def get_boot_volume(volumes):
            # Let's assume it's only one bootable volume
            for v in volumes:
                vol = volumes_dict[v['id']]
                if not vol['is_bootable']:
                    continue
                return vol

        def has_floating(addresses):
            return 'floating' in [
                j['OS-EXT-IPS:type'] for i in list(addresses.values()) for j in i]

        servers = []
        pre_optimized = []
        if conf.DUMP_STORAGE:
            volumes_dict = {i['id']: i for i in data['volumes']}
            images_dict = {i['id']: i['name'] for i in data['images']}
        else:
            volumes_dict = {}
            images_dict = {}
        flavors_names = {i['id']: i['name'] for i in data['flavors']}
        for ser in data['servers']:
            s = {'state': 'present'}
            s['name'] = ser['name']
            if ser.get('location') and ser['location'].get('cloud'):
                s['cloud'] = ser['location']['cloud']
            if value(ser, 'server', 'security_groups'):
                s['security_groups'] = list(set(
                    [i['name'] for i in ser['security_groups']]))
            s['flavor'] = flavors_names[ser['flavor']['id']]
            if value(ser, 'server', 'key_name'):
                s['key_name'] = ser['key_name']
            if value(ser, 'server', 'scheduler_hints'):
                s['scheduler_hints'] = ser['scheduler_hints']
            if value(ser, 'server', 'metadata'):
                s['meta'] = ser['metadata']
            if value(ser, 'server', 'config_drive'):
                s['config_drive'] = ser['config_drive'] == 'True'
            if value(ser, 'server', 'user_data'):
                s['userdata'] = ser['user_data']
            # Images and volumes
            if ser['image']['id']:
                if ser['image']['id'] in images_dict:
                    s['image'] = (
                        ser['image']['id']
                        if not conf.IMAGES_AS_NAMES
                        else images_dict[ser['image']['id']])
                else:
                    print("Image with ID=%s of server %s is not in images list" %
                          (ser['image']['id'], ser['name']))
                    continue
            else:
                # Dancing with boot volumes
                if conf.USE_EXISTING_BOOT_VOLUMES:
                    s['boot_volume'] = get_boot_volume(
                        ser['attached_volumes'])['id']
                    # s['volumes'] = [i['id'] for i in ser['attached_volumes']]
                elif conf.USE_SERVER_IMAGES:
                    meta = get_boot_volume(ser['attached_volumes'])[
                        'volume_image_metadata']
                    s['image'] = (meta['image_name']
                                  if conf.IMAGES_AS_NAMES else meta['image_id'])
                    if conf.CREATE_NEW_BOOT_VOLUMES:
                        s['boot_from_volume'] = True
                        s['volume_size'] = get_boot_volume(
                            ser['attached_volumes'])['size']
            if ser.get('attached_volumes'):
                non_bootable_volumes = [i['id'] for i in ser['attached_volumes']
                                        if not volumes_dict[i['id']]['is_bootable']]
                if non_bootable_volumes:
                    s['volumes'] = non_bootable_volumes
            if ser.get('addresses'):
                if conf.NETWORK_AUTO:
                    # In case of DHCP just connect to networks
                    nics = [{"net-name": i}
                            for i in list(ser['addresses'].keys())]
                    s['nics'] = nics
                elif conf.STRICT_NETWORK_IPS:
                    s['nics'] = []
                    for net in list(ser['addresses'].keys()):
                        for ip in ser['addresses'][net]:
                            if ip['OS-EXT-IPS:type'] == 'fixed':
                                s['nics'].append(
                                    {'net-name': net, 'fixed_ip': ip['addr']})
                if conf.FIP_AUTO:
                    # If there are existing floating IPs only
                    s['auto_ip'] = has_floating(ser['addresses'])
                elif conf.STRICT_FIPS:
                    fips = [j['addr'] for i in list(ser['addresses'].values())
                            for j in i if j['OS-EXT-IPS:type'] == 'floating']
                    s['floating_ips'] = fips
            if force_optimize:
                pre_optimized.append({'os_server': s})
            else:
                servers.append({'os_server': s})
        if force_optimize:
            optimized = optimize(
                pre_optimized,
                var_name="servers")
            if optimized:
                servers.append(optimized)
        return servers

    def create_keypairs(self, data, force_optimize=conf.VARS_OPT_KEYPAIRS):
        keypairs = []
        pre_optimized = []
        for key in data['keypairs']:
            k = {'state': 'present'}
            k['name'] = key['name']
            if key.get('location') and key['location'].get('cloud'):
                k['cloud'] = key['location']['cloud']
            if value(key, 'keypair', 'public_key'):
                k['public_key'] = key['public_key']
            if force_optimize:
                pre_optimized.append({'os_keypair': k})
            else:
                keypairs.append({'os_keypair': k})
        if force_optimize:
            optimized = optimize(
                pre_optimized,
                var_name="keypairs")
            if optimized:
                keypairs.append(optimized)
        return keypairs

    def create_images(self, data, set_id=False,
                      force_optimize=conf.VARS_OPT_IMAGES):
        imgs = []
        pre_optimized = []
        for img in data['images']:
            im = {'state': 'present'}
            im['name'] = img['name']
            if set_id:
                im['id'] = img['id']
            if img.get('location') and img['location'].get('cloud'):
                im['cloud'] = img['location']['cloud']
            if value(img, 'image', 'checksum'):
                im['checksum'] = img['checksum']
            if value(img, 'image', 'container_format'):
                im['container_format'] = img['container_format']
            if value(img, 'image', 'disk_format'):
                im['disk_format'] = img['disk_format']
            if value(img, 'image', 'owner_id'):
                im['owner'] = img['owner_id']
            if value(img, 'image', 'min_disk'):
                im['min_disk'] = img['min_disk']
            if value(img, 'image', 'min_ram'):
                im['min_ram'] = img['min_ram']
            if value(img, 'image', 'visibility'):
                im['is_public'] = (img['visibility'] == 'public')
            # Supported in ansible > 2.8
            # if value(img, 'image', 'is_protected'):
            #     im['protected'] = img['is_protected']
            if value(img, 'image', 'file'):
                im['filename'] = img['file']
            if value(img, 'image', 'ramdisk_id'):
                im['ramdisk'] = img['ramdisk_id']
            if value(img, 'image', 'kernel_id'):
                im['kernel'] = img['kernel_id']
            if value(img, 'image', 'volume'):
                im['volume'] = img['volume']
            if value(img, 'image', 'properties'):
                im['properties'] = img['properties']
            if force_optimize:
                pre_optimized.append({'os_image': im})
            else:
                imgs.append({'os_image': im})
        if force_optimize:
            optimized = optimize(
                pre_optimized,
                var_name="images")
            if optimized:
                imgs.append(optimized)
        return imgs

    def create_volumes(self, data, force_optimize=conf.VARS_OPT_VOLUMES):
        vols = []
        pre_optimized = []
        for vol in data['volumes']:
            v = {'state': 'present'}
            if not vol['name'] and conf.SKIP_UNNAMED_VOLUMES:
                continue
            if not vol['name']:
                v['display_name'] = vol['id']
            v['display_name'] = vol['name']
            if vol.get('location') and vol['location'].get('cloud'):
                v['cloud'] = vol['location']['cloud']
            if value(vol, 'volume', 'display_description'):
                v['display_description'] = vol['description']
            if value(vol, 'volume', 'size'):
                v['size'] = vol['size']
            if ('volume_image_metadata' in vol and 'image_name'
                    in vol['volume_image_metadata']):
                v['image'] = vol['volume_image_metadata']['image_name']
            if value(vol, 'volume', 'metadata'):
                v['metadata'] = vol['metadata']
            if value(vol, 'volume', 'scheduler_hints'):
                v['scheduler_hints'] = vol['scheduler_hints']
            if value(vol, 'volume', 'snapshot_id'):
                v['snapshot_id'] = vol['snapshot_id']
            if value(vol, 'volume', 'source_volume_id'):
                v['volume'] = vol['source_volume_id']
            if force_optimize:
                pre_optimized.append({'os_volume': v})
            else:
                vols.append({'os_volume': v})
        if force_optimize:
            optimized = optimize(
                pre_optimized,
                var_name="volumes")
            if optimized:
                vols.append(optimized)
        return vols


def main():
    playbook = OpenstackAnsible("test-cloud")
    playbook.run()


if __name__ == "__main__":
    main()
