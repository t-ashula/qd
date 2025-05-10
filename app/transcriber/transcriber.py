import os
import time
from typing import Any, Dict, List, Optional, Tuple

import torch
from transformers import AutoModelForSpeechSeq2Seq, AutoProcessor, pipeline
from transformers.pipelines.base import Pipeline

# Available models
AVAILABLE_MODELS = {
    "kotoba-tech/kotoba-whisper-v2.2": "Kotoba Whisper v2.2",
    "openai/whisper-large-v3": "OpenAI Whisper Large v3",
}

# Default model
DEFAULT_MODEL = "kotoba-tech/kotoba-whisper-v2.2"

# Unload model after this many seconds of inactivity
MODEL_UNLOAD_TIMEOUT = 300  # 5 minutes


class ModelInstance:
    """
    Class to hold a model instance and its components
    """

    def __init__(self, model_name: str, device: str, torch_dtype: torch.dtype):
        self.model_name = model_name
        self.device = device
        self.torch_dtype = torch_dtype
        self.model: Optional[Any] = None
        self.processor: Optional[Any] = None
        self.pipe: Optional[Pipeline] = None
        self.last_used: Optional[float] = None

    def load(self) -> None:
        """
        Load the model, processor, and pipeline
        """
        if self.model is None:
            print(f"Loading transcription model {self.model_name} on {self.device}...")

            # Load model
            self.model = AutoModelForSpeechSeq2Seq.from_pretrained(
                self.model_name,
                torch_dtype=self.torch_dtype,
                low_cpu_mem_usage=True,
                use_safetensors=True,
            )
            self.model.to(self.device)
            self.processor = AutoProcessor.from_pretrained(self.model_name)
            # Create pipeline
            generate_kwargs = {
                "num_beams": 6,
                # "best_of": 6,
                "temperature": [0.0],
                "no_repeat_ngram_size": 3,
                "logprob_threshold": -1.0,
                "compression_ratio_threshold": 2.4,
            }
            if self.model_name == "kotoba-tech/kotoba-whisper-v2.2":
                generate_kwargs["language"] = "ja"

            self.pipe = pipeline(
                "automatic-speech-recognition",
                model=self.model,
                tokenizer=self.processor.tokenizer,
                feature_extractor=self.processor.feature_extractor,
                chunk_length_s=25,
                stride_length_s=6,
                return_timestamps=True,
                torch_dtype=self.torch_dtype,
                device=self.device,
                generate_kwargs=generate_kwargs,
            )

            print(f"Transcription model {self.model_name} loaded successfully")

        # Update last used time
        self.last_used = time.time()

    def unload_if_inactive(self) -> None:
        """
        Unload model if it hasn't been used for a while and is on GPU
        """
        if (
            self.model is not None
            and self.device == "cuda"
            and self.last_used is not None
            and (time.time() - self.last_used) > MODEL_UNLOAD_TIMEOUT
        ):
            print(
                f"Unloading transcription model {self.model_name} from GPU due to inactivity"
            )
            self.model = None
            self.processor = None
            self.pipe = None
            self.last_used = None

            # Force garbage collection to free GPU memory
            if torch.cuda.is_available():
                torch.cuda.empty_cache()

    def transcribe(self, audio_path: str) -> Dict[str, Any]:
        """
        Transcribe audio file using this model instance
        """
        # Load model if not loaded
        self.load()

        if self.pipe is None:
            raise RuntimeError("no pipeline found")

        # Transcribe audio
        result = self.pipe(audio_path, chunk_length_s=25, stride_length_s=6)

        # Update last used time
        self.last_used = time.time()

        return result


class TranscriberService:
    """
    Service for audio transcription using multiple models

    Lazy loads models only when needed and unloads them after a period of inactivity
    """

    def __init__(self):
        # Set device
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        self.torch_dtype = torch.float16 if torch.cuda.is_available() else torch.float32

        # Dictionary to store model instances
        self.model_instances: Dict[str, ModelInstance] = {}

    def get_available_models(self) -> Dict[str, str]:
        """
        Get available models

        Returns:
            Dictionary of model_name: display_name
        """
        return AVAILABLE_MODELS

    def _get_model_instance(self, model_name: str) -> ModelInstance:
        """
        Get or create a model instance for the specified model
        """
        if model_name not in AVAILABLE_MODELS:
            print(f"Warning: Model {model_name} not in available models, using default")
            model_name = DEFAULT_MODEL

        if model_name not in self.model_instances:
            self.model_instances[model_name] = ModelInstance(
                model_name, self.device, self.torch_dtype
            )

        return self.model_instances[model_name]

    def _unload_inactive_models(self) -> None:
        """
        Unload all inactive models
        """
        for model_instance in self.model_instances.values():
            model_instance.unload_if_inactive()

    def transcribe(
        self, audio_path: str, model_name: str = DEFAULT_MODEL
    ) -> Dict[str, Any]:
        """
        Transcribe audio file and return chunks with timestamps

        Args:
            audio_path: Path to audio file
            model_name: Name of the model to use (default: DEFAULT_MODEL)

        Returns:
            Dictionary with transcription results
        """
        # Check if models should be unloaded due to inactivity
        self._unload_inactive_models()

        # Get model instance
        model_instance = self._get_model_instance(model_name)

        # Transcribe audio
        result = model_instance.transcribe(audio_path)

        # Add model name to result
        result["model_name"] = model_name

        return result


# Singleton instance
transcriber_service = TranscriberService()
