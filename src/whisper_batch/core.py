"""Transcription orchestration for whisper-batch.

The heavy dependency (``openai-whisper``) is imported lazily *inside* the
functions that actually need it. This keeps the module importable in
environments where whisper / torch / ffmpeg are not installed, which in turn
lets the test-suite exercise planning and resume logic without the model.
"""

from __future__ import annotations

import os
from typing import Callable, Iterable, List, Optional, Sequence

# Audio extensions we consider transcribable. Lower-case, leading dot.
AUDIO_EXTENSIONS: tuple = (
    ".mp3",
    ".wav",
    ".m4a",
    ".flac",
    ".ogg",
    ".opus",
    ".aac",
    ".wma",
    ".mp4",
    ".mkv",
    ".webm",
)

# Type alias for a transcribe callable, useful for dependency injection in tests.
# Signature: (audio_path, model, language) -> transcript text.
TranscribeFn = Callable[[str, object, Optional[str]], str]


def find_audio_files(folder: str, extensions: Sequence[str] = AUDIO_EXTENSIONS) -> List[str]:
    """Return a sorted list of audio file names (not full paths) inside *folder*.

    Only the immediate directory is scanned (no recursion). Matching is done on
    the lower-cased extension so ``.MP3`` and ``.mp3`` are both picked up.
    """
    if not os.path.isdir(folder):
        raise NotADirectoryError(f"Not a directory: {folder}")

    ext_set = {e.lower() for e in extensions}
    names = []
    for entry in os.listdir(folder):
        full = os.path.join(folder, entry)
        if not os.path.isfile(full):
            continue
        if os.path.splitext(entry)[1].lower() in ext_set:
            names.append(entry)
    names.sort()
    return names


def build_output_path(audio_name: str, out_dir: str) -> str:
    """Build the destination ``.txt`` path for a given audio file name.

    The base name (without its audio extension) is reused and ``.txt`` appended,
    e.g. ``meeting.mp3`` -> ``<out_dir>/meeting.txt``. Only the base name of
    *audio_name* is used, so passing a full path is also safe.
    """
    base = os.path.splitext(os.path.basename(audio_name))[0]
    return os.path.join(out_dir, base + ".txt")


def is_already_done(audio_name: str, out_dir: str) -> bool:
    """Return True if the transcript for *audio_name* already exists in *out_dir*."""
    return os.path.exists(build_output_path(audio_name, out_dir))


def build_plan(
    folder: str,
    out_dir: Optional[str] = None,
    resume: bool = False,
    extensions: Sequence[str] = AUDIO_EXTENSIONS,
) -> dict:
    """Compute what the batch run would do, without touching whisper.

    Returns a dict with keys:
        - ``folder``:   resolved input folder
        - ``out_dir``:  resolved output directory (defaults to *folder*)
        - ``all``:      list of all discovered audio file names
        - ``todo``:     names that still need transcription
        - ``done``:     names already transcribed (only populated when *resume*)

    When *resume* is False, every discovered file is scheduled (``done`` empty),
    matching the intuitive "re-do everything" behaviour. Resume skips files whose
    ``.txt`` output already exists.
    """
    resolved_out = out_dir or folder
    all_files = find_audio_files(folder, extensions)

    todo: List[str] = []
    done: List[str] = []
    for name in all_files:
        if resume and is_already_done(name, resolved_out):
            done.append(name)
        else:
            todo.append(name)

    return {
        "folder": folder,
        "out_dir": resolved_out,
        "all": all_files,
        "todo": todo,
        "done": done,
    }


def format_plan(plan: dict) -> str:
    """Render a human-readable summary of a plan (used by --dry-run)."""
    lines = [
        "whisper-batch plan",
        f"  input folder : {plan['folder']}",
        f"  output dir   : {plan['out_dir']}",
        f"  discovered   : {len(plan['all'])} audio file(s)",
        f"  already done : {len(plan['done'])}",
        f"  to transcribe: {len(plan['todo'])}",
    ]
    if plan["todo"]:
        lines.append("  queue:")
        for name in plan["todo"]:
            lines.append(f"    - {name}")
    return "\n".join(lines)


