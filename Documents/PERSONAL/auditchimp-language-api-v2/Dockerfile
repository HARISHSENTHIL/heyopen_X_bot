FROM nvidia/cuda:12.9.1-cudnn-runtime-ubuntu22.04

WORKDIR /app

# Install Python and system dependencies
RUN apt-get update && apt-get install -y \
    python3.10 \
    python3-pip \
    python3.10-venv \
    gcc \
    g++ \
    ffmpeg \
    libavformat-dev \
    libavcodec-dev \
    libavdevice-dev \
    libavutil-dev \
    libavfilter-dev \
    libswscale-dev \
    libswresample-dev \
    libsndfile1-dev \
    portaudio19-dev \
    pkg-config \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Create symlinks for python/pip
RUN ln -s /usr/bin/python3.10 /usr/local/bin/python && \
    ln -s /usr/bin/pip3 /usr/local/bin/pip

# Install pip packages (adjust torch index URL to match CUDA 12.2)
COPY requirements.txt .
RUN pip install --upgrade pip
RUN pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu121
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY auditchimp/ ./auditchimp/

# Create necessary directories and set permissions
RUN mkdir -p /app/uploads /app/temp /app/models /app/logs && \
    useradd --create-home --shell /bin/bash app && \
    chown -R app:app /app

USER app

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=30s --start-period=30s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

ENV QUANTIZATION=true \
    WHISPER_MODEL=large-v3 \
    WHISPER_DEVICE=auto \
    WHISPER_COMPUTE_TYPE=int8_float16 \
    DIARIZATION_USE_GPU=true \
    API_HOST=0.0.0.0 \
    API_PORT=8000 \
    API_WORKERS=4

EXPOSE 8000
CMD ["python", "-m", "auditchimp.main"]
