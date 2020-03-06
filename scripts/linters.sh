#!/bin/bash
set -euxo pipefail

# Ansible lint
find ./ -not -wholename "*.tox/*" -and -name "*.yml"|while read file; do
    ansible-lint $file
done

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
flake8 --exclude releasenotes,.tox --ignore E125,E251,E402,H405,W503,W504,E501

# Bash hate
find ./ -not -wholename "*.tox/*" -and -not -wholename "*.test/*" -and -name "*.sh" -print0 | xargs -0 bashate -v --ignore E006

#Yaml lint
find ./ -not -wholename "*.tox/*" -and -name "*.yml"  -print0 | xargs -0 yamllint
