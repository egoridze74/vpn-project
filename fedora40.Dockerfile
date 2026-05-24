FROM fedora:40

RUN dnf update -y && \
    dnf install -y \
    python3 \
    python3-pip \
    bash \
    sqlite \
    python3-devel \
    gcc \
    git \
    vim \
    sudo && \
    dnf clean all

RUN pip3 install --no-cache-dir flask pyyaml

RUN useradd -m -u 1000 -s /bin/bash dev && \
    echo "dev ALL=(ALL) NOPASSWD:ALL" >> /etc/sudoers.d/dev

USER dev

WORKDIR /workspace

CMD ["/bin/bash"]