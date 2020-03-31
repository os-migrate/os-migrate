#!/bin/bash

set -euo pipefail
SCRIPT_NAME=${SCRIPT_NAME:-$(basename $0)}

function exit_error {
    echo >&2 "Error: $*"
    exit 1
}

function main {
    PARSED_ARGS=$(getopt -o ,h \
                         -l ,config:,dst:,help,src: \
                         -n $SCRIPT_NAME -- "$@")
    if [ $? -ne 0 ]; then
        print_usage
        exit 1
    fi
    eval set -- "$PARSED_ARGS"

    local CONFIG=""
    local DST=""
    local SRC=""
    while true ; do
        case "$1" in
            --help|-h) print_usage; exit 0;;
            --config) CONFIG="$2"; shift 2;;
            --dst) DST="$2"; shift 2;;
            --src) SRC="$2"; shift 2;;
            --) shift ; break ;;
            *) echo "$*"; echo "Error: unsupported option $1." ; exit 1 ;;
        esac
    done

    if [ "$CONFIG" = "" ]; then
        exit_error "--config argument was not provided."
    fi
    if [ "$DST" = "" -a "$SRC" = "" ]; then
        exit_error "Neither of --src or --dst arguments was provided."
    fi

    if [ -n "$SRC" ]; then
        print_auth_from_clouds "$CONFIG" "$SRC" "os_migrate_src_"
    fi
    if [ -n "$DST" ]; then
        print_auth_from_clouds "$CONFIG" "$DST" "os_migrate_dst_"
    fi
}

function print_auth_from_clouds {
    local CONFIG="$1"
    local CLOUD="$2"
    local PREFIX="$3"

    local CLOUDS
    CLOUDS=$(cat "$CONFIG")
    # Fails with error message if $CLOUD isn't present, otherwise prints nothing.
    shyaml get-value "clouds.$CLOUD" <<<"$CLOUDS" > /dev/null

    local AUTH
    local AUTH_TYPE
    local REGION_NAME
    AUTH=$(shyaml get-value "clouds.$CLOUD.auth" <<<"$CLOUDS" 2> /dev/null || true)
    AUTH_TYPE=$(shyaml get-value "clouds.$CLOUD.auth_type" <<<"$CLOUDS" 2> /dev/null || true)
    REGION_NAME=$(shyaml get-value "clouds.$CLOUD.region_name" <<<"$CLOUDS" 2> /dev/null || true)

    if [ -n "$AUTH" ]; then
        echo "${PREFIX}auth:"
        echo "$(sed -e 's/^/  /' <<< "$AUTH")"
    fi
    if [ -n "$AUTH_TYPE" ]; then
        echo "${PREFIX}auth_type: $AUTH_TYPE"
    fi
    if [ -n "$REGION_NAME" ]; then
        echo "${PREFIX}region_name: $REGION_NAME"
    fi
}

function print_usage {
    echo >&2 "Usage: $SCRIPT_NAME [options]"
    echo >&2
    echo >&2 "Read clouds.yaml file and write auth params for os_migrate on stdout."
    echo >&2 "The 'config' option and at least one of 'src' or 'dst' are mandatory."
    echo >&2
    echo >&2 "Options:"
    echo >&2 "  --help, -h  Print this help message and exit"
    echo >&2
    echo >&2 "  --config    Path to clouds.yaml file"
    echo >&2 "  --dst       Cloud name to use as migration destination"
    echo >&2 "  --src       Cloud name to use as migration source"
}

main "$@"
