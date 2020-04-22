#!/bin/bash

PARAMS=""
while (( "$#" )); do
    case "$1" in
        -k|--galaxy-key)
            KARG=$2
            shift 2
            ;;
        --) # end argument parsing
            shift
            break
            ;;
        -*|--*=) # unsupported flags
            echo "Error: Unsupported flag $1" >&2
            echo "Please use ./publish.sh [-k <galaxy key> | --galaxy-key <galaxy key>]" >&2
            exit 1
            ;;
        *) # preserve positional arguments
            PARAMS="$PARAMS $1"
            shift
        ;;
    esac
done

if [ ! -e /.os-migrate-toolbox ]; then
    echo "Error: This script must be run from an os-migrate-toolbox container" >&2
    echo "to ensure having all dependencies available and in expected versions." >&2
    exit 1
fi

#
# Initial variables
#

namespace=os_migrate
name=os_migrate
all_published_versions=$(curl https://galaxy.ansible.com/api/v2/collections/$namespace/$name/versions/ | jq -r '.results' | jq -c '.[].version')
current_galaxy_version=$(cat os_migrate/galaxy.yml | shyaml get-value version)
current_galaxy_namespace=$(cat os_migrate/galaxy.yml | shyaml get-value namespace)
current_galaxy_name=$(cat os_migrate/galaxy.yml | shyaml get-value name)
publish="1"

#
# Check all the current published versions and if the
# packaged to be created has a different version, then
# we publish it to Galaxy Ansible
#

for ver in $all_published_versions; do
    echo "--"
    echo "Published: "$ver
    echo "Built: "$current_galaxy_version
    echo ""
    if [[ $ver == \"$current_galaxy_version\" ]]; then
        echo "The current version $current_galaxy_version is already published"
        echo "Proceed to update the galaxy.yml file with a newer version"
        echo "After the version change, when the commit is merged, then the package"
        echo "will be published automatically."
        publish="0"
    fi
done

if [ "$publish" == "1" ]; then
    echo 'This version is not published, publishing!...'
    ./scripts/build.sh
    ansible-galaxy collection publish \
        releases/$current_galaxy_namespace-$current_galaxy_name-$current_galaxy_version.tar.gz \
        --api-key $KARG
fi
