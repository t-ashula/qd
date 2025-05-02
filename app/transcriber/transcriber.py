import os
import time
from typing import Any, Dict, List, Optional, Tuple

import torch
from transformers import AutoModelForSpeechSeq2Seq, AutoProcessor, pipeline
from transformers.pipelines.base import Pipeline

# Model name
WHISPER_MODEL_NAME = "kotoba-tech/kotoba-whisper-v2.2"
# Unload model after this many seconds of inactivity
MODEL_UNLOAD_TIMEOUT = 300  # 5 minutes


class TranscriberService:
    """
    Service for audio transcription using kotoba-whisper-v2.2

    Lazy loads the model only when needed and unloads it after a period of inactivity
    """

    def __init__(self):
        # Set device
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        self.torch_dtype = torch.float16 if torch.cuda.is_available() else torch.float32

        # Initialize model components as None (lazy loading)
        self.model: Optional[Any] = None
        self.processor: Optional[Any] = None
        self.pipe: Optional[Pipeline] = None

        # Track last usage time for unloading
        self.last_used: Optional[float] = None

    def _load_model(self) -> None:
        """
        Load the model, processor, and pipeline if not already loaded
        """
        if self.model is None:
            print(f"Loading transcription model on {self.device}...")

            # Load model
            self.model = AutoModelForSpeechSeq2Seq.from_pretrained(
                WHISPER_MODEL_NAME,
                torch_dtype=self.torch_dtype,
                low_cpu_mem_usage=True,
                use_safetensors=True,
            )
            self.model.to(self.device)

            # Load processor
            self.processor = AutoProcessor.from_pretrained(WHISPER_MODEL_NAME)

            # Create pipeline
            self.pipe = pipeline(
                "automatic-speech-recognition",
                model=self.model,
                tokenizer=self.processor.tokenizer,
                feature_extractor=self.processor.feature_extractor,
                max_new_tokens=128,
                chunk_length_s=30,
                batch_size=16,
                return_timestamps=True,
                torch_dtype=self.torch_dtype,
                device=self.device,
            )

            print("Transcription model loaded successfully")

        # Update last used time
        self.last_used = time.time()

    def _unload_model_if_inactive(self) -> None:
        """
        Unload model if it hasn't been used for a while and is on GPU
        """
        if (
            self.model is not None
            and self.device == "cuda"
            and self.last_used is not None
            and (time.time() - self.last_used) > MODEL_UNLOAD_TIMEOUT
        ):
            print("Unloading transcription model from GPU due to inactivity")
            self.model = None
            self.processor = None
            self.pipe = None
            self.last_used = None

            # Force garbage collection to free GPU memory
            if torch.cuda.is_available():
                torch.cuda.empty_cache()

    def transcribe(self, audio_path: str) -> Dict[str, Any]:
        """
        Transcribe audio file and return chunks with timestamps

        Loads the model if not already loaded
        """
        # Check if model should be unloaded due to inactivity
        self._unload_model_if_inactive()

        # Load model if not loaded
        self._load_model()

        # Transcribe audio
        result = self.pipe(audio_path)  # type:ignore

        # Update last used time
        self.last_used = time.time()

        return result


# Singleton instance
transcriber_service = TranscriberService()
