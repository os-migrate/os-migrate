Test NBDkit Hypervisor Role
============================

⚠️ **WARNING: THIS IS A TEST ROLE ONLY** ⚠️

This role is designed for **testing and development purposes only**. It should **NOT** be used in production environments.

## Purpose

This role spawns nbdkit on an OpenStack compute node (hypervisor) to expose VM disk images for testing nbdkit direct mode migration. It:

1. Verifies the source instance is shut down
2. Locates the instance disk on the hypervisor
3. Inspects the disk format (qcow2 vs raw)
4. Determines the correct nbdkit plugin and source file
5. Starts nbdkit with the appropriate configuration
6. Updates the export file with the nbdkit URI

## Requirements

- Direct SSH access to the OpenStack hypervisor (compute node)
- `nbdkit` and `nbdkit-plugin-*` packages installed on hypervisor
- `qemu-img` installed on hypervisor
- Source instance must be in SHUTOFF state
- Firewall rules allowing access to nbdkit port from destination conversion host

## Role Variables

### Required Variables

These must be passed when calling the role:

```yaml
workload_data: <workload_dict>    # Workload data from export
hypervisor_host: <hostname_or_ip> # Hypervisor hostname or IP
test_nbdkit_export_file: <path>   # Path to export file to update
```

### Optional Variables (see defaults/main.yml)

```yaml
# NBDkit port
test_nbdkit_port: 10809

# Protocol: 'tcp' or 'ssh'
test_nbdkit_protocol: tcp

# IP restriction (optional)
test_nbdkit_ip_allow: 192.168.1.100

# SSH configuration
test_nbdkit_hypervisor_ssh_user: root
test_nbdkit_hypervisor_ssh_key: "{{ ansible_env.HOME }}/.ssh/id_rsa"

# Directories
test_nbdkit_nova_instances_dir: /var/lib/nova/instances
test_nbdkit_nova_base_dir: /var/lib/nova/instances/_base

# NBDkit options
test_nbdkit_foreground: false
test_nbdkit_readonly: true
test_nbdkit_timeout: 300
```

## Usage

### Example Playbook

```yaml
---
- name: Setup nbdkit for testing
  hosts: localhost
  tasks:
    - name: Read workload file
      ansible.builtin.slurp:
        src: /path/to/workload.yml
      register: workload_file

    - name: Parse workload
      ansible.builtin.set_fact:
        workload: "{{ workload_file.content | b64decode | from_yaml }}"

    - name: Setup nbdkit on hypervisor
      ansible.builtin.include_role:
        name: os_migrate.os_migrate.test_nbdkit_hypervisor
      vars:
        workload_data: "{{ workload }}"
        hypervisor_host: compute-01.example.com
        test_nbdkit_export_file: /path/to/workload.yml
        test_nbdkit_ip_allow: 192.168.1.100  # Destination conversion host IP
```

### With TCP Protocol

```yaml
- name: Setup nbdkit with TCP
  ansible.builtin.include_role:
    name: os_migrate.os_migrate.test_nbdkit_hypervisor
  vars:
    workload_data: "{{ item }}"
    hypervisor_host: "{{ compute_hostname }}"
    test_nbdkit_export_file: "{{ export_file_path }}"
    test_nbdkit_protocol: tcp
    test_nbdkit_port: 10809
```

### With SSH Protocol

```yaml
- name: Setup nbdkit with SSH
  ansible.builtin.include_role:
    name: os_migrate.os_migrate.test_nbdkit_hypervisor
  vars:
    workload_data: "{{ item }}"
    hypervisor_host: "{{ compute_hostname }}"
    test_nbdkit_export_file: "{{ export_file_path }}"
    test_nbdkit_protocol: ssh
    test_nbdkit_hypervisor_ssh_user: nova
```

### With IP Restriction

```yaml
- name: Setup nbdkit with IP filtering
  ansible.builtin.include_role:
    name: os_migrate.os_migrate.test_nbdkit_hypervisor
  vars:
    workload_data: "{{ item }}"
    hypervisor_host: "{{ compute_hostname }}"
    test_nbdkit_export_file: "{{ export_file_path }}"
    test_nbdkit_ip_allow: 192.168.1.100  # Only allow destination conversion host
```

## How It Works

### 1. Disk Format Detection

The role uses `qemu-img info` to inspect the disk:

```bash
qemu-img info /var/lib/nova/instances/<uuid>/disk
```

**For qcow2 disks with backing file:**
- Plugin: `nbdkit qcow2`
- Source: Backing file path (e.g., `/var/lib/nova/instances/_base/...`)

