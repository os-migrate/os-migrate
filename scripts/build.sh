#!/bin/bash

if [ -z "${VIRTUAL_ENV:-}" ]; then
    source /root/venv/bin/activate
fi
set -euxo pipefail


# Uninstall any dependencies if defined
if [ -n "${OS_MIGRATE_REQUIREMENTS_UNINSTALL_BEFORE_OVERRIDE:-}" ]; then
    python3 -m pip uninstall -y ${OS_MIGRATE_REQUIREMENTS_UNINSTALL_BEFORE_OVERRIDE}
fi

# Apply virtualenv version overrides if defined
if [ -n "${OS_MIGRATE_REQUIREMENTS_OVERRIDE:-}" ]; then
    python3 -m pip \
        install \
        --upgrade \
        -r "$OS_MIGRATE_REQUIREMENTS_OVERRIDE" \
        --no-cache-dir
fi

# update version in const.py based on galaxy.yml
VERSION=$(grep '^version: ' os_migrate/galaxy.yml | awk '{print $2}')
sed -i -e "s/^OS_MIGRATE_VERSION = .*$/OS_MIGRATE_VERSION = '$VERSION'  # updated by build.sh/" \
    os_migrate/plugins/module_utils/const.py

ansible-galaxy collection build os_migrate -v --force --output-path releases/
cd releases
ln -sf os_migrate-os_migrate-$VERSION.tar.gz os_migrate-os_migrate-latest.tar.gz
