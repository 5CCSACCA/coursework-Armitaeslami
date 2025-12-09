FROM python:3.11-slim-bookworm

WORKDIR /app

# Install system dependencies for BitNet.cpp
RUN apt-get update && apt-get install -y \
    build-essential \
    cmake \
    git \
    wget \
    curl \
    gnupg \
    lsb-release \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# Install LLVM/Clang 18
RUN wget -O - https://apt.llvm.org/llvm-snapshot.gpg.key | apt-key add - && \
    echo "deb http://apt.llvm.org/bookworm/ llvm-toolchain-bookworm-18 main" > /etc/apt/sources.list.d/llvm.list && \
    apt-get update && \
    apt-get install -y clang-18 && \
    rm -rf /var/lib/apt/lists/*

# Create symlinks for clang
RUN ln -sf /usr/bin/clang-18 /usr/bin/clang && \
    ln -sf /usr/bin/clang++-18 /usr/bin/clang++

# Set clang as default compiler
ENV CC=clang
ENV CXX=clang++

# Upgrade pip
RUN pip install --no-cache-dir --upgrade pip

# Install Python dependencies
RUN pip install --no-cache-dir \
    fastapi==0.109.0 \
    uvicorn==0.27.0 \
    pydantic==2.5.3 \
    prometheus-client==0.19.0

# Clone BitNet repository
RUN git clone --recursive https://github.com/microsoft/BitNet.git /app/BitNet

WORKDIR /app/BitNet

# Install BitNet.cpp Python requirements
RUN pip install --no-cache-dir -r requirements.txt

# Download the BitNet model (2-3GB download)
RUN huggingface-cli download microsoft/BitNet-b1.58-2B-4T-gguf \
    --local-dir models/BitNet-b1.58-2B-4T

# Build and quantize the model
RUN python setup_env.py -md models/BitNet-b1.58-2B-4T -q i2_s

# Set environment variables
ENV BITNET_PATH=/app/BitNet
ENV BITNET_MODEL_PATH=/app/BitNet/models/BitNet-b1.58-2B-4T/ggml-model-i2_s.gguf

# Copy application code
COPY app/ /app/service/

WORKDIR /app/service

# Expose port
EXPOSE 8002

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD curl -f http://localhost:8002/health || exit 1

# Run the service
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8002"]