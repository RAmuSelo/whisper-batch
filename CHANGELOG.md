# Changelog

All notable changes to this project are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added

- CONTRIBUTING.md
- CHANGELOG.md
- A more specific README (Why + Roadmap)

### Planned

- Output formats beyond `.txt` — `.srt`, `.vtt`, and JSON segments (Whisper already produces them internally).
- Recursive folder scanning.
- A per-run summary file (done / failed / skipped) for auditable batch jobs.

## [0.1.0] - 2026-06-08

### Added

- Batch-transcribe a whole folder of audio files to text using OpenAI Whisper running locally; each audio file gets a matching `.txt` transcript.
- `--resume` to skip files whose `.txt` transcript already exists, so interrupted runs pick up where they left off.
- `--dry-run` to preview the plan without importing whisper or downloading a model.
- CLI options: `--model`, `--lang`, `--out`, `--device` (cpu/cuda/mps), and `--version`; non-zero exit if any file failed.
- Lazy whisper import (only when transcription starts), so the package imports without the heavy model.
- Library API: `build_plan` and `run_batch`, with `transcribe_fn` and `model_loader` seams for injecting your own implementation.
- Stdlib unittest test suite.
- GitHub Actions CI.
- MIT license.

[Unreleased]: https://github.com/RAmuSelo/whisper-batch/compare/v0.1.0...HEAD
[0.1.0]: https://github.com/RAmuSelo/whisper-batch/releases/tag/v0.1.0
