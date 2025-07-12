# Let's use bash!
SHELL := /bin/bash
.SHELLFLAGS := -euo pipefail -c

# --- Configuration Variables ---
# Reuse container content if possible. Set to 'false' to always rebuild.
USE_CACHE ?= true

# Container and Python Configuration
CONTAINER_ENGINE ?= podman
CONTAINER_IMAGE  ?= quay.io/centos/centos:stream10
CONTAINER_NAME   ?= os-migrate
PYTHON_VERSION   ?= 3.12

# Directory and Mount Structure
COLLECTION_ROOT         := $(CURDIR)
CONTAINER_COLLECTION_ROOT := /code
MOUNT_PATH                := $(COLLECTION_ROOT):$(CONTAINER_COLLECTION_ROOT)
VENV_DIR                  := $(CONTAINER_COLLECTION_ROOT)/.venv

# --- Core Logic for Container Creation ---

# Check if the container already exists and strip any whitespace/newlines
CONTAINER_EXISTS = $(strip $(shell $(CONTAINER_ENGINE) ps -a -q -f name=$(CONTAINER_NAME)))


# --- Dynamic Variable Setup ---

# Check if SELinux is enforcing to set container security options
GETENFORCE_CMD := $(shell command -v getenforce 2>/dev/null)
SELINUX_ENFORCING := $(shell $(GETENFORCE_CMD) 2>/dev/null | grep -q "Enforcing" && echo "yes" || echo "no")

ifeq ($(SELINUX_ENFORCING),yes)
    SECURITY_OPT := --security-opt label=disable
else
    SECURITY_OPT :=
endif

# Extract collection metadata from galaxy.yml
GALAXY_YML := $(COLLECTION_ROOT)/galaxy.yml
ifneq ($(wildcard $(GALAXY_YML)),)
    COLLECTION_NAMESPACE := $(shell grep -E "^namespace:" $(GALAXY_YML) | sed 's/namespace: *//g')
    COLLECTION_NAME      := $(shell grep -E "^name:" $(GALAXY_YML) | sed 's/name: *//g')
    COLLECTION_VERSION   := $(shell grep -E "^version:" $(GALAXY_YML) | sed 's/version: *//g')
    COLLECTION_TARBALL   := $(COLLECTION_NAMESPACE)-$(COLLECTION_NAME)-$(COLLECTION_VERSION).tar.gz
else
    COLLECTION_TARBALL   :=
endif

# --- Core Logic for Container Creation ---

# Check if the container already exists
CONTAINER_EXISTS = $(shell $(CONTAINER_ENGINE) ps -a -q -f name=$(CONTAINER_NAME))

# Determine if we need to create a container based on cache settings and existence.
# Default to 0 (don't create).
CREATE_CONTAINER := 0
ifeq ($(USE_CACHE),true)
    # If using cache, only create if the container doesn't exist.
    ifeq ($(CONTAINER_EXISTS),)
        CREATE_CONTAINER := 1
    endif
else
    # If not using cache, always create a fresh container.
    CREATE_CONTAINER := 1
endif

# --- Phony Targets Definition ---
.PHONY: all help build clean-build tests test-ansible-lint test-ansible-sanity test-ansible-units \
        create-centos-container clean-centos-container check-root check-python-version \
        create-venv install-deps install generate-auth-files

# --- Main User-Facing Targets ---

# Default target when running `make`
all: build

# Help screen
help:
	@echo "Available targets:"
	@echo "  help                  - Display this help message"
	@echo "  build                 - Build the Ansible collection tarball"
	@echo "  clean-build           - Remove the built collection tarball"
	@echo "  install               - Build and install the collection and all dependencies in the container"
	@echo "  tests                 - Launch all available tests (lint, sanity, units)"
	@echo "  test-ansible-lint     - Launch ansible-lint tests"
	@echo "  test-ansible-sanity   - Launch ansible-sanity tests"
	@echo "  test-ansible-units    - Launch ansible-test unit tests"
	@echo "  test-e2e-tenant       - Launch e2e tenant tests"
	@echo "  test-e2e-admin        - Launch e2e admin tests"
	@echo "  generate-auth-files   - Generate auth files for e2e tests"
	@echo ""
	@echo "  create-centos-container - Create the CentOS container (if needed)"
	@echo "  clean-centos-container  - Stop and remove the CentOS container"
	@echo "  create-venv           - Create the Python virtual environment in the container"
	@echo "  install-deps          - Install Python dependencies from requirements files"
	@echo ""
	@echo "Customizable variables:"
	@echo "  USE_CACHE        - Reuse container if it exists (default: $(USE_CACHE))"
	@echo "  CONTAINER_ENGINE - Container runtime (default: $(CONTAINER_ENGINE))"
	@echo "  CONTAINER_IMAGE  - Container image (default: $(CONTAINER_IMAGE))"
	@echo "  PYTHON_VERSION   - Python version to use in the container (default: $(PYTHON_VERSION))"

