FROM ubuntu:22.04

RUN sed -i 's@archive.ubuntu.com@ftp.yz.yamagata-u.ac.jp/pub/Linux@g' /etc/apt/sources.list

RUN perl -p -i.bak -e 's%(deb(?:-src|)\s+)https?://(?!archive\.canonical\.com|security\.ubuntu\.com)[^\s]+%$1http://linux.yz.yamagata-u.ac.jp/pub/linux/ubuntu/archives/%' /etc/apt/sources.list

LABEL maintainer="yabashikazuya"

SHELL ["/bin/bash", "-c"]

ENV DEBIAN_FRONTEND noninteractive

RUN apt-get update && apt-get install -y \
    sudo \
    wget \
    nano

RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        git \
        python3-pip \
        python3-dev \
        build-essential \
        pkg-config \
        libssl-dev \
        language-pack-ja-base \
        language-pack-ja \
        libjpeg8-dev && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

ENV LANG=ja_JP.UTF-8

RUN echo "PYTHONIOENCODING=utf-8" >> /etc/bash.bashrc && \
    echo "export PS1='\[\033[01;32m\]socket@\h\[\033[00m\]:\[\033[01;34m\]\w\[\033[00m\]\$ '" >> /etc/bash.bashrc

RUN pip3 install \
        setuptools \
        Cython \
        wheel --verbose

# socket通信用
RUN pip3 install \
    websockets \
    mediapipe

# 

# userの設定
ARG username=socket
ARG wkdir=/home/${username}/

ARG UID=1000
ARG GID=1000
RUN groupadd -g $GID $username && \
    useradd -m -s /bin/bash -u $UID -g $GID -G sudo $username && \
    echo $username:$username | chpasswd && \
    echo "$username   ALL=(ALL) NOPASSWD:ALL" >> /etc/sudoers

# workdirの権限をルートからユーザーに変更
RUN chown ${username}:${username} ${wkdir}
# ユーザー
USER ${username}

WORKDIR ${wkdir}
