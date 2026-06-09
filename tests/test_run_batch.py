"""Tests for run_batch orchestration using injected fakes (no whisper)."""

import os
import tempfile
import unittest

import _support  # noqa: F401  (also puts src/ on sys.path)

from whisper_batch import core


class FakeModel:
    """Stands in for a loaded whisper model; records calls."""

    def __init__(self):
        self.calls = []

    def transcribe(self, audio_path, **kwargs):  # mimics whisper's API
        self.calls.append(audio_path)
        return {"text": "  hello from " + os.path.basename(audio_path) + "  "}


class RunBatchTests(unittest.TestCase):
    def setUp(self):
        self.folder = tempfile.mkdtemp()
        for name in ("a.mp3", "b.mp3"):
            _support.touch(os.path.join(self.folder, name))
        self.loaded = []

    def _loader(self, model_name, device):
        model = FakeModel()
        self.loaded.append((model_name, device))
        return model

    def test_transcribes_all_and_writes_files(self):
        summary = core.run_batch(
            self.folder,
            model_name="tiny",
            model_loader=self._loader,
        )
        self.assertEqual(summary["done"], ["a.mp3", "b.mp3"])
        self.assertEqual(summary["failed"], [])
        # Output files exist with stripped text.
        a_txt = os.path.join(self.folder, "a.txt")
        self.assertTrue(os.path.exists(a_txt))
        with open(a_txt, encoding="utf-8") as fh:
            self.assertEqual(fh.read(), "hello from a.mp3\n")
        # Model loaded exactly once, with the requested name.
        self.assertEqual(self.loaded, [("tiny", None)])

    def test_resume_skips_existing_and_does_only_remaining(self):
        _support.touch(os.path.join(self.folder, "a.txt"), "old transcript\n")
        summary = core.run_batch(
            self.folder,
            resume=True,
            model_loader=self._loader,
        )
        self.assertEqual(summary["skipped"], ["a.mp3"])
        self.assertEqual(summary["done"], ["b.mp3"])
        # The pre-existing transcript must be left untouched.
        with open(os.path.join(self.folder, "a.txt"), encoding="utf-8") as fh:
            self.assertEqual(fh.read(), "old transcript\n")

    def test_custom_transcribe_fn_is_used(self):
        seen = []

        def fake_transcribe(audio_path, model, language):
            seen.append((os.path.basename(audio_path), language))
            return "TEXT:" + os.path.basename(audio_path)

        summary = core.run_batch(
            self.folder,
            language="fr",
            transcribe_fn=fake_transcribe,
            model_loader=self._loader,
        )
        self.assertEqual(summary["done"], ["a.mp3", "b.mp3"])
        self.assertEqual(seen, [("a.mp3", "fr"), ("b.mp3", "fr")])
        with open(os.path.join(self.folder, "b.txt"), encoding="utf-8") as fh:
            self.assertEqual(fh.read(), "TEXT:b.mp3\n")

    def test_failure_is_recorded_and_batch_continues(self):
        def flaky(audio_path, model, language):
            name = os.path.basename(audio_path)
            if name == "a.mp3":
                raise RuntimeError("decode error")
            return "ok"

        summary = core.run_batch(
            self.folder,
            transcribe_fn=flaky,
            model_loader=self._loader,
        )
        self.assertEqual([n for n, _ in summary["failed"]], ["a.mp3"])
        self.assertEqual(summary["done"], ["b.mp3"])
        # Failed file produced no output; successful one did.
        self.assertFalse(os.path.exists(os.path.join(self.folder, "a.txt")))
        self.assertTrue(os.path.exists(os.path.join(self.folder, "b.txt")))

    def test_nothing_to_do_does_not_load_model(self):
        empty = tempfile.mkdtemp()
        summary = core.run_batch(empty, model_loader=self._loader)
        self.assertEqual(summary["done"], [])
        self.assertEqual(self.loaded, [])  # loader never called

    def test_out_dir_is_created_and_used(self):
        out = os.path.join(tempfile.mkdtemp(), "fresh_out")
        self.assertFalse(os.path.exists(out))
        summary = core.run_batch(
            self.folder,
            out_dir=out,
            model_loader=self._loader,
        )
        self.assertEqual(summary["out_dir"], out)
        self.assertTrue(os.path.isdir(out))
        self.assertTrue(os.path.exists(os.path.join(out, "a.txt")))
        # Nothing written back into the source folder.
        self.assertFalse(os.path.exists(os.path.join(self.folder, "a.txt")))


class TranscribeFileTests(unittest.TestCase):
    def test_transcribe_file_strips_and_passes_language(self):
        model = FakeModel()
        text = core.transcribe_file("/tmp/x.mp3", model, language="en")
        self.assertEqual(text, "hello from x.mp3")
        self.assertEqual(model.calls, ["/tmp/x.mp3"])


if __name__ == "__main__":
    unittest.main()
