#!/bin/bash

set -euxo pipefail

DIR=$(dirname $(realpath $0))
OS_MIGRATE_DIR=$(realpath "$DIR/../..")

### PACKAGES ###

dnf clean all
dnf -y install ansible make python3-devel python3-openstackclient jq shyaml
# This below packages are for vagrant-libvirt and take a lot of deps,
# comment out if you run vagrant from host rather than from container.
dnf -y install cargo make openssl-devel python3-openstackclient rust; dnf -y install ansible libvirt-client rsync openssh-clients vagrant-libvirt
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