# --- Build Targets ---

build: check-root clean-build install-deps
	@echo "--- Building Ansible collection: $(COLLECTION_TARBALL) ---"
	@$(CONTAINER_ENGINE) exec -w $(CONTAINER_COLLECTION_ROOT) $(CONTAINER_NAME) bash -c '\
		source $(VENV_DIR)/bin/activate; \
		ansible-galaxy collection build'

clean-build:
	@echo "--- Cleaning built collection ---"
	@if [ -n "$(COLLECTION_TARBALL)" ]; then \
		if [ -f "$(COLLECTION_TARBALL)" ]; then \
			echo "Removing $(COLLECTION_TARBALL)"; \
			rm -f "$(COLLECTION_TARBALL)"; \
		fi \
	else \
		echo "Skipping removal, collection tarball name not determined from galaxy.yml."; \
	fi

# --- Container and Environment Setup Targets ---

# Define a reusable function to verify we're in the right directory
define verify_collection_root
    @if [ ! -f "$(COLLECTION_ROOT)/galaxy.yml" ]; then \
        echo "Error: Must be run from the Ansible collection root directory (missing galaxy.yml)."; \
        exit 1; \
    fi
endef

check-root:
	$(call verify_collection_root)

create-centos-container:
ifeq ($(CREATE_CONTAINER),1)
	@# This recipe runs only if a new container is needed.
	@# First, check with a shell 'if' if the old one must be cleaned up.
	@if [ "$(USE_CACHE)" = "false" ] && [ -n "$(CONTAINER_EXISTS)" ]; then \
		echo "--- Stale container found and USE_CACHE is false. Cleaning it first. ---"; \
		$(MAKE) clean-centos-container; \
	fi
	@echo "--- Spawning new container: $(CONTAINER_NAME) ---"
	@$(CONTAINER_ENGINE) run --pull always -q --rm -d --name $(CONTAINER_NAME) -v $(MOUNT_PATH) \
		$(SECURITY_OPT) $(CONTAINER_IMAGE) sleep infinity
else
	@# This recipe runs if CREATE_CONTAINER is 0
	@echo "--- Using cached container ---"
endif

clean-centos-container:
	@echo "--- Removing container '$(CONTAINER_NAME)' if it exists ---"
	@$(CONTAINER_ENGINE) rm -f $(CONTAINER_NAME)

check-python-version: create-centos-container
	@echo "--- Checking for Python $(PYTHON_VERSION) in container ---"
	@$(CONTAINER_ENGINE) exec $(CONTAINER_NAME) bash -c '\
	if [[ ! -x "$$(command -v pip$(PYTHON_VERSION))" ]]; then \
		echo "Installing Python $(PYTHON_VERSION) development packages..."; \
		dnf upgrade --refresh -y --skip-broken --nobest && \
		dnf -y install gcc python$(PYTHON_VERSION) python$(PYTHON_VERSION)-devel >/dev/null || \
			(echo "Error: packages are unavailable." && exit 1); \
	fi'

create-venv: check-python-version
	@echo "--- Ensuring venv exists at $(VENV_DIR) ---"
	@$(CONTAINER_ENGINE) exec -w $(CONTAINER_COLLECTION_ROOT) $(CONTAINER_NAME) bash -c '\
		if [[ ! -d "$(VENV_DIR)" ]]; then \
			echo "Creating venv..."; \
			python$(PYTHON_VERSION) -m venv $(VENV_DIR); \
		fi'

install-deps: create-venv
	@echo "--- Installing/updating Python dependencies ---"
	@$(CONTAINER_ENGINE) exec -w $(CONTAINER_COLLECTION_ROOT) $(CONTAINER_NAME) bash -c '\
		source $(VENV_DIR)/bin/activate; \
		pip install --root-user-action ignore -q --upgrade pip; \
		pip install --root-user-action ignore -q -r requirements.txt; \
		pip install --root-user-action ignore -q -r requirements-tests.txt'

install: build
	@echo "--- Installing collection $(COLLECTION_TARBALL) into the container ---"
	@$(CONTAINER_ENGINE) exec -w $(CONTAINER_COLLECTION_ROOT) $(CONTAINER_NAME) bash -c '\
		source $(VENV_DIR)/bin/activate; \
		ansible-galaxy collection install $(COLLECTION_TARBALL) --force-with-deps'

# --- Test Targets ---

tests: test-ansible-lint test-ansible-sanity test-ansible-units

test-ansible-lint: install-deps install
	@echo "--- Launching ansible-lint ---"
	@$(CONTAINER_ENGINE) exec -w $(CONTAINER_COLLECTION_ROOT) $(CONTAINER_NAME) bash -c '\
		source $(VENV_DIR)/bin/activate && ansible-lint'
	@if [[ $(USE_CACHE) == false ]]; then $(MAKE) clean-centos-container; fi

