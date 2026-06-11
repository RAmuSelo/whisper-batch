# Contributing to whisper-batch

Thanks for your interest in improving `whisper-batch`. It is a thin orchestration layer around local OpenAI Whisper, and contributions that keep it lean are very welcome.

## Ground rules

- **No secrets in the repo.** Never commit API keys, tokens, credentials, or absolute paths from your machine.
- **ffmpeg is a system dependency.** Whisper shells out to ffmpeg to decode audio; the user installs it themselves (e.g. `brew install ffmpeg`, `apt install ffmpeg`). The tool must **not** bundle, download, or auto-install ffmpeg or any model — it orchestrates what is already available.
- **Keep the whisper import lazy.** The package must import (and the tests must run) without the heavy `openai-whisper` model. Only import whisper when transcription actually starts.

## Development setup

```bash
pip install -e . --no-deps
python3 -m unittest discover -s tests
```

Note: whisper is **not** needed to run the tests. They use the `transcribe_fn` / `model_loader` seams to avoid loading the real model, so `--no-deps` keeps the install light.

## Making a change

- Keep pull requests small and focused on a single change.
- Add or update unittest tests to cover your change (use the injection seams instead of loading the real model).
- Keep CI green (the test suite runs on Python 3.9, 3.11, and 3.12).
- No new runtime dependencies without discussion first.

## Reporting bugs

Open an issue and include:

- What you ran (the exact command and flags).
- What you expected to happen, and what actually happened.
- Your OS, Python version, device (`cpu`/`cuda`/`mps`), and `ffmpeg -version` output.
- The whisper model name used, if relevant.

Never paste secrets or absolute machine paths into an issue.

## Scope

- **In scope:** queuing a folder of audio files for local Whisper transcription, with resume support and a dry-run preview.
- **Out of scope:** shipping or installing whisper/ffmpeg/models, and the transcription model itself (this tool orchestrates the real Whisper, it does not reimplement it).
