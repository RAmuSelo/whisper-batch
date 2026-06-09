"""Command-line interface for whisper-batch.

Usage is driven entirely by argparse (no interactive prompts), so the tool is
scriptable and CI-friendly.
"""

from __future__ import annotations

import argparse
import sys
from typing import List, Optional

from . import __version__
from .core import build_plan, format_plan, run_batch


def build_parser() -> argparse.ArgumentParser:
    """Create the argument parser for the CLI."""
    parser = argparse.ArgumentParser(
        prog="whisper-batch",
        description=(
            "Batch-transcribe a folder of audio files to text using OpenAI "
            "Whisper (running locally), with resume support."
        ),
    )
    parser.add_argument(
        "folder",
        help="Folder containing the audio files to transcribe.",
    )
    parser.add_argument(
        "--model",
        default="large-v3",
        help="Whisper model name (default: large-v3). E.g. tiny, base, small, "
        "medium, large-v3.",
    )
    parser.add_argument(
        "--lang",
        default=None,
        help="Language code to force, e.g. en, fr, es. Omit to auto-detect.",
    )
    parser.add_argument(
        "--out",
        default=None,
        help="Output directory for .txt transcripts (default: same as folder).",
    )
    parser.add_argument(
        "--device",
        default=None,
        help="Compute device passed to whisper: cpu, cuda or mps. "
        "Omit to let whisper choose.",
    )
    parser.add_argument(
        "--resume",
        action="store_true",
        help="Skip audio files whose .txt transcript already exists.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print the plan (what would be transcribed) and exit without "
        "loading whisper.",
    )
    parser.add_argument(
        "--version",
        action="version",
        version=f"%(prog)s {__version__}",
    )
    return parser


def main(argv: Optional[List[str]] = None) -> int:
    """Entry point. Returns a process exit code (0 = success)."""
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.dry_run:
        # Planning only — never imports whisper.
        plan = build_plan(args.folder, out_dir=args.out, resume=args.resume)
        print(format_plan(plan))
        return 0

    summary = run_batch(
        args.folder,
        model_name=args.model,
        language=args.lang,
        out_dir=args.out,
        resume=args.resume,
        device=args.device,
        log=print,
    )

    # Non-zero exit if any file failed, so callers/CI can detect partial runs.
    return 1 if summary["failed"] else 0


if __name__ == "__main__":  # pragma: no cover
    sys.exit(main())
