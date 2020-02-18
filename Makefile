.DEFAULT_GOAL := build
SHELL := /bin/bash
ROOT_DIR := $(shell dirname $(realpath $(lastword $(MAKEFILE_LIST))))

FUNC_TEST_ARGS ?=


# ANSIBLE COLLECTION

build: unlink-latest os_migrate-os_migrate-latest.tar.gz

install: os_migrate-os_migrate-latest.tar.gz
	if [ -n "${VIRTUAL_ENV:-}" ]; then \
		source /root/venv/bin/activate; \
	fi; \
	cd releases; \
	ansible-galaxy collection install --force os_migrate-os_migrate-latest.tar.gz

clean:
	ls releases/os_migrate-os_migrate*.tar.gz | xargs rm

reinstall: build install


# ANSIBLE COLLECTION -- utility targets

unlink-latest:
	rm releases/os_migrate-os_migrate-latest.tar.gz || true

os_migrate-os_migrate-latest.tar.gz:
	./scripts/build.sh


# TESTS

test-setup-vagrant-devstack:
	cp toolbox/vagrant/env/clouds.yaml tests/func/clouds.yaml && \
	sed -i -e "s/ devstack:/ testsrc:/" tests/func/clouds.yaml && \
	sed -i -e "s/ devstack-alt:/ testdst:/" tests/func/clouds.yaml

test: test-fast test-func

test-func: reinstall
	set -euo pipefail; \
	if [ -z "$${VIRTUAL_ENV:-}" ]; then \
		source /root/venv/bin/activate; \
	fi; \
	cd tests/func; \
	ansible-playbook \
		-v \
		-i $(ROOT_DIR)/os_migrate/localhost_inventory.yml \
		-e os_migrate_src_cloud=testsrc \
		-e os_migrate_dst_cloud=testdst \
		-e os_migrate_data_dir=$(ROOT_DIR)/tests/func/tmpdata \
		$(FUNC_TEST_ARGS) test_all.yml

test-fast: test-sanity test-unit

# We have to skip validate-modules sanity test because it checks for
# GPLv3 licensing and AFAICT that check can't be disabled.
test-sanity: reinstall
	set -euo pipefail; \
	if [ -z "$${VIRTUAL_ENV:-}" ]; then \
		source /root/venv/bin/activate; \
	fi; \
	cd /root/.ansible/collections/ansible_collections/os_migrate/os_migrate; \
	ansible-test sanity --skip-test import --skip-test validate-modules

test-unit: reinstall
	set -euo pipefail; \
	if [ -z "$${VIRTUAL_ENV:-}" ]; then \
		source /root/venv/bin/activate; \
	fi; \
	cd /root/.ansible/collections/ansible_collections/os_migrate/os_migrate; \
	ansible-test units

# TOOLBOX

toolbox-build:
	cd toolbox && \
	podman build --build-arg NO_VAGRANT=$(NO_VAGRANT) -t localhost/os_migrate_toolbox:latest . && \
	podman tag localhost/os_migrate_toolbox:latest localhost/os_migrate_toolbox:$$(date "+%Y_%m_%d")

toolbox-clean:
	podman rmi localhost/os_migrate_toolbox:latest
