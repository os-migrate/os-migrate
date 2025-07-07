#!/usr/bin/env bash

tag_name=os-migrate

ansible-builder build -v3 --tag $tag_name
rm -fr "$(pwd)/context/"
