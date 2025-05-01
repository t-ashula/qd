import os
from typing import Any, Dict, List, Tuple

import torch
from transformers import AutoModelForSpeechSeq2Seq, AutoProcessor, pipeline

# Model name
WHISPER_MODEL_NAME = "kotoba-tech/kotoba-whisper-v2.2"


class TranscriberService:
    """
    Service for audio transcription using kotoba-whisper-v2.2
    """

    def __init__(self):
        # Set device
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        self.torch_dtype = torch.float16 if torch.cuda.is_available() else torch.float32

        # Load model and processor
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

    def transcribe(self, audio_path: str) -> Dict[str, Any]:
        """
        Transcribe audio file and return chunks with timestamps
        """
        result = self.pipe(audio_path)
        return result


# Singleton instance
transcriber_service = TranscriberService()
