"""Tests for file discovery, output-path building, and resume logic."""

import os
import tempfile
import unittest

import _support  # noqa: F401  (also puts src/ on sys.path)

from whisper_batch import core


class OutputPathTests(unittest.TestCase):
    def test_build_output_path_swaps_extension(self):
        self.assertEqual(
            core.build_output_path("meeting.mp3", "out"),
            os.path.join("out", "meeting.txt"),
        )

    def test_build_output_path_uses_basename_only(self):
        # A full path as input still yields just <out>/<base>.txt
        self.assertEqual(
            core.build_output_path(os.path.join("a", "b", "clip.wav"), "out"),
            os.path.join("out", "clip.txt"),
        )

    def test_build_output_path_handles_dotted_names(self):
        self.assertEqual(
            core.build_output_path("ep.01.final.m4a", "out"),
            os.path.join("out", "ep.01.final.txt"),
        )


class FindAudioFilesTests(unittest.TestCase):
    def test_finds_only_audio_sorted_case_insensitive(self):
        with tempfile.TemporaryDirectory() as d:
            _support.touch(os.path.join(d, "b.mp3"))
            _support.touch(os.path.join(d, "a.WAV"))  # upper-case ext
            _support.touch(os.path.join(d, "c.flac"))
            _support.touch(os.path.join(d, "readme.txt"))  # not audio
            _support.touch(os.path.join(d, "image.png"))   # not audio
            found = core.find_audio_files(d)
            self.assertEqual(found, ["a.WAV", "b.mp3", "c.flac"])

    def test_ignores_subdirectories(self):
        with tempfile.TemporaryDirectory() as d:
            os.makedirs(os.path.join(d, "nested.mp3"))  # a *dir* named like audio
            _support.touch(os.path.join(d, "real.mp3"))
            found = core.find_audio_files(d)
            self.assertEqual(found, ["real.mp3"])

    def test_missing_folder_raises(self):
        with self.assertRaises(NotADirectoryError):
            core.find_audio_files("/this/does/not/exist/whisper-batch-xyz")


class ResumePlanTests(unittest.TestCase):
    def _make_folder(self):
        d = tempfile.mkdtemp()
        for name in ("one.mp3", "two.mp3", "three.mp3"):
            _support.touch(os.path.join(d, name))
        return d

    def test_no_resume_schedules_everything(self):
        d = self._make_folder()
        # Pre-existing transcript should be ignored when resume is off.
        _support.touch(os.path.join(d, "one.txt"))
        plan = core.build_plan(d, resume=False)
        self.assertEqual(plan["todo"], ["one.mp3", "three.mp3", "two.mp3"])
        self.assertEqual(plan["done"], [])

    def test_resume_skips_done_files(self):
        d = self._make_folder()
        _support.touch(os.path.join(d, "one.txt"))   # already done
        _support.touch(os.path.join(d, "two.txt"))   # already done
        plan = core.build_plan(d, resume=True)
        self.assertEqual(plan["done"], ["one.mp3", "two.mp3"])
        self.assertEqual(plan["todo"], ["three.mp3"])

    def test_resume_uses_out_dir_for_done_check(self):
        d = self._make_folder()
        out = tempfile.mkdtemp()
        # transcript lives in the OUT dir, not next to audio
        _support.touch(os.path.join(out, "two.txt"))
        plan = core.build_plan(d, out_dir=out, resume=True)
        self.assertEqual(plan["out_dir"], out)
        self.assertEqual(plan["done"], ["two.mp3"])
        self.assertEqual(plan["todo"], ["one.mp3", "three.mp3"])

    def test_is_already_done(self):
        d = self._make_folder()
        _support.touch(os.path.join(d, "one.txt"))
        self.assertTrue(core.is_already_done("one.mp3", d))
        self.assertFalse(core.is_already_done("two.mp3", d))


if __name__ == "__main__":
    unittest.main()
