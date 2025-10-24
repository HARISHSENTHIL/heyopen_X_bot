# AudioChimp Transcription API v2.0

A fast and accurate audio transcription and diarization API with GPU/CPU support, built with faster-whisper and optimized for performance.

## Features

- 🚀 **Fast Processing**: Uses faster-whisper for 10-40x faster transcription than standard implementations
- 🎯 **High Accuracy**: Supports multiple Whisper models with quantization for optimal speed/accuracy balance
- 🔊 **Speaker Diarization**: Automatic speaker detection using NeMo (GPU) or PyAnnote (CPU)
- 📊 **Real-time Progress**: Live progress tracking with percentage updates
- 🔧 **Flexible Modes**: Choose between accurate (chunked) or fast (full) transcription modes
- 📈 **System Monitoring**: Built-in metrics and health monitoring
- 🗄️ **Queue Management**: SQLite-based request queuing with background processing
- ⚙️ **Easy Configuration**: Environment-based configuration with sensible defaults
- 🔐 **File Integrity**: SHA-256 file hashing for verification and deduplication
- 📋 **Request Management**: Cancel queued requests and comprehensive request tracking
- 🏗️ **Production Architecture**: Complete separation between API and job processing threads
- 🔄 **Concurrent Processing**: Multiple audio files processed simultaneously
- 🐳 **Docker Support**: GPU-accelerated containers with CUDA 12.x support

## Hardware Requirements

### Minimum Requirements
- Python 3.9-3.10 (Python 3.11+ not supported due to dependency constraints)
- 8GB RAM
- 4-core CPU
- 10GB storage

### Recommended Setup (with GPU)
- Python 3.9+
- 16GB RAM
- NVIDIA GPU with 8GB+ VRAM (L40S, RTX 40-series, or similar)
- 50GB storage for models

## Quick Start

### 1. Installation

#### Option A: Docker (Recommended)

```bash
# Clone the repository
git clone <repository-url>
cd auditchimp-language-api-v2

# Run with Docker Compose
docker-compose up --build

# Or build and run manually
docker build -t auditchimp-api .
docker run -p 8000:8000 auditchimp-api
```

#### Option C: Quick Start Script (Cross-platform)

```bash
# Clone the repository
git clone <repository-url>
cd auditchimp-language-api-v2

# Run the startup script (works on Linux/Mac/Windows)
./start.sh docker    # Start with Docker
./start.sh local     # Start locally
./start.sh help      # Show help
```

#### Option B: Local Installation

```bash
# Clone the repository
git clone <repository-url>
cd auditchimp-language-api-v2

# Install with Poetry (recommended)
pip install poetry
poetry install

# Or install with pip (legacy)
pip install -r requirements.txt
```

### 2. Configuration

Copy the environment file and modify as needed:

```bash
cp .env .env.local  # Optional: create local override
```

#### Complete Environment Configuration

```bash
# =============================================================================
# AUDIO PROCESSING CONFIGURATION
# =============================================================================

# Quantization Settings
QUANTIZATION=true                    # Enable INT8 quantization for faster processing
WHISPER_MODEL=large-v2              # Whisper model size (tiny, base, small, medium, large-v2)
WHISPER_DEVICE=auto                 # Device: auto (detect GPU), cuda, cpu
WHISPER_COMPUTE_TYPE=int8_float16   # Compute type: int8, int8_float16, float16

# Diarization Settings (Auto-detected)
DIARIZATION_MODEL=pyannote/speaker-diarization-3.1  # PyAnnote model (CPU fallback)
NEMO_MODEL=nvidia/speakerverification_en_titanet_large  # NeMo model (GPU when available)

# =============================================================================
# API CONFIGURATION
# =============================================================================

# Server Settings
API_HOST=0.0.0.0                    # Bind address (0.0.0.0 for all interfaces)
API_PORT=8000                       # Port number
API_WORKERS=4                       # Number of uvicorn workers

# =============================================================================
# DATABASE CONFIGURATION
# =============================================================================

DATABASE_URL=sqlite:///./auditchimp.db  # Database connection string

# =============================================================================
# PROCESSING CONFIGURATION
# =============================================================================

# File Handling
MAX_FILE_SIZE=100000000             # Maximum file size (100MB)
SUPPORTED_FORMATS=mp3,wav,flac,m4a,ogg,webm  # Supported audio formats
CHUNK_SIZE=30                       # Audio chunk size in seconds for processing
MAX_CONCURRENT_JOBS=3               # Maximum concurrent processing jobs

# =============================================================================
# MODEL CACHE CONFIGURATION
# =============================================================================

MODEL_CACHE_DIR=./models            # Directory for model storage
MAX_CACHE_SIZE=10GB                 # Maximum cache size

# =============================================================================
# HUGGING FACE CONFIGURATION (Windows Compatibility)
# =============================================================================

HF_HOME=./models                    # Hugging Face cache directory
HF_HUB_DISABLE_SYMLINKS_WARNING=1   # Disable symlink warnings
HF_HUB_ENABLE_HF_TRANSFER=0         # Use standard downloads

# =============================================================================
# LOGGING CONFIGURATION
# =============================================================================

LOG_LEVEL=INFO                      # Logging level (DEBUG, INFO, WARNING, ERROR)
LOG_FILE=./logs/auditchimp.log      # Log file path
```

