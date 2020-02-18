#!/bin/bash

set -euxo pipefail

DIR=$(dirname $(realpath $0))
OS_MIGRATE_DIR=$(realpath "$DIR/../..")

### PACKAGES ###

dnf clean all
dnf -y update
dnf -y install ansible gcc make python3-devel python3-openstackclient jq shyaml
# The below packages are for vagrant-libvirt and take a lot of deps,
# build with `NO_VAGRANT=1 make toolbox-build` if Vagrant isn't required.
if [ "${NO_VAGRANT:-}" != "1" ]; then
    dnf -y install ansible libvirt-client rsync openssh-clients vagrant-libvirt
fi
dnf clean all


### VIRTUALENV ###

python3 -m venv /root/venv
set +x
source /root/venv/bin/activate
set -x
pip install --upgrade pip
pip install --upgrade setuptools
pip install -r /build/venv-requirements.txt

cp /build/venv-wrapper /usr/local/bin/venv-wrapper
chmod a+x /usr/local/bin/venv-wrapper

touch /.os-migrate-toolbox
chmod 0444 /.os-migrate-toolbox
