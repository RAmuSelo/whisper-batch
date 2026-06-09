# whisper-batch

[![Tests](https://github.com/RAmuSelo/whisper-batch/actions/workflows/tests.yml/badge.svg)](https://github.com/RAmuSelo/whisper-batch/actions/workflows/tests.yml)

Batch-transcribe a whole folder of audio files to text using
[OpenAI Whisper](https://github.com/openai/whisper) running **locally** — with
**resume support** so interrupted runs pick up where they left off.

Point it at a directory, and every audio file (`.mp3`, `.wav`, `.m4a`, `.flac`,
`.ogg`, …) gets a matching `.txt` transcript next to it (or in an output folder
of your choice). Re-run with `--resume` and already-transcribed files are
skipped.

## Why

Whisper's own CLI transcribes one file at a time. When you have a folder full of
recordings, you want to:

- queue the whole folder in one command,
- not re-transcribe files you already did (`--resume`),
- preview what *would* run before spending GPU/CPU time (`--dry-run`).

That's all this tool does — a thin, dependency-light orchestration layer around
the real Whisper model.

## Install

```bash
pip install -e .
```

> **For real transcription you also need:**
> - `openai-whisper` (installed automatically as a dependency), and
> - **ffmpeg** available on your `PATH` — Whisper shells out to it to decode
>   audio. Install it via your package manager, e.g. `brew install ffmpeg`
>   (macOS) or `apt install ffmpeg` (Debian/Ubuntu).
>
> The package itself imports fine without these (whisper is imported lazily,
> only when you actually start a transcription), which is why the test-suite
> runs with zero heavy dependencies.

## Usage

```bash
# Transcribe every audio file in ./recordings, write .txt next to each file.
whisper-batch ./recordings

# Force English, use the small model, write transcripts to ./out
whisper-batch ./recordings --model small --lang en --out ./out

# Resume: skip files already transcribed in the output folder
whisper-batch ./recordings --out ./out --resume

# Preview the plan without loading whisper (fast, no model download)
whisper-batch ./recordings --resume --dry-run

# Pick a device explicitly (cpu / cuda / mps)
whisper-batch ./recordings --device cpu
```

### Options

| Option           | Default     | Description                                              |
| ---------------- | ----------- | -------------------------------------------------------- |
| `folder`         | (required)  | Folder containing the audio files.                       |
| `--model`        | `large-v3`  | Whisper model name (`tiny`…`large-v3`).                  |
| `--lang`         | auto-detect | Force a language code (e.g. `en`, `fr`, `es`).           |
| `--out`          | same folder | Output directory for `.txt` transcripts.                 |
| `--device`       | auto        | Compute device: `cpu`, `cuda`, or `mps` (Apple Silicon). |
| `--resume`       | off         | Skip files whose `.txt` already exists.                  |
| `--dry-run`      | off         | Print the plan and exit, without importing whisper.      |
| `--version`      |             | Print version and exit.                                  |

The process exits non-zero if any file failed, so it's safe to use in scripts.

## Use as a library

```python
from whisper_batch import build_plan, run_batch

# Inspect what would happen — no whisper import.
plan = build_plan("recordings", out_dir="out", resume=True)
print(plan["todo"])   # list of audio files still to do

# Actually run it.
summary = run_batch("recordings", model_name="small", language="en", out_dir="out")
print(summary["done"], summary["failed"])
```

`run_batch` accepts `transcribe_fn` and `model_loader` seams for injecting your
own implementation (also how the tests avoid loading the real model).

## Development

```bash
pip install -e ".[dev]"
python3 -m unittest discover -s tests   # stdlib unittest, no network, no whisper
```

## Roadmap

Honest next steps:

- Output formats beyond `.txt` — `.srt`, `.vtt`, and JSON segments (Whisper already produces them internally).
- Recursive folder scanning.
- A per-run summary file (done / failed / skipped) for auditable batch jobs.

## License

MIT — see [LICENSE](LICENSE).