**For raw disks or qcow2 without backing file:**
- Plugin: `nbdkit file`
- Source: Instance disk path

### 2. NBDkit Command Construction

**Example for qcow2 with backing file:**
```bash
sudo nbdkit -p 10809 qcow2 /var/lib/nova/instances/_base/9bde3b6613ce0546fdd2bf75b9cc6298d8479b87 --readonly
```

**Example for raw disk:**
```bash
sudo nbdkit -p 10809 file file=/var/lib/nova/instances/<uuid>/disk --readonly
```

**With IP filtering:**
```bash
sudo nbdkit -p 10809 file file=/path/to/disk --readonly --filter=ip ip-allow=192.168.1.100
```

### 3. Export File Update

The role updates the export YAML file with:

```yaml
_migration_params:
  use_nbdkit_direct: true
  nbdkit_socket_uri: "nbd://192.168.24.1:10809"
  nbdkit_port: 10809
```

## Testing

### Verify NBDkit is Running

On the hypervisor:
```bash
sudo netstat -tlnp | grep 10809
```

### Test Connectivity

From destination conversion host:
```bash
# Check NBD info
nbdinfo nbd://hypervisor-ip:10809

# Test copy (to /dev/null for testing)
nbdcopy nbd://hypervisor-ip:10809 /dev/null --progress
```

### Test Over SSH

```bash
nbdinfo "nbd+ssh://root@hypervisor/var/lib/nova/instances/<uuid>/disk"
```

## Output

The role provides:

1. **NBDkit URI**: Full URI for use in migration
2. **Updated export file**: With nbdkit_socket_uri populated
3. **Port information**: For firewall configuration
4. **Debug information**: Disk format, plugin used, etc.

## Cleanup

To stop nbdkit after testing:

```bash
# On hypervisor
sudo pkill -f "nbdkit.*10809"
```

Or let it run until the migration completes.

## Security Considerations

⚠️ **Important Security Notes:**

1. **Use IP filtering**: Always set `test_nbdkit_ip_allow` in production-like testing
2. **Read-only mode**: Keep `test_nbdkit_readonly: true` (default)
3. **Firewall rules**: Ensure nbdkit port is not exposed to untrusted networks
4. **SSH keys**: Secure your SSH keys for hypervisor access
5. **Temporary use**: Stop nbdkit after migration completes

## Troubleshooting

### Port Already in Use

```yaml
# Kill existing nbdkit first
sudo pkill -f "nbdkit.*10809"
```

### Disk Not Found

- Verify instance UUID is correct
- Check instance directory exists: `ls /var/lib/nova/instances/<uuid>/`
- Ensure you're on the correct hypervisor

### Permission Denied

- Ensure SSH user has sudo privileges
- Check disk file permissions

### Connection Refused

- Verify nbdkit is running: `netstat -tlnp | grep 10809`
- Check firewall rules
- Test from hypervisor locally first: `nbdinfo nbd://localhost:10809`

## Example Complete Workflow

```yaml
---
- name: Complete nbdkit test workflow
  hosts: localhost
  tasks:
    # 1. Export workload (creates export file with use_nbdkit_direct: true)
    - name: Export workload
      os_migrate.os_migrate.export_workloads:
        cloud: src
        # ... other params

    # 2. Setup nbdkit on hypervisor
    - name: Read workload
      ansible.builtin.include_vars:
        file: /data/workloads.yml
        name: workload_data

    - name: Spawn nbdkit
      ansible.builtin.include_role:
        name: os_migrate.os_migrate.test_nbdkit_hypervisor
      vars:
        workload_data: "{{ workload_data.resources[0] }}"
        hypervisor_host: compute-01.example.com
        test_nbdkit_export_file: /data/workloads.yml
        test_nbdkit_ip_allow: 192.168.1.100

    # 3. Import workload (reads nbdkit_socket_uri from updated export file)
    - name: Import workload
      os_migrate.os_migrate.import_workloads:
        # ... params
```

## Limitations

- **One instance per port**: Each nbdkit process uses one port
- **Manual hypervisor mapping**: You need to know which hypervisor hosts the instance
- **No automatic cleanup**: nbdkit processes must be manually stopped
- **Testing only**: Not designed for production use

## See Also

- Main nbdkit direct mode documentation: `docs/src/nbdkit-direct-mode.rst`
- NBDkit documentation: https://libguestfs.org/nbdkit.1.html
- NBDcopy documentation: https://libguestfs.org/nbdcopy.1.html