#### Configuration Explanations

**Audio Processing:**
- `QUANTIZATION`: Enable INT8 quantization for 2-3x faster processing with minimal accuracy loss
- `WHISPER_MODEL`: Choose model size based on accuracy vs speed requirements
- `WHISPER_DEVICE`: Auto-detection recommended - automatically uses GPU when available
- `WHISPER_COMPUTE_TYPE`: Quantization level for GPU processing

**Diarization (Auto-Detected):**
- **GPU Available**: Automatically uses NeMo for GPU-accelerated diarization
- **CPU Only**: Falls back to PyAnnote for CPU-based diarization
- `DIARIZATION_MODEL`: PyAnnote model (used when GPU unavailable)
- `NEMO_MODEL`: NeMo model (used when GPU available)

**Performance Tuning:**
- `MAX_CONCURRENT_JOBS`: Number of simultaneous audio processing jobs
- `API_WORKERS`: Number of FastAPI server workers
- `CHUNK_SIZE`: Smaller chunks = more accurate but slower processing

### 3. Run the API

```bash
# Using Poetry
poetry run auditchimp-api

# Or using Python
python -m auditchimp.main

# Or using uvicorn directly
uvicorn auditchimp.api:app --host 0.0.0.0 --port 8000
```

The API will be available at `http://localhost:8000`

## Docker Deployment

### Prerequisites
- Docker 20.10+
- Docker Compose 2.0+ (for docker-compose.yml)
- NVIDIA Container Toolkit (for GPU support)
- NVIDIA GPU with CUDA 12.x support

### Quick Docker Deployment

```bash
# 1. Clone and navigate to the repository
git clone <repository-url>
cd auditchimp-language-api-v2

# 2. Start with Docker Compose (includes GPU support)
docker-compose up --build

# 3. Access the API
# - API: http://localhost:8000
# - Documentation: http://localhost:8000/docs
# - Health Check: http://localhost:8000/health
```

### Manual Docker Deployment

```bash
# Build the image
docker build -t auditchimp-api .

# Run with CPU only
docker run -p 8000:8000 auditchimp-api

# Run with GPU support (requires nvidia-docker)
docker run --gpus all -p 8000:8000 auditchimp-api

# Run with volume mounts for data persistence
docker run -p 8000:8000 \
  -v $(pwd)/uploads:/app/uploads \
  -v $(pwd)/models:/app/models \
  -v $(pwd)/logs:/app/logs \
  auditchimp-api
```

### Docker Configuration

#### Environment Variables
The Docker container supports all the same environment variables as the local installation:

```bash
# Performance settings
QUANTIZATION=true                    # Enable quantization for speed
WHISPER_MODEL=large-v2              # Model size
WHISPER_COMPUTE_TYPE=int8_float16   # Compute type for quantization

# Hardware settings
WHISPER_DEVICE=cuda                 # Use GPU (cuda) or CPU (cpu)
DIARIZATION_USE_GPU=true            # Use GPU for diarization

# API settings
API_HOST=0.0.0.0
API_PORT=8000
API_WORKERS=4
```

#### Volumes
- `/app/uploads` - Audio file uploads
- `/app/models` - Model cache directory
- `/app/logs` - Application logs
- `/app/auditchimp.db` - SQLite database

