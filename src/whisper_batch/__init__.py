"""whisper-batch: batch-transcribe a folder of audio files using OpenAI Whisper.

Public API re-exports the most useful helpers from :mod:`whisper_batch.core`
so callers can do ``from whisper_batch import build_plan, run_batch``.
"""

from .core import (
    AUDIO_EXTENSIONS,
    build_output_path,
    build_plan,
    find_audio_files,
    is_already_done,
    run_batch,
    transcribe_file,
)

__version__ = "0.1.0"

__all__ = [
    "AUDIO_EXTENSIONS",
    "build_output_path",
    "build_plan",
    "find_audio_files",
    "is_already_done",
    "run_batch",
    "transcribe_file",
    "__version__",
]
