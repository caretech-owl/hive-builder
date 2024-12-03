#!/bin/sh

if [ -z "${DOCKER_SOCKET}" ]; then
    echo "DOCKER_SOCKET is not set"
    exit 1
fi


set -e
DOCKER_GID=$(stat -c '%g' ${DOCKER_SOCKET})
DOCKER_GROUP=$(getent group ${DOCKER_GID} | awk -F ":" '{ print $1 }')
echo "DOCKER_GID=${DOCKER_GID}"
if [ $DOCKER_GROUP ]
then
    echo "Adding user to group ${DOCKER_GROUP}"
else
    echo "Creating group _docker with GID ${DOCKER_GID}"
    DOCKER_GROUP=_docker
    addgroup -S -g ${DOCKER_GID} $DOCKER_GROUP
fi


# Create a non-root user:
addgroup user $DOCKER_GROUP

# exec runuser -u $RUNUSER -- /bin/sh
exec runuser -u user -- $@
