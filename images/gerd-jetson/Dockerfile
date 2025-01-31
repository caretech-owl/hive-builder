# Use the pytorch image from the Docker Hub
FROM dustynv/l4t-pytorch:r36.4.0

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

ENV GERD_VERSION="v0.6.1"
ENV PATH="/workspace/.local/bin:$PATH"
# To make gradio accessible from the outside
ENV GRADIO_SERVER_NAME="0.0.0.0"
# Mount volume/host directory to this path for persistent storage
ENV HF_HOME="/workspace/hf"
# gerd configuration overrides to potential persistent LoRAs
ENV gerd_lora_output_dir="/workspace/loras"

ADD --chown=user:user https://github.com/caretech-owl/gerd.git#${GERD_VERSION} gerd
RUN mkdir hf && \
    mkdir loras && \
    cd gerd && \
    pip install -e .

WORKDIR /workspace/gerd
ENTRYPOINT ["python3", "-m"]
CMD ["gerd.frontends.router"]