def load_model(model_name: str, device: Optional[str] = None):
    """Load a Whisper model. Imports whisper lazily.

    *device* may be ``None`` (let whisper decide), ``"cpu"``, ``"cuda"`` or
    ``"mps"`` (Apple Silicon). Raises a clear error if whisper is missing.
    """
    try:
        import whisper  # type: ignore
    except ImportError as exc:  # pragma: no cover - exercised only without whisper
        raise ImportError(
            "openai-whisper is required for transcription. "
            "Install it with `pip install openai-whisper` "
            "(and make sure ffmpeg is available on your PATH)."
        ) from exc

    return whisper.load_model(model_name, device=device)


def transcribe_file(audio_path: str, model: object, language: Optional[str] = None) -> str:
    """Transcribe a single audio file and return the transcript text.

    This is the default :data:`TranscribeFn`. ``model`` is a loaded whisper
    model object (see :func:`load_model`). Whisper itself is not imported here;
    we only call ``model.transcribe(...)``, so tests can pass a fake model.
    """
    kwargs = {
        "task": "transcribe",
        "verbose": False,
        "fp16": False,  # safe default; required for CPU / Apple MPS backends
    }
    if language:
        kwargs["language"] = language

    result = model.transcribe(audio_path, **kwargs)
    return (result.get("text") or "").strip()


def run_batch(
    folder: str,
    model_name: str = "large-v3",
    language: Optional[str] = None,
    out_dir: Optional[str] = None,
    resume: bool = False,
    device: Optional[str] = None,
    extensions: Sequence[str] = AUDIO_EXTENSIONS,
    transcribe_fn: Optional[TranscribeFn] = None,
    model_loader: Optional[Callable[[str, Optional[str]], object]] = None,
    log: Optional[Callable[[str], None]] = None,
) -> dict:
    """Run the full batch transcription.

    Parameters mirror the CLI. The two seams ``transcribe_fn`` and
    ``model_loader`` exist so the orchestration can be tested without whisper:
    inject fakes and no real model is ever loaded.

    Returns a summary dict: ``{"done": [...], "failed": [(name, error), ...],
    "skipped": [...], "out_dir": ...}``.
    """
    emit = log or (lambda _msg: None)
    do_transcribe = transcribe_fn or transcribe_file
    load = model_loader or load_model

    plan = build_plan(folder, out_dir=out_dir, resume=resume, extensions=extensions)
    resolved_out = plan["out_dir"]
    os.makedirs(resolved_out, exist_ok=True)

    skipped = list(plan["done"])
    for name in skipped:
        emit(f"skip (already done): {name}")

    todo = plan["todo"]
    if not todo:
        emit("nothing to transcribe")
        return {"done": [], "failed": [], "skipped": skipped, "out_dir": resolved_out}

    # Load the model only once, only when there is real work to do.
    model = load(model_name, device)

    done: List[str] = []
    failed: List[tuple] = []
    total = len(todo)
    for index, name in enumerate(todo, start=1):
        audio_path = os.path.join(folder, name)
        out_path = build_output_path(name, resolved_out)
        emit(f"[{index}/{total}] transcribing: {name}")
        try:
            text = do_transcribe(audio_path, model, language)
            with open(out_path, "w", encoding="utf-8") as handle:
                handle.write(text + "\n")
            done.append(name)
            emit(f"[{index}/{total}] saved: {out_path}")
        except Exception as exc:  # noqa: BLE001 - report and continue the batch
            failed.append((name, str(exc)))
            emit(f"[{index}/{total}] FAILED: {name}: {exc}")

    emit(f"done: {len(done)} ok, {len(failed)} failed, {len(skipped)} skipped")
    return {"done": done, "failed": failed, "skipped": skipped, "out_dir": resolved_out}


def iter_plan_names(plan: dict) -> Iterable[str]:
    """Convenience iterator over the queued file names of a plan."""
    return iter(plan["todo"])
