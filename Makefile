.DEFAULT_GOAL := build
SHELL := /bin/bash
ROOT_DIR := $(shell dirname $(realpath $(lastword $(MAKEFILE_LIST))))

FUNC_TEST_PLAYBOOK ?= all


# ANSIBLE COLLECTION

build: unlink-latest os_migrate-os_migrate-latest.tar.gz

install: os_migrate-os_migrate-latest.tar.gz
	if [ -n "${VIRTUAL_ENV:-}" ]; then \
		source /root/venv/bin/activate; \
	fi; \
	ansible-galaxy collection install --force os_migrate-os_migrate-latest.tar.gz

clean:
	ls os_migrate-os_migrate*.tar.gz | xargs rm

reinstall: build install


# ANSIBLE COLLECTION -- utility targets

unlink-latest:
	rm os_migrate-os_migrate-latest.tar.gz || true

os_migrate-os_migrate-latest.tar.gz:
	set -euxo pipefail; \
	if [ -n "${VIRTUAL_ENV:-}" ]; then \
		source /root/venv/bin/activate; \
	fi; \
	ansible-galaxy collection build --force os_migrate; \
	LATEST=$$(ls os_migrate-os_migrate*.tar.gz | grep -v latest | sort -V | tail -n1); \
	ln -sf $$LATEST os_migrate-os_migrate-latest.tar.gz


# TESTS

test-setup-vagrant-devstack:
	cp toolbox/vagrant/env/clouds.yaml tests/func/clouds.yaml && \
	sed -i -e "s/ devstack:/ testsrc:/" tests/func/clouds.yaml && \
	sed -i -e "s/ devstack-alt:/ testdst:/" tests/func/clouds.yaml

test: test-func

test-func: reinstall
	set -euxo pipefail; \
	cd tests/func; \
	ansible-playbook \
		-v \
		-i $(ROOT_DIR)/os_migrate/localhost_inventory.yml \
		-e os_migrate_src_cloud=testsrc \
		-e os_migrate_dst_cloud=testdst \
		-e os_migrate_data_dir=$(ROOT_DIR)/tests/func/tmpdata \
		test_$(FUNC_TEST_PLAYBOOK).yml


# TOOLBOX

toolbox-build:
	cd toolbox && \
	podman build -t localhost/os_migrate_toolbox:latest . && \
	podman tag localhost/os_migrate_toolbox:latest localhost/os_migrate_toolbox:$$(date "+%Y_%m_%d")

toolbox-clean:
	podman rmi localhost/os_migrate_toolbox:latest
