# Use the pytorch image from the Docker Hub
FROM dustynv/l4t-pytorch:r36.4.0
#FROM nvcr.io/nvidia/l4t-cuda:12.2.2-devel-arm64-ubuntu22.04

RUN groupadd -r -g 1000 user && \
    useradd \
    --create-home \
    --home-dir /workspace \
    --no-user-group \
    --uid 1000 \
    --gid 1000 \
    --shell /bin/bash \
    user

#RUN apt update && apt install python3 python3-pip git ninja-build -y
USER user
WORKDIR /workspace

# Copy the project code into the container
RUN git clone https://github.com/caretech-owl/gerd.git gerd
ENV CUDACXX=/usr/local/cuda-12.2/bin/nvcc
ENV CMAKE_ARGS="-DGGML_CUDA=on"
ENV FORCE_CMAKE=1
ENV PATH="$PATH:/workspace/.local/bin"

# Cache for model files
ENV HF_HOME="/workspace/models/"
RUN mkdir /workspace/models     

WORKDIR /workspace/gerd
# Install the dependencies
RUN sed -i 's/llama-cpp-python>=0.3.2/llama-cpp-python==0.3.1/g' pyproject.toml
RUN sed -i 's/torch>=2.5.1/torch>=2.5.0/g' pyproject.toml
RUN pip install --no-cache-dir -e .

# RUN pip install llama-cpp-python==0.3.1 --force-reinstall --upgrade --no-cache-dir --verbose

EXPOSE 7860
ENV GRADIO_SERVER_NAME="0.0.0.0"

# Correct permission
USER root
RUN chown -R user /workspace 
USER user

# Command to run the application
CMD ["gradio", "gerd/frontends/qa_frontend.py"]
