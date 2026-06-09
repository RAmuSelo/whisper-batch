"""CLI argument-parsing and dry-run tests (stdlib unittest, no whisper)."""

import io
import os
import tempfile
import unittest
from contextlib import redirect_stdout

import _support  # noqa: F401  (also puts src/ on sys.path)

from whisper_batch import cli


class ArgParsingTests(unittest.TestCase):
    def test_defaults(self):
        args = cli.build_parser().parse_args(["myfolder"])
        self.assertEqual(args.folder, "myfolder")
        self.assertEqual(args.model, "large-v3")
        self.assertIsNone(args.lang)
        self.assertIsNone(args.out)
        self.assertIsNone(args.device)
        self.assertFalse(args.resume)
        self.assertFalse(args.dry_run)

    def test_all_flags(self):
        args = cli.build_parser().parse_args(
            [
                "audio",
                "--model",
                "small",
                "--lang",
                "en",
                "--out",
                "out",
                "--device",
                "cpu",
                "--resume",
                "--dry-run",
            ]
        )
        self.assertEqual(args.model, "small")
        self.assertEqual(args.lang, "en")
        self.assertEqual(args.out, "out")
        self.assertEqual(args.device, "cpu")
        self.assertTrue(args.resume)
        self.assertTrue(args.dry_run)

    def test_folder_is_required(self):
        with self.assertRaises(SystemExit):
            cli.build_parser().parse_args([])


class DryRunTests(unittest.TestCase):
    def test_dry_run_prints_plan_and_does_not_import_whisper(self):
        with tempfile.TemporaryDirectory() as folder:
            _support.touch(os.path.join(folder, "a.mp3"))
            _support.touch(os.path.join(folder, "b.wav"))
            _support.touch(os.path.join(folder, "notes.txt"))  # ignored input

            buf = io.StringIO()
            with redirect_stdout(buf):
                rc = cli.main([folder, "--dry-run"])

            self.assertEqual(rc, 0)
            out = buf.getvalue()
            self.assertIn("whisper-batch plan", out)
            self.assertIn("a.mp3", out)
            self.assertIn("b.wav", out)
            # The .txt input file must not be treated as an audio file.
            self.assertNotIn("notes.txt", out)
            self.assertIn("to transcribe: 2", out)

    def test_dry_run_never_loads_model(self):
        """Even if whisper were broken, --dry-run must not touch it.

        We poison core.load_model so any accidental call fails loudly.
        """
        from whisper_batch import core

        def _boom(*_a, **_k):  # pragma: no cover - only runs on regression
            raise AssertionError("dry-run must not load the model")

        original = core.load_model
        core.load_model = _boom
        try:
            with tempfile.TemporaryDirectory() as folder:
                _support.touch(os.path.join(folder, "a.mp3"))
                buf = io.StringIO()
                with redirect_stdout(buf):
                    rc = cli.main([folder, "--dry-run"])
                self.assertEqual(rc, 0)
        finally:
            core.load_model = original


if __name__ == "__main__":
    unittest.main()
