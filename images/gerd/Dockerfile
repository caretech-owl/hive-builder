FROM python:3.12

RUN groupadd -r -g 1000 user && \
    useradd \
    --create-home \
    --home-dir /workspace \
    --no-user-group \
    --uid 1000 \
    --gid 1000 \
    --shell /bin/bash \
    user

USER user
WORKDIR /workspace

ENV GERD_VERSION="v0.7.7"
ENV PATH="/workspace/.local/bin:$PATH"
# To make gradio accessible from the outside
ENV GRADIO_SERVER_NAME="0.0.0.0"
# Mount volume/host directory to this path for persistent storage
ENV HF_HOME="/workspace/hf"
# must point to a potential lora, not the parent directory of all loras
ENV gerd_lora_output_dir="/workspace/loras/lora"

ADD --chown=user:user https://github.com/caretech-owl/gerd.git#${GERD_VERSION} gerd
RUN mkdir hf && \
    mkdir loras && \
    cd gerd && \
    pip install -e .

WORKDIR /workspace/gerd
ENTRYPOINT ["python", "-m"]
CMD ["gerd.frontends.router"]
