#!/bin/bash

if [ -z "$${VIRTUAL_ENV:-}" ]; then
    source /root/venv/bin/activate
fi
set -euxo pipefail

# update version in const.py based on galaxy.yml
VERSION=$(grep '^version: ' os_migrate/galaxy.yml | awk '{print $2}')
sed -i -e "s/^OS_MIGRATE_VERSION = .*$/OS_MIGRATE_VERSION = '$VERSION'  # updated by build.sh/" \
    os_migrate/plugins/module_utils/const.py

ansible-galaxy collection build os_migrate -v --force --output-path releases/
cd releases
LATEST=$(ls os_migrate-os_migrate*.tar.gz | grep -v latest | sort -V | tail -n1)
ln -sf $LATEST os_migrate-os_migrate-latest.tar.gz
