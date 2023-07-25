#!/bin/bash

if [ -z "${VIRTUAL_ENV:-}" ]; then
    source /root/venv/bin/activate
fi
set -euxo pipefail

# Set cache dir
cache_dir=$(python3 -m pip cache dir)

# Uninstall any dependencies if defined
if [ -n "${OS_MIGRATE_REQUIREMENTS_UNINSTALL_BEFORE_OVERRIDE:-}" ]; then
    python3 -m pip uninstall --yes ${OS_MIGRATE_REQUIREMENTS_UNINSTALL_BEFORE_OVERRIDE}
fi

# Apply virtualenv version overrides if defined
if [ -n "${OS_MIGRATE_REQUIREMENTS_OVERRIDE:-}" ]; then
    python3 -m pip cache purge && rm -rf $cache_dir
    sleep 1
    python3 -m pip install --upgrade pip
    python3 -m pip cache purge && rm -rf $cache_dir

    # Workaround for ERROR: Could not install packages due to an
    #     OSError: [Errno 39] Directory not empty: '__pycache__'
    PYTHON_SITE_PACKAGES_DIR=$(python -c "from distutils.sysconfig import get_python_lib; print(get_python_lib())")
    if [[ "$OS_MIGRATE_REQUIREMENTS_OVERRIDE" =~ "openstacksdk" ]]; then
        find "$PYTHON_SITE_PACKAGES_DIR/openstack" -depth -type d -name __pycache__ -exec rm -r '{}' \;
    fi
    if [[ "$OS_MIGRATE_REQUIREMENTS_OVERRIDE" =~ "openstackclient" ]]; then
        find "$PYTHON_SITE_PACKAGES_DIR/openstackclient" -depth -type d -name __pycache__ -exec rm -r '{}' \;
    fi

    if [ -z "$(ls -A $cache_dir)" ]; then
        echo "Cache directory is empty."
    else
        echo "Cache directory is not empty. Removing contents..."
        rm -rf $cache_dir/*
        echo "Cache directory cleaned."
    fi

    python3 -m pip \
        install \
        --upgrade \
        -r "$OS_MIGRATE_REQUIREMENTS_OVERRIDE"
fi

# update version in const.py based on galaxy.yml
VERSION=$(grep '^version: ' os_migrate/galaxy.yml | awk '{print $2}')
sed -i -e "s/^OS_MIGRATE_VERSION = .*$/OS_MIGRATE_VERSION = '$VERSION'  # updated by build.sh/" \
    os_migrate/plugins/module_utils/const.py

ansible-galaxy collection build os_migrate -v --force --output-path releases/
cd releases
ln -sf os_migrate-os_migrate-$VERSION.tar.gz os_migrate-os_migrate-latest.tar.gz
