
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

test-lint: reinstall
	set -euo pipefail; \
	if [ -z "$${VIRTUAL_ENV:-}" ]; then \
		source /root/venv/bin/activate; \
	fi; \
	./scripts/linters.sh

test-setup-vagrant-devstack:
	./scripts/auth-from-clouds.sh \
		--config toolbox/vagrant/env/clouds.yaml \
		--src devstack \
		--dst devstack-alt \
		> tests/auth.yml

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
		-e os_migrate_data_dir=$(ROOT_DIR)/tests/func/tmpdata \
		-e @$(ROOT_DIR)/tests/auth.yml \
		$(FUNC_TEST_ARGS) test_all.yml

test-e2e: reinstall
	set -euo pipefail; \
	if [ -z "$${VIRTUAL_ENV:-}" ]; then \
		source /root/venv/bin/activate; \
	fi; \
	cd tests/e2e; \
	ansible-playbook \
		-v \
		-i $(ROOT_DIR)/os_migrate/localhost_inventory.yml \
		-e os_migrate_data_dir=$(ROOT_DIR)/tests/func/tmpdata \
		-e os_migrate_src_validate_certs=False \
		-e os_migrate_dst_validate_certs=False \
		-e @$(ROOT_DIR)/tests/auth.yml \
		$(FUNC_TEST_ARGS) test_all.yml

test-fast: test-lint test-sanity test-unit

test-sanity: reinstall
	set -euo pipefail; \
	if [ -z "$${VIRTUAL_ENV:-}" ]; then \
		source /root/venv/bin/activate; \
	fi; \
	cd /root/.ansible/collections/ansible_collections/os_migrate/os_migrate; \
	ansible-test sanity --skip-test import

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