### GPU Support

For GPU acceleration, ensure you have:

1. **NVIDIA GPU** with sufficient VRAM (8GB+ recommended)
2. **NVIDIA Container Toolkit** installed
3. **CUDA drivers** compatible with your GPU (CUDA 12.x recommended)

```bash
# Test GPU availability
docker run --gpus all nvidia/cuda:11.8-devel-ubuntu20.04 nvidia-smi

# Run with GPU support
docker-compose up --build
```

### Production Deployment

For production deployment, consider:

1. **Reverse Proxy**: Use Nginx or Traefik as a reverse proxy
2. **SSL/TLS**: Enable HTTPS with Let's Encrypt
3. **Monitoring**: Add Prometheus and Grafana
4. **Logging**: Use centralized logging (ELK stack)
5. **Backup**: Regular backups of uploads and database

Example production docker-compose.yml:

```yaml
version: '3.8'

services:
  auditchimp-api:
    image: your-registry/auditchimp-api:latest
    deploy:
      replicas: 3
      resources:
        reservations:
          devices:
            - driver: nvidia
              count: 1
              capabilities: [gpu]
    environment:
      - QUANTIZATION=true
      - WHISPER_MODEL=large-v2
      - API_WORKERS=8
    volumes:
      - auditchimp_data:/app/data
      - auditchimp_models:/app/models

volumes:
  auditchimp_data:
  auditchimp_models:
```

## API Usage

### Submit Audio for Processing

```bash
curl -X POST "http://localhost:8000/submit" \
  -F "file=@audio_sample.mp3" \
  -F "accurate_mode=false"
```

**Note**: Quantization is now controlled by the `QUANTIZATION` environment variable and cannot be set per request.

Response:
```json
{
  "request_id": "123e4567-e89b-12d3-a456-426614174000",
  "file_hash": "a665a45920422f9d417e4867efdc4fb8a04a1f3fff1fa07e998e86f7f7a27ae3",
  "status": "queued",
  "message": "Audio file submitted successfully",
  "estimated_time": "2-5 minutes depending on file length and processing mode"
}
```

### Check Processing Status

```bash
curl "http://localhost:8000/status/123e4567-e89b-12d3-a456-426614174000"
```

Response:
```json
{
  "request_id": "123e4567-e89b-12d3-a456-426614174000",
  "status": "completed",
  "progress": 100.0,
  "filename": "audio_sample.mp3",
  "transcription_result": {
    "segments": [
      {
        "start": 0.0,
        "end": 3.5,
        "text": "Hello, this is a sample transcription.",
        "speaker": "SPEAKER_00",
        "confidence": 0.95
      }
    ],
    "mode": "fast",
    "total_segments": 1,
    "language": "en"
  },
  "diarization_result": {
    "segments": [
      {
        "start": 0.0,
        "end": 3.5,
        "speaker": "SPEAKER_00"
      }
    ],
    "method": "pyannote",
    "device": "cpu"
  }
}
```

### Get System Metrics

```bash
curl "http://localhost:8000/metrics"
```

Response:
```json
{
  "system": {
    "cpu_usage": 15.2,
    "memory_usage": 45.8,
    "gpu_usage": 23.1,
    "timestamp": "2025-01-21T12:00:00"
  },
  "queue": {
    "queued": 2,
    "processing": 1,
    "completed_today": 15,
    "failed_today": 0
  },
  "performance": {
    "total_processed_today": 15,
    "success_rate": 100.0,
    "estimated_wait_time": "6 minutes"
  },
  "configuration": {
    "whisper_model": "large-v2",
    "quantization": true,
    "diarization_gpu": true,
    "max_concurrent_jobs": 3
  }
}
```

### Health Check with GPU Information

```bash
curl "http://localhost:8000/health"
```

Response:
```json
{
  "status": "healthy",
  "issues": [],
  "database": "healthy",
  "processor": "running",
  "models": "loaded",
  "gpu": {
    "available": true,
    "name": "NVIDIA L40S",
    "memory": "44.4 GB"
  },
  "timestamp": "2025-01-21T12:00:00"
}
```

### Cancel a Queued Request

```bash
curl -X PATCH "http://localhost:8000/request/123e4567-e89b-12d3-a456-426614174000/cancel"
```

