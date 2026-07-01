Import From Hypervisor Role
============================

This role spawns nbdkit on OpenStack hypervisors (compute nodes) for workloads that have `use_nbdkit_direct: true` in their migration parameters.

## Purpose

This role is part of the nbdkit direct mode migration workflow. It:

1. Reads workloads from `workloads.yml`
2. Filters workloads with `use_nbdkit_direct: true`
3. For each workload:
   - Connects to the hypervisor (from `hypervisor_hostname` in workload data)
   - Finds the instance disk
   - Inspects disk format (qcow2 vs raw) and detects backing files
   - Spawns nbdkit with the correct plugin
   - Updates the workload file with the nbdkit URI

## Workflow Order

```
1. export_workloads.yml      # Exports workloads with hypervisor_hostname
2. import_from_hypervisor.yml # Spawns nbdkit (this role)
3. import_workloads.yml       # Migrates using nbdkit URIs
```

## Usage

```bash
# 1. Export workloads
ansible-playbook export_workloads.yml -e os_migrate_data_dir=/data

# 2. Spawn nbdkit on hypervisors
ansible-playbook import_from_hypervisor.yml -e os_migrate_data_dir=/data

# 3. Import workloads
ansible-playbook import_workloads.yml -e os_migrate_data_dir=/data
```

See full README in the file for more details.
