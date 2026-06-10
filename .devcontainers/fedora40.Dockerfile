FROM fedora:40

RUN dnf -y update && \
    dnf -y install python3 python3-pip sqlite bash ncurses iproute procps-ng iptables iputils && \
    dnf clean all

RUN pip3 install --no-cache-dir flask pyyaml python-pytun

# Root пользователь для TUN создания
USER root
WORKDIR /workspaces/project