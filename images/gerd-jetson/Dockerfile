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

ENV GERD_VERSION="v0.7.5"
ENV PATH="/workspace/.local/bin:$PATH"
# To make gradio accessible from the outside
ENV GRADIO_SERVER_NAME="0.0.0.0"
# Mount volume/host directory to this path for persistent storage
ENV HF_HOME="/workspace/hf"
# must point to a potential lora, not the parent directory of all loras
ENV gerd_lora_output_dir="/workspace/loras/lora"
# torch 2.5.0 in l4t-pytorch sets learning rate to 0.0 with cuda
ENV PIP_INDEX_URL="http://jetson.webredirect.org/jp6/cu128"

ADD --chown=user:user https://github.com/caretech-owl/gerd.git#${GERD_VERSION} gerd
RUN mkdir hf && \
    mkdir loras && \
    cd gerd && \
    pip install torch==2.6.0 torchvision==0.21.0 torchaudio==2.6.0 && \
    pip install -e .[bitsandbytes]

WORKDIR /workspace/gerd
ENTRYPOINT ["python3", "-m"]
CMD ["gerd.frontends.router"]
