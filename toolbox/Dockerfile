FROM registry.fedoraproject.org/fedora:30
RUN dnf -y install ansible make python3-openstackclient
# This is for vagrant-libvirt and takes a lot of deps, comment out if
# you run vagrant from host rather than container
RUN dnf -y install cargo make openssl-devel python3-openstackclient rust; dnf -y install ansible libvirt-client rsync openssh-clients vagrant-libvirt; dnf clean all
WORKDIR /root/os_migrate
