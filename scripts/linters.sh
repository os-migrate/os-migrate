#!/bin/bash
set -euxo pipefail

# E125 is deliberately excluded. See
# https://github.com/jcrocholl/pep8/issues/126. It's just wrong.
#
# H405 is another one that is good as a guideline, but sometimes
# multiline doc strings just don't have a natural summary
# line. Rejecting code for this reason is wrong.
#
# E251 Skipped due to https://github.com/jcrocholl/pep8/issues/301
#
# The following two are also ignored that we don't think it is useful.
# W503 line break before binary operator
# W504 line break after binary operator
#
# E501 line too long 79 characters seems too little
#
# Flake
# TODO: Have the Ansible and YAML lint fixed first
flake8 \
    --exclude releasenotes,.tox \
    --ignore E125,E251,E402,H405,W503,W504,E501

# Bash hate
find ./ \
     -not -wholename ".tox/*" \
     -and -not -wholename "./local/*" \
     -and -not -wholename "*.test/*" \
     -and -name "*.sh" -print0 \
    | xargs -0 bashate -v --ignore E006

# Yaml lint
find ./ \
     -not -wholename ".tox/*" \
     -and -not -wholename "./local/*" \
     -and -not -wholename "./tests/func/tmp/*" \
     -and -name "*.yml" -print0 \
    | xargs -0 -I {} yamllint -d '{
        extends: default,
        rules: {
            truthy: disable,
            document-start: disable,
            line-length: { max: 150 },
        }
    }' {}

# Match both docs and modules/roles

roles_docs_number=`ls docs/src/roles | wc -l`
roles_readmes_number=`find os_migrate/roles/ -name README.md | wc -l`
roles_number=`ls os_migrate/roles/ | wc -l`

modules_docs_number=`ls docs/src/modules | wc -l`
modules_number=`ls os_migrate/plugins/modules/ | grep -v __pycache__ | wc -l`

pending_readmes=`grep -R role_description_goes_here . | wc -l`

echo "Roles in docs: $roles_docs_number"
echo "Roles: $roles_number"

echo "Modules in docs: $modules_docs_number"
echo "Modules: $modules_number"

if [ "$pending_readmes" -ne "3" ];then
    echo "The README.md files in each role must have";
    echo "a brief description, role_description_goes_here";
    echo "is not allowed.";
    exit 1;
fi

if [ "$roles_readmes_number" -ne "$roles_number" ];then
    echo "The README.md file in each role do not";
    echo "match with the number of existing roles";
    exit 1;
fi

if [ "$roles_docs_number" -ne "$roles_number" ];then
    echo "Links in the roles docs section";
    echo "do not match with the number of existing roles";
    exit 1;
fi

if [ "$modules_docs_number" -ne "$modules_number" ];then
    echo "Links in the modules docs section";
    echo "do not match with the number of existing modules";
    exit 1;
fi

# Fully qualified collection names check
python ./scripts/check_fqcn.py

# Ansible lint
# runtime.yml is skipped until ansible-lint is compatible with it
if ansible --version | grep '^ansible 2.9'; then
    echo "Skipping lint for ansible version 2.9"
else
    find \
        ./os_migrate \
        ./tests \
        -name "*.yml" \
        -and -not -wholename "./os_migrate/meta/runtime.yml" \
        -and -not -wholename "./os_migrate/localhost_inventory.yml" \
        -and -not -wholename "./tests/func/tmp/*" \
        -and -not -wholename "./tests/auth_*" \
        -print0 \
        | xargs -0 ansible-lint -v --exclude=os_migrate/meta/runtime.yml
fi
