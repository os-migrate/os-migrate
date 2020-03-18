FROM docker.io/library/fedora:31
RUN yum install -y glibc-langpack-en
ENV LANG en_US.UTF-8
ENV LANGUAGE en_US:en
ENV LC_ALL en_US.UTF-8
ADD build /build
RUN bash /build/build.sh
WORKDIR /root/os_migrate
