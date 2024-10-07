#!/bin/bash

set -euxo pipefail

DIR=$(dirname $(realpath $0))
OS_MIGRATE_DIR=$(realpath "$DIR/../..")
ANSIBLE_PYTHON=python3

### PACKAGES ###

dnf -y upgrade --refresh
dnf -y install \
    cargo \
    findutils \
    gcc \
    graphviz \
    iputils \
    java-11-openjdk \
    jq \
    make \
    plantuml \
    python3-devel \
    python3-openstackclient \
    "$ANSIBLE_PYTHON" \
    shyaml \

# The below packages are for vagrant-libvirt and take a lot of deps,
# build with `NO_VAGRANT=1 make toolbox-build` if Vagrant isn't required.
if [ "${NO_VAGRANT:-0}" != "1" ]; then
    dnf -y install ansible libvirt-client rsync openssh-clients vagrant-libvirt
fi

### VIRTUALENV ###

"$ANSIBLE_PYTHON" -m venv /root/venv
set +x
source /root/venv/bin/activate
set -x
# We need to be sure we use the latest versions of
# pip, virtualenv and setuptools
python3 -m pip install --upgrade \
                        pip \
                        virtualenv \
                        setuptools
python3 -m pip install --upgrade -r /build/venv-requirements.txt

cp /build/venv-wrapper /usr/local/bin/venv-wrapper
chmod a+x /usr/local/bin/venv-wrapper

cat /build/galaxy.yml | shyaml get-value dependencies | \
    while read -r value; do
        depname=$(echo $value | cut -f1 -d':' | sed "s/'//g" | sed "s/ //g")
        depver=$(echo $value | cut -f2 -d':' | sed "s/'//g" | sed "s/ //g")
        ansible-galaxy collection install $depname:$depver
    done

touch /.os-migrate-toolbox
chmod 0444 /.os-migrate-toolbox

### CLEANUP ###

dnf clean all
python3 -m pip cache purge
