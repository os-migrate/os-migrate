---
name: Request For Demo
about: Template for requesting demo's, walk throughs or insight from migrations team
title: 'Request for Demo - name/company'
labels: ''
assignees: ''
---

### Channel
- TAM: `point of contact`
- Engineer: `point of contact`
- Target date: `date`

### Migration details
1. What is the impact of potential failures? Is cloud-scoped risk allowed? Tenant-scoped?
2. Is controlplane downtime allowed? Is rolling downtime of workloads allowed?
3. What type of workload will we migrate? Is the workload stateless? Is it required to preserve the workload's state? Is the workload state stored on its boot disk or attached volumes? Are there restrictions on data handling?
4. Is there extra hardware available? Is there physical space in the data center to allocate a new control plane?
5. Is there old or deprecated hardware to be replaced? When repurposing hardware, should some of it be repurposed in batches? How many VMs, how much storage will be migrated?
6. Is there any additional internal or external dependency? Is there a dependency on any other third-party vendor? For example, an SDN vendor.

### Simple checklist
- [ ] Migration details completed
- [ ] Point of contacts assigned
- [ ] Target date confirmed
