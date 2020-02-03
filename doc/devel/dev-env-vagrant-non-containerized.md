# Installing Vagrant directly on host

```
yum install https://releases.hashicorp.com/vagrant/2.2.6/vagrant_2.2.6_x86_64.rpm -y
vagrant --version
```

```
virsh pool-define-as vagrant dir - - - - "/var/lib/libvirt/images/vagrant"
virsh pool-list --all
virsh pool-build vagrant
virsh pool-start vagrant
virsh pool-autostart vagrant
virsh pool-info vagrant
```

We need to install the libvirt provider

```
yum groupinstall "Virtualization Host" -y
yum install libvirt-devel -y
vagrant plugin install vagrant-libvirt
systemctl restart libvirtd
```

Go to the toolbox/vagrant folder

```
cd toolbox/vagrant
```

```
vagrant box add --name fedora29 https://download.fedoraproject.org/pub/fedora/linux/releases/29/Cloud/x86_64/images/Fedora-Cloud-Base-Vagrant-29-1.2.x86_64.vagrant-libvirt.box
```
Start the environment using the libvirt provider

```
vagrant up --provider libvirt
```
