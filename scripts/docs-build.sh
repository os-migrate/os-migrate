#!/usr/bin/env bash

set -euxo pipefail

# Check if running inside a container (Podman or Docker compatible)
# Podman sets 'container=podman' in /run/.containerenv
if [ ! -f "/run/.containerenv" ]; then
    echo "This script is only meant to be run in a container"
    exit 1
fi

if [ -z "${VIRTUAL_ENV:-}" ]; then
    source "$(VENV_DIR)/bin/activate"
fi

export GITCHANGELOG_CONFIG_FILENAME=./scripts/gitchangelog.rc
gitchangelog > ./docs/src/changelog.rst

cd ./docs/src
make html
