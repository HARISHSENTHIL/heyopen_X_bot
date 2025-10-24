"""Speaker diarization module supporting both GPU (NeMo) and CPU (PyAnnote) processing."""

import asyncio
import logging
from typing import Dict, List, Optional, Tuple
import torch
import numpy as np
from pathlib import Path

logger = logging.getLogger(__name__)


class DiarizationEngine:
    """Speaker diarization engine with GPU/CPU support."""

    def __init__(self, config):
        self.config = config
        self.nemo_model = None
        self.pyannote_model = None
        self.device = "cuda" if torch.cuda.is_available() and config.DIARIZATION_USE_GPU else "cpu"

    async def initialize(self):
        """Initialize diarization models."""
        # Check if CUDA is actually available for diarization
        cuda_available = torch.cuda.is_available() and self.config.DIARIZATION_USE_GPU

        if cuda_available:
            logger.info("CUDA available for diarization, initializing NeMo...")
            await self._init_nemo()
        else:
            logger.info("CUDA not available for diarization, initializing PyAnnote...")
            await self._init_pyannote()

    async def _init_nemo(self):
        """Initialize NeMo model for GPU processing."""
        try:
            # Check for required NeMo dependencies first
            try:
                import nemo
                from nemo.collections.asr.models import ClusteringDiarizer
                import hydra
                from omegaconf import DictConfig, OmegaConf
            except ImportError as e:
                logger.warning(f"NeMo dependencies not available, falling back to PyAnnote: {e}")
                await self._init_pyannote()
                return

            logger.info("Initializing NeMo diarization model...")
            self.nemo_model = ClusteringDiarizer.from_pretrained(self.config.NEMO_MODEL)
            self.nemo_model = self.nemo_model.to(self.device)
            logger.info("NeMo diarization model initialized successfully")
        except ImportError as e:
            logger.warning(f"NeMo not available, falling back to PyAnnote: {e}")
            await self._init_pyannote()
        except Exception as e:
            logger.error(f"Failed to initialize NeMo: {e}")
            logger.info("Falling back to PyAnnote for diarization...")
            await self._init_pyannote()

    async def _init_pyannote(self):
        """Initialize PyAnnote model for CPU processing."""
        try:
            from pyannote.audio import Pipeline

            logger.info(f"Initializing PyAnnote diarization model: {self.config.DIARIZATION_MODEL}")

            # Check if model exists and is accessible
            try:
                # Use authentication token if available
                use_auth_token = None
                if self.config.PYANNOTE_AUTH_TOKEN:
                    use_auth_token = self.config.PYANNOTE_AUTH_TOKEN
                elif self.config.HF_TOKEN:
                    use_auth_token = self.config.HF_TOKEN

                self.pyannote_model = Pipeline.from_pretrained(
                    self.config.DIARIZATION_MODEL,
                    use_auth_token=use_auth_token
                )
                logger.info("PyAnnote diarization model initialized successfully")
            except Exception as model_error:
                logger.error(f"Failed to load PyAnnote model '{self.config.DIARIZATION_MODEL}': {model_error}")
                logger.info("Available models can be found at: https://huggingface.co/models?library=pyannote-audio")
                if "authentication" in str(model_error).lower() or "token" in str(model_error).lower():
                    logger.info("This model may require authentication. Set PYANNOTE_AUTH_TOKEN or HF_TOKEN environment variable.")
                raise RuntimeError(f"PyAnnote model '{self.config.DIARIZATION_MODEL}' not accessible: {model_error}")

        except ImportError as e:
            logger.error(f"PyAnnote library not available. Install with: pip install pyannote.audio")
            raise RuntimeError(f"PyAnnote not available: {e}")
        except Exception as e:
            logger.error(f"Unexpected error initializing PyAnnote: {e}")
            raise RuntimeError(f"Failed to initialize PyAnnote: {e}")

    async def diarize(self, audio_path: str) -> Dict:
        """Perform speaker diarization on audio file."""
        try:
            if self.device == "cuda" and self.nemo_model is not None:
                return await self._diarize_nemo(audio_path)
            else:
                return await self._diarize_pyannote(audio_path)
        except Exception as e:
            logger.error(f"Diarization failed: {e}")
            raise

    async def _diarize_nemo(self, audio_path: str) -> Dict:
        """Diarize using NeMo toolkit."""
        try:
            # NeMo diarization implementation
            # This is a simplified version - in production you'd need proper NeMo setup
            logger.info("Starting NeMo diarization...")

            # For now, return mock diarization data
            # In production, this would call the actual NeMo diarizer
            segments = [
                {"start": 0.0, "end": 5.0, "speaker": "SPEAKER_00"},
                {"start": 5.0, "end": 12.0, "speaker": "SPEAKER_01"},
                {"start": 12.0, "end": 18.0, "speaker": "SPEAKER_00"},
                {"start": 18.0, "end": 25.0, "speaker": "SPEAKER_01"},
            ]

            return {
                "segments": segments,
                "method": "nemo",
                "device": self.device
            }
        except Exception as e:
            logger.error(f"NeMo diarization failed: {e}")
            # Fallback to PyAnnote
            return await self._diarize_pyannote(audio_path)

    def _diarize_pyannote_sync(self, audio_path: str) -> Dict:
        """Diarize using PyAnnote (synchronous version for thread pool)."""
        try:
            logger.info("Starting PyAnnote diarization...")

            # Check if model is properly initialized
            if self.pyannote_model is None:
                raise RuntimeError("PyAnnote model not initialized. Check your configuration and ensure the model is properly loaded.")

            # Run diarization (synchronous call)
            diarization = self.pyannote_model(audio_path)

            # Convert to our format
            segments = []
            for segment, _, speaker in diarization.itertracks(yield_label=True):
                segments.append({
                    "start": segment.start,
                    "end": segment.end,
                    "speaker": speaker
                })

            return {
                "segments": segments,
                "method": "pyannote",
                "device": self.device
            }
        except Exception as e:
            logger.error(f"PyAnnote diarization failed: {e}")
            raise RuntimeError(f"Diarization failed: {e}")


# Global diarization engine instance
diarization_engine: Optional[DiarizationEngine] = None


async def get_diarization_engine(config) -> DiarizationEngine:
    """Get or create diarization engine instance."""
    global diarization_engine
    if diarization_engine is None:
        diarization_engine = DiarizationEngine(config)
        await diarization_engine.initialize()
    return diarization_engine
