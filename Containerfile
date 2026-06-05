ARG PYTHON_VERSION=3.12
ARG BASE_IMAGE=quay.io/centos/centos:stream10

FROM $BASE_IMAGE

ARG PYTHON_VERSION

LABEL maintainer="os-migrate team" \
      description="OpenStack tenant migration tooling"

RUN dnf upgrade --refresh -y --skip-broken --nobest && \
    dnf install -y \
        epel-release \
        openssh-clients \
        sshpass \
        python${PYTHON_VERSION} \
        python${PYTHON_VERSION}-devel \
        python${PYTHON_VERSION}-pip \
        python3-dnf \
        rsync \
        gcc \
        git-core \
        rhel-system-roles \
        util-linux \
        && dnf clean all

WORKDIR /code

COPY requirements.txt requirements-tests.txt ./

RUN python${PYTHON_VERSION} -m venv /code/.venv && \
    . /code/.venv/bin/activate && \
    pip install --root-user-action ignore --upgrade pip && \
    pip install --root-user-action ignore -r requirements.txt && \
    pip install --root-user-action ignore -r requirements-tests.txt

COPY . .

RUN git clone --depth 1 --branch 2.5.0 \
        https://github.com/openstack/ansible-collections-openstack.git \
        /code/plugins/modules/_vendor/openstack.cloud && \
    for mod in auth compute_flavor compute_flavor_info floating_ip identity_domain identity_role \
        identity_user identity_user_info image image_info keypair network networks_info port project \
        project_info role_assignment router security_group security_group_rule server \
        server_action server_info server_volume subnet subnets_info volume volume_info; do \
        ln -sf /code/plugins/modules/_vendor/openstack.cloud/plugins/modules/$mod.py \
            /code/plugins/modules/$mod.py; \
    done && \
    for util in openstack ironic; do \
        ln -sf /code/plugins/modules/_vendor/openstack.cloud/plugins/module_utils/$util.py \
            /code/plugins/module_utils/$util.py; \
    done

RUN . /code/.venv/bin/activate && \
    pip install ansible-core && \
    ansible-galaxy collection build && \
    ansible-galaxy collection install openstack.cloud community.general && \
    ansible-galaxy collection install os_migrate-os_migrate-*.tar.gz --force-with-deps

ENV PATH="/code/.venv/bin:${PATH}"

CMD ["bash"]