Response:
```json
{
  "message": "Request canceled successfully",
  "request_id": "123e4567-e89b-12d3-a456-426614174000",
  "status": "canceled"
}
```

**Note**: Only queued requests can be canceled. Processing requests cannot be canceled.

## File Hashing and Integrity

### Overview
All uploaded audio files are automatically assigned a SHA-256 hash for integrity verification and deduplication purposes. This ensures:

- **File Integrity**: Verify that files haven't been corrupted during upload
- **Deduplication**: Prevent processing the same file multiple times
- **Traceability**: Track files through the processing pipeline
- **Security**: Cryptographic verification of file contents

### Hash Generation
- **Algorithm**: SHA-256 (industry standard)
- **Timing**: Generated during file upload before processing
- **Storage**: Stored in database and returned in API responses
- **Uniqueness**: Each unique file will have a unique hash

### Usage in API Responses
File hashes are included in:
- **Submit Response**: `file_hash` field in successful upload response
- **Status Response**: `file_hash` field in all status queries
- **Database**: Stored permanently with each request record

### Example Workflow
```bash
# 1. Submit file
curl -X POST "http://localhost:8000/submit" -F "file=@audio.mp3"

# Response includes hash
{
  "request_id": "123e4567-e89b-12d3-a456-426614174000",
  "file_hash": "a665a45920422f9d417e4867efdc4fb8a04a1f3fff1fa07e998e86f7f7a27ae3",
  "status": "queued",
  "message": "Audio file submitted successfully"
}

# 2. Check status (hash included)
curl "http://localhost:8000/status/123e4567-e89b-12d3-a456-426614174000"

# Response includes hash
{
  "request_id": "123e4567-e89b-12d3-a456-426614174000",
  "file_hash": "a665a45920422f9d417e4867efdc4fb8a04a1f3fff1fa07e998e86f7f7a27ae3",
  "status": "completed",
  "progress": 100.0,
  ...
}
```

### Benefits
1. **Data Integrity**: Ensures files aren't corrupted during upload/processing
2. **Deduplication**: Prevents duplicate processing of identical files
3. **Audit Trail**: Complete traceability of file processing
4. **Security**: Cryptographic verification of file contents
5. **Debugging**: Easier troubleshooting with file identification

## API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/submit` | POST | Submit audio file for processing |
| `/status/{request_id}` | GET | Get processing status |
| `/queue` | GET | Get queue status and system metrics |
| `/metrics` | GET | Get detailed system metrics |
| `/health` | GET | Health check with GPU information |
| `/request/{request_id}/cancel` | PATCH | Cancel a queued request |
| `/request/{request_id}` | DELETE | Delete any request and associated files |
| `/docs` | GET | Interactive API documentation |
| `/redoc` | GET | Alternative API documentation |

## Processing Modes

### Accurate Mode (`accurate_mode=true`)
- Splits audio by diarization segments
- Transcribes each segment separately with Whisper
- Higher accuracy but slower processing
- Better for complex multi-speaker scenarios

### Fast Mode (`accurate_mode=false`) - Default
- Transcribes full audio with Whisper
- Maps diarization speakers to transcription segments
- Faster processing with good accuracy
- Suitable for most use cases

## Performance Tuning

### For Maximum Speed
```bash
QUANTIZATION=true
WHISPER_MODEL=small
WHISPER_COMPUTE_TYPE=int8_float16
DIARIZATION_USE_GPU=true
MAX_CONCURRENT_JOBS=4
```

### For Maximum Accuracy
```bash
QUANTIZATION=false
WHISPER_MODEL=large-v2
WHISPER_COMPUTE_TYPE=float16
DIARIZATION_USE_GPU=true
MAX_CONCURRENT_JOBS=2
```

### CPU-Only Setup
```bash
WHISPER_DEVICE=cpu
DIARIZATION_USE_GPU=false
MAX_CONCURRENT_JOBS=2
```

## Model Information

### Whisper Models
- **tiny**: Fastest, least accurate (~85% WER)
- **base**: Good balance (~75% WER)
- **small**: Better accuracy (~65% WER)
- **medium**: High accuracy (~55% WER)
- **large-v2**: Best accuracy (~45% WER)

