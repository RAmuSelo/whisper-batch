# Release Readiness — whisper-batch

## What it is

`whisper-batch` is a small command-line tool (and importable library) that
batch-transcribes a folder of audio files to text using OpenAI Whisper running
locally, with **resume** support. It discovers audio files in a directory,
writes one `.txt` transcript per file, and can skip files already transcribed.

- CLI driven entirely by `argparse` (no interactive prompts).
- `--dry-run` prints the plan without importing/loading Whisper.
- `--resume` skips files whose `.txt` output already exists.
- Whisper is imported **lazily** inside the functions that need it, so the
  package imports and the full test-suite run with zero heavy dependencies.

## Layout

```
whisper-batch/
├── LICENSE                     # MIT, "The whisper-batch authors", 2026
├── README.md
├── RELEASE_READINESS.md
├── pyproject.toml              # setuptools, entry point whisper-batch
├── .gitignore
├── src/whisper_batch/
│   ├── __init__.py             # public API re-exports
│   ├── cli.py                  # argparse CLI, main()
│   └── core.py                 # discovery / planning / orchestration (lazy whisper)
└── tests/                      # stdlib unittest
    ├── __init__.py
    ├── _support.py             # path bootstrap + helpers
    ├── test_cli.py             # arg parsing + dry-run (no whisper)
    ├── test_planning.py        # discovery, output paths, resume logic
    └── test_run_batch.py       # orchestration via injected fakes
```

## Tests

- Framework: **stdlib `unittest`** (no third-party test runner needed).
- Command: `python3 -m unittest discover -s tests`
- Result: **22 tests, all passing (OK)**, ~0.007s.
- No network access, no Whisper, no torch. Verified that neither `whisper` nor
  `torch` appears in `sys.modules` after a full discovery run.
- `--dry-run` is explicitly tested to never load the model (the loader is
  poisoned in one test to prove it is not called).
- Orchestration (`run_batch`) is tested through injected `transcribe_fn` and
  `model_loader` seams: success path, resume/skip, per-file failure isolation,
  "nothing to do" (model never loaded), and output-dir creation.

## Secrets / personal data

- Secret/personal-path scan (user home prefix, Shopify/Google/OpenAI key
  prefixes) → **CLEAN** (no matches).
- No hardcoded personal paths, no API keys, no tokens. No `input()` prompts.
- No network calls anywhere in the code.

## Dependencies note

- Runtime: `openai-whisper` (declared in `pyproject.toml`).
- **System requirement for real use:** `ffmpeg` must be on `PATH` (Whisper
  shells out to it to decode audio). Not needed to import the package or run
  tests.
- Optional dev extra: `pytest` (the suite itself uses stdlib `unittest`, so
  pytest is not required).

## Install / run

```bash
pip install -e .
whisper-batch ./recordings --resume          # real run
whisper-batch ./recordings --dry-run         # preview, no whisper needed
python3 -m unittest discover -s tests        # tests
```

## Status

**READY.** Clean local OSS repo. Builds via setuptools (`src/` layout,
console entry point `whisper-batch = whisper_batch.cli:main`). All tests pass,
no secrets, lazy-import design verified. No git history initialized (per
request). No known blockers.
