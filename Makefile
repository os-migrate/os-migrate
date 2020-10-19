.DEFAULT_GOAL := build
SHELL := /bin/bash
ROOT_DIR := $(shell dirname $(realpath $(lastword $(MAKEFILE_LIST))))
OS_MIGRATE := $(HOME)/.ansible/collections/ansible_collections/os_migrate/os_migrate
export OS_MIGRATE

FUNC_TEST_ARGS ?=


# ANSIBLE COLLECTION

build: unlink-latest os_migrate-os_migrate-latest.tar.gz

install: os_migrate-os_migrate-latest.tar.gz
	if [ -z "$${VIRTUAL_ENV:-}" ]; then \
		echo "Sourcing venv."; \
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
		echo "Sourcing venv."; \
		source /root/venv/bin/activate; \
	fi; \
	./scripts/linters.sh

test-setup-vagrant-devstack:
	./scripts/auth-from-clouds.sh \
		--config toolbox/vagrant/env/clouds.yaml \
		--src devstack \
		--dst devstack-alt \
		> tests/auth_tenant.yml

test-setup-vagrant-devstack-admin:
	./scripts/auth-from-clouds.sh \
		--config toolbox/vagrant/env/clouds.yaml \
		--src devstack-admin \
		--dst devstack-admin \
		> tests/auth_admin.yml

test: test-fast test-func

test-func: test-func-tenant test-func-admin

test-func-tenant: reinstall
	set -euo pipefail; \
	if [ -z "$${VIRTUAL_ENV:-}" ]; then \
		echo "Sourcing venv."; \
		source /root/venv/bin/activate; \
	fi; \
	cd tests/func; \
	ansible-playbook \
		-v \
		-i $(ROOT_DIR)/os_migrate/localhost_inventory.yml \
		-e os_migrate_tests_tmp_dir=$(ROOT_DIR)/tests/func/tmp \
		-e os_migrate_data_dir=$(ROOT_DIR)/tests/func/tmp/data \
		-e @$(ROOT_DIR)/tests/auth_tenant.yml \
		$(FUNC_TEST_ARGS) test_as_tenant.yml

test-func-admin: reinstall
	set -euo pipefail; \
	if [ -z "$${VIRTUAL_ENV:-}" ]; then \
		echo "Sourcing venv."; \
		source /root/venv/bin/activate; \
	fi; \
	cd tests/func; \
	ansible-playbook \
		-v \
		-i $(ROOT_DIR)/os_migrate/localhost_inventory.yml \
		-e os_migrate_tests_tmp_dir=$(ROOT_DIR)/tests/func/tmp \
		-e os_migrate_data_dir=$(ROOT_DIR)/tests/func/tmp/data \
		-e @$(ROOT_DIR)/tests/auth_admin.yml \
		$(FUNC_TEST_ARGS) test_as_admin.yml

test-e2e: test-e2e-tenant test-e2e-admin

test-e2e-tenant: reinstall
	set -euo pipefail; \
	if [ -z "$${VIRTUAL_ENV:-}" ]; then \
		echo "Sourcing venv."; \
		source /root/venv/bin/activate; \
	fi; \
	cd tests/e2e; \
	ansible-playbook \
		-v \
		-i $(OS_MIGRATE)/localhost_inventory.yml \
		-e os_migrate_tests_tmp_dir=$(ROOT_DIR)/tests/e2e/tmp \
		-e os_migrate_data_dir=$(ROOT_DIR)/tests/e2e/tmp/data \
		-e os_migrate_conversion_host_key=$(ROOT_DIR)/tests/e2e/tmpdata/conversion/ssh.key \
		-e @$(ROOT_DIR)/tests/auth_tenant.yml \
		-e @$(ROOT_DIR)/tests/e2e/tenant/scenario_variables.yml \
		$(E2E_TEST_ARGS) test_as_tenant.yml

test-e2e-admin: reinstall
	set -euo pipefail; \
	if [ -z "$${VIRTUAL_ENV:-}" ]; then \
		echo "Sourcing venv."; \
		source /root/venv/bin/activate; \
	fi; \
	cd tests/e2e; \
	ansible-playbook \
		-v \
		-i $(OS_MIGRATE)/localhost_inventory.yml \
		-e os_migrate_tests_tmp_dir=$(ROOT_DIR)/tests/e2e/tmp \
		-e os_migrate_data_dir=$(ROOT_DIR)/tests/e2e/tmp/data \
		-e os_migrate_conversion_host_key=$(ROOT_DIR)/tests/e2e/tmpdata/conversion/ssh.key \
		-e @$(ROOT_DIR)/tests/auth_admin.yml \
		-e @$(ROOT_DIR)/tests/e2e/admin/scenario_variables.yml \
		$(E2E_TEST_ARGS) test_as_admin.yml

test-fast: test-lint test-sanity test-unit

test-sanity: reinstall
	set -euo pipefail; \
	if [ -z "$${VIRTUAL_ENV:-}" ]; then \
		echo "Sourcing venv."; \
		source /root/venv/bin/activate; \
	fi; \
	cd /root/.ansible/collections/ansible_collections/os_migrate/os_migrate; \
	ansible-test sanity --skip-test import

test-unit: reinstall
	set -euo pipefail; \
	if [ -z "$${VIRTUAL_ENV:-}" ]; then \
		echo "Sourcing venv."; \
		source /root/venv/bin/activate; \
	fi; \
	cd /root/.ansible/collections/ansible_collections/os_migrate/os_migrate; \
	ansible-test units

# TOOLBOX

toolbox-build:
	if [[ -z "$REUSE_TOOLBOX" || $(REUSE_TOOLBOX) -eq "0" ]]; then \
		echo "Building the toolbox container image"; \
		cd toolbox && \
		podman build --format docker --build-arg NO_VAGRANT=$(NO_VAGRANT) -t localhost/os_migrate_toolbox:latest . && \
		podman tag localhost/os_migrate_toolbox:latest localhost/os_migrate_toolbox:$$(date "+%Y_%m_%d"); \
	else \
		echo "Reusing the toolbox container image"; \
		podman pull docker.pkg.github.com/os-migrate/os-migrate/os_migrate_toolbox:main; \
		podman image tag docker.pkg.github.com/os-migrate/os-migrate/os_migrate_toolbox:main localhost/os_migrate_toolbox:latest; \
		podman image tag localhost/os_migrate_toolbox:latest localhost/os_migrate_toolbox:$$(date "+%Y_%m_%d"); \
		podman image list -a; \
	fi; \

toolbox-clean:
	podman rmi localhost/os_migrate_toolbox:latest
