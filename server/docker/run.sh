#!/bin/bash

USER_ID=$(id -u)
XSOCK="/tmp/.X11-unix"
XAUTH="/tmp/.docker.xauth"

HOST_WS=$(dirname $(dirname $(readlink -f $0)))/shared_dir

DOCKER_VOLUME="-v ${XSOCK}:${XSOCK}:rw"
DOCKER_VOLUME="${DOCKER_VOLUME} -v ${XAUTH}:${XAUTH}:rw"
DOCKER_VOLUME="${DOCKER_VOLUME} -v ${HOST_WS}:/home/socket:rw"

DOCKER_ENV="-e XAUTHORITY=${XAUTH}"
DOCKER_ENV="${DOCKER_ENV} -e DISPLAY=$DISPLAY"
DOCKER_ENV="${DOCKER_ENV} -e QT_X11_NO_MITSHM=1"
DOCKER_ENV="${DOCKER_ENV} -e USER_ID=${USER_ID}"
DOCKER_ENV="${DOCKER_ENV} -e HOME=/home/socket"
IMAGE_NAME="ubuntu:3.10-socket"

DOCKER_IMAGE="${IMAGE_NAME}"


docker run \
  --rm -it \
  --gpus all \
  --privileged \
  --name ubuntu \
  --net "host" \
  --shm-size 10gb \
  --user root \
  ${DOCKER_ENV} \
  ${DOCKER_VOLUME} \
  ${DOCKER_IMAGE} \
  bash