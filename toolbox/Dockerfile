FROM quay.io/fedora/fedora:34-x86_64
RUN dnf install -y glibc-langpack-en
ARG NO_VAGRANT=0
ENV LANG en_US.UTF-8
ENV LANGUAGE en_US:en
ENV LC_ALL en_US.UTF-8
ADD build /build
RUN bash /build/build.sh
WORKDIR /root/os_migrate