test-ansible-sanity: install-deps install
	@echo "--- Running Ansible sanity tests ---"
	@$(CONTAINER_ENGINE) exec -w $(CONTAINER_COLLECTION_ROOT) $(CONTAINER_NAME) bash -c '\
		source $(VENV_DIR)/bin/activate && \
		cd /root/.ansible/collections/ansible_collections/$(COLLECTION_NAMESPACE)/$(COLLECTION_NAME) && \
		ansible-test sanity --python $(PYTHON_VERSION) --requirements'
	@if [[ $(USE_CACHE) == false ]]; then $(MAKE) clean-centos-container; fi

test-ansible-units: install-deps install
	@echo "--- Running Ansible unit tests ---"
	@$(CONTAINER_ENGINE) exec -w $(CONTAINER_COLLECTION_ROOT) $(CONTAINER_NAME) bash -c '\
		source $(VENV_DIR)/bin/activate && \
		cd /root/.ansible/collections/ansible_collections/$(COLLECTION_NAMESPACE)/$(COLLECTION_NAME) && \
		ansible-test units --python $(PYTHON_VERSION) --local'
	@if [[ $(USE_CACHE) == false ]]; then $(MAKE) clean-centos-container; fi


# --- E2E Test Auth Generation ---

generate-auth-files: install-deps install
	@echo "--- Generating auth files ---"
	@echo "SRC_CLOUD: $(SRC_CLOUD)"
	@echo "DST_CLOUD: $(DST_CLOUD)"
	@if [ -z "$(SRC_CLOUD)" ] || [ -z "$(DST_CLOUD)" ]; then \
		echo "Error: SRC_CLOUD and DST_CLOUD variables must be set"; \
		exit 1; \
	fi
	@$(CONTAINER_ENGINE) exec -w $(CONTAINER_COLLECTION_ROOT) $(CONTAINER_NAME) bash -c '\
		source "$(VENV_DIR)/bin/activate" && \
		pip install --root-user-action ignore -q shyaml && \
		dnf -y install util-linux openssh-clients && \
		./scripts/auth-from-clouds.sh --config "$(CONTAINER_COLLECTION_ROOT)/tests/clouds.yml" --src "$(SRC_CLOUD)" --dst "$(DST_CLOUD)" | tee "$(CONTAINER_COLLECTION_ROOT)/tests/auth_tenant.yml"'


test-e2e-tenant: install-deps install generate-auth-files
	@echo "--- Running e2e tenant tests ---"
	@$(CONTAINER_ENGINE) exec -w $(CONTAINER_COLLECTION_ROOT) $(CONTAINER_NAME) bash -c '\
		if [ ! -f "$(CONTAINER_COLLECTION_ROOT)/tests/auth_tenant.yml" ]; then \
			echo "Error: auth_tenant.yml not found. Please run auth generation first."; \
			exit 1; \
		fi && \
		source $(VENV_DIR)/bin/activate && \
		cd tests/e2e; \
		ansible-playbook \
			-v \
			-i $(CONTAINER_COLLECTION_ROOT)/inventory/localhost.yml \
			-e os_migrate_tests_tmp_dir=$(CONTAINER_COLLECTION_ROOT)/tests/e2e/tmp \
			-e os_migrate_data_dir=$(CONTAINER_COLLECTION_ROOT)/tests/e2e/tmp/data \
			-e os_migrate_conversion_host_key=$(CONTAINER_COLLECTION_ROOT)/tests/e2e/tmpdata/conversion/ssh.key \
			-e @$(CONTAINER_COLLECTION_ROOT)/tests/auth_tenant.yml \
			-e @$(CONTAINER_COLLECTION_ROOT)/tests/e2e/tasks/tenant/scenario_variables.yml \
			$(OS_MIGRATE_E2E_TEST_ARGS) test_as_tenant.yml'

# --- Docs Targets ---

docs: docs-diagrams
	@echo "--- Generate documentation ---"
	@$(CONTAINER_ENGINE) exec -w $(CONTAINER_COLLECTION_ROOT) $(CONTAINER_NAME) bash -c '\
		dnf -y install git-core && \
		source $(VENV_DIR)/bin/activate && \
		pip install --root-user-action ignore -r requirements-docs.txt && \
		./scripts/docs-build.sh'

docs-diagrams: install
	@echo "--- Generate diagrams ---"
	@$(CONTAINER_ENGINE) exec -w $(CONTAINER_COLLECTION_ROOT) $(CONTAINER_NAME) bash -c '\
		dnf config-manager --set-enabled crb && \
		dnf install -y epel-release && \
		dnf install -y plantuml graphviz && \
		plantuml -progress -SDpi=150 -output render ./docs/src/images/plantuml/*.plantuml && \
		echo'
