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
ADD --chown=user:user https://github.com/caretech-owl/gerd.git gerd
RUN mkdir hf && \
    cd gerd && \
    pip install -e . 

ENV PATH="/workspace/.local/bin:$PATH"
# To make gradio accessible from the outside
ENV GRADIO_SERVER_NAME="0.0.0.0"

WORKDIR /workspace/gerd
CMD ["gradio", "gerd/frontends/qa_frontend.py"]
