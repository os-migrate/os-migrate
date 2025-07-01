#!/usr/bin/env bash

set -euxo pipefail
if [ -z "${VIRTUAL_ENV:-}" ]; then
    source /root/venv/bin/activate
fi

export GITCHANGELOG_CONFIG_FILENAME=./scripts/gitchangelog.rc
gitchangelog > ./docs/src/changelog.rst

cd ./docs/src
make html
