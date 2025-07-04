#!/usr/bin/env bash

tag_name=vmware-migration-kit

ansible-builder build --tag $tag_name
rm -fr "$(pwd)/context/"
