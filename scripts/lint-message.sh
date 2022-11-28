#!/bin/bash
set -euo pipefail

ALLOWED_TYPES=(
    new
    fix
    chg
    oth
    dev
)


MAX_FIRST_LINE_LENGTH=75

function lint_commit_message {
    local commit_msg="$1"
    local first_line;
    first_line=$(head -n1 <<<"$commit_msg")

    local first_line_length;
    first_line_length=$(wc -c <<<"$first_line")
    if [ "$first_line_length" -gt $MAX_FIRST_LINE_LENGTH ]; then
        error_header_first_line "$first_line"
        echo "The line has $first_line_length characters, but $MAX_FIRST_LINE_LENGTH is maximum (incl. newline)."
        exit 1
    fi

    # local first_line_regex='^([^\(:]+): (.+)$'
    # The following should work once we support scopes:
    local first_line_regex='^([^\(:]+)(\([^)]+\))?!?: (.+)$'
    if [[ "$first_line" =~ $first_line_regex ]]; then
        local type="${BASH_REMATCH[1]}"
        local scope_parens="${BASH_REMATCH[2]}"
        local scope=${scope_parens/(/}
        scope=${scope/)/}
        if ! printf '%s\n' "${ALLOWED_TYPES[@]}" | grep -qxF "$type"; then
            error_header_first_line "$first_line"
            echo "Unrecognized type '$type'. Allowed types: ${ALLOWED_TYPES[*]}"
            exit 1
        fi
        if [ -n "$scope_parens" ]; then
            echo "Scopes are presently not allowed in commit messages."
            exit 1
        fi
        # if [ -n "$scope_parens" ] && ! printf '%s\n' "${ALLOWED_SCOPES[@]}" | grep -qxF "$scope"; then
        #     error_header_first_line "$first_line"
        #     echo "Unrecognized scope '$scope'. Allowed scopes: ${ALLOWED_SCOPES[*]}"
        #     exit 1
        # fi
    else
        error_header_first_line "$first_line"
        echo "The first line does not match pattern. Examples of first line formatting:"
        echo "type: summary"
        echo "type!: summary"
        # echo "type(scope): summary"
        # echo "type(scope)!: summary"
        echo
        echo "Allowed types: ${ALLOWED_TYPES[*]}"
        # echo "Allowed scopes: ${ALLOWED_SCOPES[*]}"
        echo "Variants with exclamation mark should be used for breaking changes."
        exit 1
    fi

    local num_lines;
    num_lines=$(wc -l <<<"$commit_msg")
    if [ "$num_lines" -gt 1 ]; then
        if [ "$num_lines" -lt 3 ]; then
            error_header_first_line "$first_line"
            echo "The message has $num_lines lines. It must have either 1, or 3+."
            exit 1
        fi
        local second_line;
        second_line=$(sed -n 2p <<<"$commit_msg")
        if [ -n "$second_line" ]; then
            error_header_first_line "$first_line"
            echo "The 2nd line of commit message must be empty."
            exit 1
        fi
        local third_line;
        third_line=$(sed -n 3p <<<"$commit_msg")
        if [ -z "$third_line" ]; then
            error_header_first_line "$first_line"
            echo "The 3rd line of commit message must not be empty."
            exit 1
        fi
    fi
}

function error_header_first_line {
    echo "ERROR: Commit does not follow convention:"
    echo "$1"
    echo
}

# change this back to original dir path before testing on line 98
lint_commit_message "$(< /dev/stdin)"
