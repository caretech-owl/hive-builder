FROM docker:dind

ENV PIP_NO_CACHE_DIR=1 \
  PIP_DISABLE_PIP_VERSION_CHECK=1 \
  PIP_DEFAULT_TIMEOUT=100

# Installing system deps:
RUN apk update && apk upgrade \
  && apk add --no-cache \
       # Installing Python:
       python3 python3-dev py3-pip \
       # Installing runuser and jq:
       runuser jq
    #    # Installing build deps:
    #    libffi-dev openssl-dev build-base git curl bash \
    #    # Installing Rust (latest cryptography requires it):
    #    cargo gcc musl-dev

RUN adduser --disabled-password --home /workspace --uid 1000 --shell /bin/sh user

USER user
WORKDIR /workspace

ENV CLI_VERSION="v0.6.6"
# ENV CLI_BRANCH="main"
ENV PATH="/workspace/.local/bin:$PATH"
ENV HIVE_HOME="/workspace/hive"
ENV HIVE_HOST="0.0.0.0"
ENV UV_CACHE_DIR="/workspace/uv"
ENV DOCKER_SOCKET=/var/run/docker.sock
ENV RUNUSER=user

# check whether something changed in the git repo
# https://stackoverflow.com/a/39278224
# ADD https://api.github.com/repos/caretech-owl/hive-cli/git/refs/heads/$CLI_BRANCH version.json
ADD https://api.github.com/repos/caretech-owl/hive-cli/git/refs/tags/${CLI_VERSION} version.json
RUN wget -qO- https://astral.sh/uv/install.sh | sh \
    && git clone --branch ${CLI_VERSION} https://github.com/caretech-owl/hive-cli.git \
    && mkdir $HIVE_HOME \
    && cd hive-cli \
    && uv sync --no-dev

USER root
WORKDIR /workspace/hive-cli
COPY images/hive-cli/entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

ENTRYPOINT ["/entrypoint.sh", "uv", "run", "--no-dev", "poe"]
CMD ["prod"]
