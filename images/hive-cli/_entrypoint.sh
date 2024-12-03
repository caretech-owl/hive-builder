# OTHER VERSION WHICH MIGHT BE USEFUL
# WHEN DATA HAS TO BE WRITTEN TO THE HOST

#!/bin/sh

if [ -z "$UID" ]; then
    echo "UID is not set"
    exit 1
fi
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
adduser --disabled-password --home /workspace --uid $UID --ingroup $DOCKER_GROUP --shell /bin/sh $RUNUSER
addgroup $RUNUSER $DOCKER_GROUP

chown -R $RUNUSER:$DOCKER_GROUP /root
chown -R $RUNUSER:$DOCKER_GROUP /workspace
# exec runuser -u $RUNUSER -- /bin/sh
exec runuser -u $RUNUSER -- $@
