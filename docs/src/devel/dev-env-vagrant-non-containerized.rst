Installing Vagrant directly on host (alternative path)
======================================================

Normally you should run Vagrant containerized as the `developer
environment setup <dev-env-setup.rst>`_ doc suggests. If you have a
reason to install on bare metal instead, here are relevant
instructions.

::

   yum install https://releases.hashicorp.com/vagrant/2.4.1/vagrant-2.4.1-1.x86_64.rpm -y
   vagrant --version

::

   virsh pool-define-as vagrant dir - - - - "/var/lib/libvirt/images/vagrant"
   virsh pool-list --all
   virsh pool-build vagrant
   virsh pool-start vagrant
   virsh pool-autostart vagrant
   virsh pool-info vagrant

We need to install the libvirt provider

::

   yum groupinstall "Virtualization Host" -y
   yum install libvirt-devel -y
   vagrant plugin install vagrant-libvirt
   systemctl restart libvirtd

Go to the toolbox/vagrant folder

::

   cd toolbox/vagrant

::

   vagrant box add --name fedora37 https://archives.fedoraproject.org/pub/archive/fedora/linux/releases/37/Cloud/x86_64/images/Fedora-Cloud-Base-Vagrant-37-1.7.x86_64.vagrant-libvirt.box

Start the environment using the libvirt provider

::

   vagrant up --provider libvirt
