#!/bin/bash

set -eu

mkdir -p env
vagrant ssh-config > env/ssh-config
vagrant ssh -c 'cat /etc/openstack/clouds.yaml' > env/clouds.yaml
