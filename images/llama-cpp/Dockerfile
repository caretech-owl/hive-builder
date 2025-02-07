FROM ghcr.io/ggerganov/llama.cpp:full

RUN pip install gradio[oauth] gradio-huggingfacehub-search==0.0.12 && \
    groupadd -r -g 1000 user && \
    useradd \
    --create-home \
    --home-dir /workspace \
    --no-user-group \
    --uid 1000 \
    --gid 1000 \
    --shell /bin/bash \
    user

ENV GRADIO_SERVER_NAME="0.0.0.0"
ENV HF_HOME="/workspace/hf"

WORKDIR /workspace
COPY --chown=user:user images/llama-cpp/merger_gui.py /workspace/merger_gui.py
USER user
RUN mkdir -p /workspace/models && mkdir -p /workspace/loras && mkdir -p /workspace/hf

ENTRYPOINT ["gradio", "/workspace/merger_gui.py"]