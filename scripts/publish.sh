#!/usr/bin/env bash

# Exit immediately if a command exits with a non-zero status, if a variable is
# unset, and if a command in a pipeline fails.
set -euo pipefail

# --- Functions ---

# Print an error message and exit.
# @param message The error message to print.
error() {
    echo "Error: $1" >&2
    exit 1
}

# Check if a command exists.
# @param cmd The command to check.
check_command() {
    command -v "$1" >/dev/null 2>&1 || error "$1 is not installed. Please install it to continue."
}

# --- Initial Setup and Dependencies Check ---

check_command "ansible-galaxy"
check_command "curl"
check_command "jq"
check_command "yq" # Using yq as a more standard and powerful YAML processor

# --- Argument Parsing ---

GALAXY_API_KEY="${ANSIBLE_GALAXY_API_KEY:-}" # Use environment variable if set

while (( "$#" )); do
    case "$1" in
        -k|--galaxy-key)
            if [[ -z "${2:-}" ]]; then
                error "A value is required for the --galaxy-key option."
            fi
            GALAXY_API_KEY="$2"
            shift 2
            ;;
        -h|--help)
            echo "Usage: $(basename "$0") [-k <galaxy_key>]"
            echo "Publish an Ansible collection to Galaxy if the version is new."
            echo "The Galaxy API key can also be provided via the ANSIBLE_GALAXY_API_KEY environment variable."
            exit 0
            ;;
        *) # preserve positional arguments
            # If you need to handle other positional arguments, they can be added to an array
            # For this script's purpose, we'll treat them as an error.
            error "Unsupported argument: $1. Use --help for usage information."
            ;;
    esac
done

if [[ -z "$GALAXY_API_KEY" ]]; then
    error "Ansible Galaxy API key not provided. Use the -k flag or the ANSIBLE_GALAXY_API_KEY environment variable."
fi

# --- Main Logic ---

GALAXY_YML="galaxy.yml"

if [[ ! -f "$GALAXY_YML" ]]; then
    error "The '$GALAXY_YML' file was not found in the current directory."
fi

# Read metadata from galaxy.yml
# Note: For yq v4+, the syntax is as shown. For older versions, it might be different.
NAMESPACE=$(yq e '.namespace' "$GALAXY_YML")
NAME=$(yq e '.name' "$GALAXY_YML")
CURRENT_VERSION=$(yq e '.version' "$GALAXY_YML")

echo "--- Collection Details ---"
echo "Namespace: $NAMESPACE"
echo "Name:      $NAME"
echo "Version:   $CURRENT_VERSION"
echo "--------------------------"

# Check if the current version is already published
echo "Checking if version $CURRENT_VERSION is already published on Ansible Galaxy..."

# The API returns a 404 status code if the collection or version doesn't exist.
# We check the HTTP status code to see if the version is published.
http_status=$(curl -s -o /dev/null -w "%{http_code}" "https://galaxy.ansible.com/api/v3/plugin/ansible/content/published/collections/index/$NAMESPACE/$NAME/versions/$CURRENT_VERSION/")

if [[ "$http_status" -eq 200 ]]; then
    echo "Version $CURRENT_VERSION is already published."
    echo "To publish a new version, please update '$GALAXY_YML' and run this script again."
    exit 0
elif [[ "$http_status" -eq 404 ]]; then
    echo "This version is not yet published. Proceeding with publishing..."

    COLLECTION_TARBALL="${NAMESPACE}-${NAME}-${CURRENT_VERSION}.tar.gz"

    if [[ ! -f "$COLLECTION_TARBALL" ]]; then
        make build
    fi

    echo "Publishing $COLLECTION_TARBALL to Ansible Galaxy..."
    ansible-galaxy collection publish "$COLLECTION_TARBALL" --api-key "$GALAXY_API_KEY"
    echo "Successfully published version $CURRENT_VERSION!"
else
    error "Failed to check collection version on Ansible Galaxy. Received HTTP status: $http_status"
fi
