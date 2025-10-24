#!/usr/bin/env python3
"""Test script to verify AudioChimp installation and basic functionality."""

import asyncio
import sys
import os
from pathlib import Path

# Add current directory to Python path
sys.path.insert(0, str(Path(__file__).parent))

async def test_imports():
    """Test that all required modules can be imported."""
    print("Testing imports...")

    try:
        from auditchimp.config import config
        print("✓ Configuration module imported successfully")

        from auditchimp.models import TranscriptionRequest, ProcessingStatus, init_database
        print("✓ Database models imported successfully")

        from auditchimp.diarization import DiarizationEngine
        print("✓ Diarization module imported successfully")

        from auditchimp.transcription import TranscriptionEngine
        print("✓ Transcription module imported successfully")

        from auditchimp.processor import AudioProcessor
        print("✓ Processor module imported successfully")

        from auditchimp.api import app
        print("✓ API module imported successfully")

        return True
    except ImportError as e:
        print(f"✗ Import error: {e}")
        return False
    except Exception as e:
        print(f"✗ Unexpected error: {e}")
        return False


async def test_configuration():
    """Test configuration loading."""
    print("\nTesting configuration...")

    try:
        from auditchimp.config import config

        print(f"✓ Whisper model: {config.WHISPER_MODEL}")
        print(f"✓ Quantization: {config.QUANTIZATION}")
        print(f"✓ Device: {config.WHISPER_DEVICE}")
        print(f"✓ API port: {config.API_PORT}")

        return True
    except Exception as e:
        print(f"✗ Configuration error: {e}")
        return False


async def test_database():
    """Test database initialization."""
    print("\nTesting database...")

    try:
        from auditchimp.models import init_database
        from auditchimp.config import config

        # Initialize database
        SessionLocal = init_database(config.DATABASE_URL)
        session = SessionLocal()

        # Test basic query
        from auditchimp.models import TranscriptionRequest
        count = session.query(TranscriptionRequest).count()

        session.close()
        print("✓ Database initialized successfully")
        print(f"✓ Current request count: {count}")

        return True
    except Exception as e:
        print(f"✗ Database error: {e}")
        return False


async def test_hardware_detection():
    """Test hardware detection."""
    print("\nTesting hardware detection...")

    try:
        import torch
        print(f"✓ PyTorch version: {torch.__version__}")
        print(f"✓ CUDA available: {torch.cuda.is_available()}")

        if torch.cuda.is_available():
            print(f"✓ GPU device: {torch.cuda.get_device_name(0)}")
            print(f"✓ GPU memory: {torch.cuda.get_device_properties(0).total_memory / 1024**3:.1f} GB")
        else:
            print("✓ Running on CPU")

        return True
    except Exception as e:
        print(f"✗ Hardware detection error: {e}")
        return False


async def main():
    """Run all tests."""
    print("AudioChimp Installation Test")
    print("=" * 40)

    tests = [
        test_imports,
        test_configuration,
        test_database,
        test_hardware_detection
    ]

    passed = 0
    total = len(tests)

    for test in tests:
        if await test():
            passed += 1

    print("\n" + "=" * 40)
    print(f"Test Results: {passed}/{total} passed")

    if passed == total:
        print("✓ All tests passed! Installation is successful.")
        print("\nNext steps:")
        print("1. Run 'python -m auditchimp.main' to start the API")
        print("2. Visit http://localhost:8000/docs for API documentation")
        print("3. Submit audio files via POST /submit endpoint")
        return 0
    else:
        print("✗ Some tests failed. Please check the errors above.")
        print("\nTroubleshooting:")
        print("1. Install missing dependencies: pip install -r requirements.txt")
        print("2. Check your Python version (requires 3.9+)")
        print("3. For GPU support, ensure CUDA is properly installed")
        return 1


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