### Quantization Options
- **int8**: 2-3x faster, ~1-2% accuracy drop
- **int8_float16**: Best balance, 2.5x faster, minimal accuracy loss
- **float16**: 1.5-2x faster, no accuracy loss

## Troubleshooting

### Common Issues

1. **CUDA Out of Memory**
   ```bash
   # Reduce batch size and use smaller model
   WHISPER_MODEL=medium
   MAX_CONCURRENT_JOBS=1
   ```

2. **Model Download Issues**
   ```bash
   # Clear model cache and retry
   rm -rf ./models
   ```

3. **High CPU Usage**
   ```bash
   # Reduce concurrent jobs
   MAX_CONCURRENT_JOBS=2
   ```

4. **Windows Permission Issues (Symbolic Links)**
   ```bash
   # The application automatically handles Windows symlink issues
   # If you encounter permission errors during model download:
   # 1. Run as Administrator
   # 2. Or set HF_HUB_DISABLE_SYMLINKS_WARNING=1 in your environment
   # 3. Or use Docker which handles this automatically
   ```

### Windows Compatibility

The application includes several Windows-specific fixes:

#### Hugging Face Configuration
The application automatically sets these environment variables for Windows compatibility:
- `HF_HUB_DISABLE_SYMLINKS_WARNING=1` - Disables symlink warnings
- `HF_HUB_ENABLE_HF_TRANSFER=0` - Uses standard download method
- `HF_HOME=./models` - Sets model cache directory

#### Docker on Windows
For Windows users, Docker provides the best experience:
```bash
# Use Docker Compose (handles Windows compatibility automatically)
docker-compose up --build

# Or use the startup script
./start.sh docker
```

### Logs
Check logs at `./logs/auditchimp.log` for detailed error information.

## Development

### Running Tests
```bash
poetry run pytest
```

### Code Formatting
```bash
poetry run black auditchimp/
poetry run isort auditchimp/
```

## Architecture

The AudioChimp API v2.0 features a production-ready architecture with complete separation between the API layer and job processing:

### System Architecture

```
┌─────────────────┐    ┌──────────────────────┐
│   FastAPI       │    │   Job Processor      │
│   Server        │    │   (Separate Thread)  │
│                 │    │                      │
│ • HTTP Requests │    │ • Polls DB for jobs  │
│ • Instant       │    │ • Processes audio    │
│ • Status/Cancel │    │ • Updates progress   │
│ • Metrics       │    │ • Thread pool        │
└─────────────────┘    └──────────────────────┘
         │                        │
         └─────── Shared DB ───────┘
```

### Key Components

**API Thread (Always Responsive):**
- Handles all HTTP requests instantly
- Never blocks on processing operations
- Provides real-time status updates
- Supports request cancellation
- Returns system metrics and health checks

**Job Processor Thread (Independent):**
- Polls database for queued jobs every 2 seconds
- Processes up to `MAX_CONCURRENT_JOBS` simultaneously
- Uses ThreadPoolExecutor for concurrent processing
- Handles both sync and async operations properly
- Automatic error recovery and retry logic

**Database Layer:**
- SQLite database for request metadata
- Thread-safe operations with proper locking
- Stores transcription and diarization results
- Tracks processing status and progress

**Hardware Detection:**
- Automatic CUDA detection for GPU acceleration
- Falls back to CPU processing when GPU unavailable
- Smart diarization engine selection (NeMo GPU / PyAnnote CPU)
- Optimized model loading based on available hardware

### Processing Flow

1. **Request Submission** → File uploaded, hash generated, queued in DB
2. **Job Discovery** → Job processor polls DB for queued requests
3. **Processing Start** → Request marked as processing, job submitted to thread pool
4. **Audio Processing** → Diarization → Transcription (concurrent when possible)
5. **Progress Updates** → Real-time progress via async callbacks
6. **Completion** → Results stored, status updated, cleanup performed

### Benefits

- **High Availability**: API always responsive, even during heavy processing
- **Scalability**: Configurable concurrent job limits
- **Reliability**: Proper error handling and recovery
- **Performance**: Optimal hardware utilization (GPU when available)
- **Monitoring**: Real-time metrics and health checks
- **Production Ready**: Enterprise-grade architecture

## License

MIT License - see LICENSE file for details.

## Support

For issues and questions, please create an issue in the repository or contact the development team.
