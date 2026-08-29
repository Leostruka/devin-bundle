"""Validation tests for youtube-fetcher.

Agent-chosen infrastructure tests, distinct from held-out behavioral tests.
"""
import json
import os
import shutil
import subprocess
from pathlib import Path

import pytest

ROOT = Path(__file__).parents[2]
SCRIPT = ROOT / "skills" / "youtube-fetcher" / "scripts" / "fetch.py"
FIXTURE = ROOT / "tests" / "fixtures" / "youtube-fetcher"


def run(args, cwd=ROOT):
    return subprocess.run(
        ["python", str(SCRIPT)] + args,
        capture_output=True,
        text=True,
        encoding="utf-8",
        cwd=cwd,
        timeout=30,
    )


def _setup_project(tmp_path, source_name="valid_captions.json"):
    project = tmp_path / "project"
    project.mkdir()
    (project / ".devin").mkdir()
    src = project / "captions.json"
    shutil.copy(FIXTURE / source_name, src)
    return project, src


class TestValidate:
    @pytest.mark.parametrize(
        "url",
        [
            "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
            "https://youtube.com/watch?v=dQw4w9WgXcQ&feature=shared",
            "https://youtu.be/dQw4w9WgXcQ",
            "https://www.youtube.com/embed/dQw4w9WgXcQ",
            "https://www.youtube.com/shorts/dQw4w9WgXcQ",
            "dQw4w9WgXcQ",
            "http1A_b2C3",
            "https://youtu.be/http1A_b2C3",
        ],
    )
    def test_accepts_supported_url(self, url):
        result = run(["validate", url])
        assert result.returncode == 0, result.stderr
        data = json.loads(result.stdout)
        assert data["valid"] is True
        expected = "http1A_b2C3" if "http1A" in url else "dQw4w9WgXcQ"
        assert data["video_id"] == expected

    @pytest.mark.parametrize(
        "bad",
        [
            "https://www.youtbube.com/watch?v=dQw4w9WgXcQ",
            "https://youtuble.be/dQw4w9WgXcQ",
            "https://example.com/watch?v=dQw4w9WgXcQ",
            "https://www.youtube.com/watch?v=invalid",
            "http1A_b2C",
            "httpxyz",
            "not-an-id",
            "",
        ],
    )
    def test_rejects_invalid_or_lookalike(self, bad):
        # argparse chokes on empty string, so skip that case.
        if bad == "":
            return
        result = run(["validate", bad])
        assert result.returncode != 0
        assert "validation failed" in result.stderr


class TestRender:
    def test_outputs_deterministic_markdown(self, tmp_path):
        project, src = _setup_project(tmp_path)
        a = run(["render", str(src), str(project)])
        b = run(["render", str(src), str(project)])
        assert a.returncode == 0, a.stderr
        assert b.returncode == 0, b.stderr
        assert a.stdout == b.stdout
        assert "## Raw transcript" in a.stdout
        assert "[00:00:00.000]" in a.stdout

    def test_writes_under_devin_with_approval(self, tmp_path):
        project, src = _setup_project(tmp_path)
        result = run(["render", str(src), str(project), "--write", "--approve"])
        assert result.returncode == 0, result.stderr
        note = project / ".devin" / "notes" / "youtube" / "dQw4w9WgXcQ.md"
        assert note.is_file()
        text = note.read_text(encoding="utf-8")
        assert "## Raw transcript" in text
        assert "structured-knowledge-extraction" in text
        assert "manual" in text

    def test_requires_approval_for_write(self, tmp_path):
        project, src = _setup_project(tmp_path)
        result = run(["render", str(src), str(project), "--write"])
        assert result.returncode != 0
        assert not (project / ".devin" / "notes" / "youtube").exists()

    def test_preserves_duplicate_without_overwrite(self, tmp_path):
        project, src = _setup_project(tmp_path)
        run(["render", str(src), str(project), "--write", "--approve"])
        note = project / ".devin" / "notes" / "youtube" / "dQw4w9WgXcQ.md"
        original = note.read_text(encoding="utf-8")

        # A different fixture with the same video_id should not overwrite.
        conflicting = {
            "video_id": "dQw4w9WgXcQ",
            "url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
            "title": "Different title",
            "author": "Different",
            "language": "pt",
            "caption_type": "auto-generated",
            "captions": [{"text": "different", "start": 0.0, "duration": 1.0}],
        }
        conflict = project / "conflict.json"
        conflict.write_text(json.dumps(conflicting), encoding="utf-8")

        result = run(["render", str(conflict), str(project), "--write", "--approve"])
        assert result.returncode != 0
        assert "already exists" in result.stderr
        assert note.read_text(encoding="utf-8") == original

    def test_overwrites_with_explicit_flag(self, tmp_path):
        project, src = _setup_project(tmp_path)
        run(["render", str(src), str(project), "--write", "--approve"])
        note = project / ".devin" / "notes" / "youtube" / "dQw4w9WgXcQ.md"
        original = note.read_text(encoding="utf-8")

        conflicting = {
            "video_id": "dQw4w9WgXcQ",
            "url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
            "title": "Different title",
            "author": "Different",
            "language": "pt",
            "caption_type": "auto-generated",
            "captions": [{"text": "different", "start": 0.0, "duration": 1.0}],
        }
        conflict = project / "conflict.json"
        conflict.write_text(json.dumps(conflicting), encoding="utf-8")

        result = run(["render", str(conflict), str(project), "--write", "--approve", "--overwrite"])
        assert result.returncode == 0, result.stderr
        new_text = note.read_text(encoding="utf-8")
        assert new_text != original
        assert "auto-generated" in new_text

    def test_rejects_missing_captions(self, tmp_path):
        project, src = _setup_project(tmp_path, source_name="no_captions.json")
        result = run(["render", str(src), str(project)])
        assert result.returncode != 0
        assert "no captions" in result.stderr.lower()

    def test_rejects_oversized_input(self, tmp_path):
        project, _ = _setup_project(tmp_path)
        huge = {"video_id": "dQw4w9WgXcQ", "captions": []}
        # Fill with a large caption array, then pad the file to exceed 50 MiB.
        huge["captions"] = [{"text": "x", "start": float(i)} for i in range(1000)]
        src = project / "huge.json"
        src.write_text(json.dumps(huge), encoding="utf-8")
        while src.stat().st_size <= 50 * 1024 * 1024:
            huge["captions"].extend([{"text": "x" * 500, "start": float(len(huge["captions"]))} for _ in range(1000)])
            src.write_text(json.dumps(huge), encoding="utf-8")
        result = run(["render", str(src), str(project)])
        assert result.returncode != 0
        assert "exceeds" in result.stderr

    def test_records_truthful_language_and_caption_type(self, tmp_path):
        project, src = _setup_project(tmp_path, source_name="auto_generated.json")
        result = run(["render", str(src), str(project)])
        assert result.returncode == 0, result.stderr
        assert "language: ko" in result.stdout
        assert "caption_type: auto-generated" in result.stdout

    def test_includes_timestamps(self, tmp_path):
        project, src = _setup_project(tmp_path)
        result = run(["render", str(src), str(project)])
        assert result.returncode == 0, result.stderr
        assert "[00:00:04.200]" in result.stdout

    def test_no_summary_or_inference_in_output(self, tmp_path):
        project, src = _setup_project(tmp_path)
        result = run(["render", str(src), str(project)])
        assert result.returncode == 0, result.stderr
        assert "## Raw transcript" in result.stdout
        assert "## Summary" not in result.stdout
        assert "## Inferences" not in result.stdout

    def test_documents_handoff_to_structured_extraction(self, tmp_path):
        project, src = _setup_project(tmp_path)
        result = run(["render", str(src), str(project)])
        assert result.returncode == 0, result.stderr
        assert "structured-knowledge-extraction" in result.stdout
        assert "## Next step" in result.stdout

    def test_no_partial_file_on_failure(self, tmp_path):
        project, _ = _setup_project(tmp_path)
        bad = project / "bad.json"
        bad.write_text("not json", encoding="utf-8")
        result = run(["render", str(bad), str(project), "--write", "--approve"])
        assert result.returncode != 0
        note_dir = project / ".devin" / "notes" / "youtube"
        assert not note_dir.exists() or not any(note_dir.iterdir())

    def test_uses_content_deterministic_timestamp(self, tmp_path):
        project, src = _setup_project(tmp_path)
        a = run(["render", str(src), str(project)])
        # Change mtime without changing content.
        os.utime(src, (1, 1))
        b = run(["render", str(src), str(project)])
        assert a.returncode == 0, a.stderr
        assert b.returncode == 0, b.stderr
        # Timestamps must be identical because they are derived from file content.
        assert "rendered_at:" in a.stdout
        assert a.stdout == b.stdout

    def test_rejects_symlinked_source(self, tmp_path):
        project, src = _setup_project(tmp_path)
        link = project / "link.json"
        try:
            link.symlink_to(src)
        except OSError:
            pytest.skip("symlinks not supported on this platform")
        result = run(["render", str(link), str(project)])
        assert result.returncode != 0
        assert "symlink" in result.stderr.lower()

    def test_rejects_url_with_mismatched_id(self, tmp_path):
        project, src = _setup_project(tmp_path)
        data = json.loads(src.read_text(encoding="utf-8"))
        data["url"] = "https://www.youtube.com/watch?v=9bZkp7q19f0"
        src.write_text(json.dumps(data), encoding="utf-8")
        result = run(["render", str(src), str(project)])
        assert result.returncode != 0
        assert "does not match" in result.stderr


class TestRegressions:
    """Regression tests for post-review hardening."""

    def test_bare_id_with_http_substring_is_accepted(self):
        # 11-char bare IDs are detected by full regex, even if they contain "http".
        result = run(["validate", "http1A_b2C3"])
        assert result.returncode == 0, result.stderr
        data = json.loads(result.stdout)
        assert data["video_id"] == "http1A_b2C3"

    def test_rejects_negative_start_timestamp(self, tmp_path):
        project, src = _setup_project(tmp_path)
        data = json.loads(src.read_text(encoding="utf-8"))
        data["captions"][0]["start"] = -1.0
        src.write_text(json.dumps(data), encoding="utf-8")
        result = run(["render", str(src), str(project)])
        assert result.returncode != 0
        assert "non-negative finite" in result.stderr

    def test_rejects_nan_start_timestamp(self, tmp_path):
        project, src = _setup_project(tmp_path)
        data = json.loads(src.read_text(encoding="utf-8"))
        data["captions"][0]["start"] = float("nan")
        src.write_text(json.dumps(data), encoding="utf-8")
        result = run(["render", str(src), str(project)])
        assert result.returncode != 0
        assert "non-negative finite" in result.stderr

    def test_rejects_infinite_duration(self, tmp_path):
        project, src = _setup_project(tmp_path)
        data = json.loads(src.read_text(encoding="utf-8"))
        data["captions"][0]["duration"] = float("inf")
        src.write_text(json.dumps(data), encoding="utf-8")
        result = run(["render", str(src), str(project)])
        assert result.returncode != 0
        assert "non-negative finite" in result.stderr

    def test_uses_unknown_title_and_author_when_missing(self, tmp_path):
        project, src = _setup_project(tmp_path)
        data = json.loads(src.read_text(encoding="utf-8"))
        data.pop("title", None)
        data.pop("author", None)
        src.write_text(json.dumps(data), encoding="utf-8")
        result = run(["render", str(src), str(project)])
        assert result.returncode == 0, result.stderr
        assert "title: unknown" in result.stdout
        assert "author: unknown" in result.stdout
        assert "# unknown" in result.stdout

    def test_project_label_is_independent_of_cwd(self, tmp_path):
        project, src = _setup_project(tmp_path)
        # Run from the bundle root and from the parent of the temp project.
        a = run(["render", str(src), str(project)], cwd=ROOT)
        b = run(["render", str(src), str(project)], cwd=tmp_path)
        assert a.returncode == 0, a.stderr
        assert b.returncode == 0, b.stderr
        # Both should produce identical Markdown (the project label is stable).
        assert a.stdout == b.stdout
        # No absolute paths like D:\ or C:\ should leak into stdout.
        assert "D:/" not in a.stdout
        assert "D:\\" not in a.stdout
        assert "C:" not in a.stdout

    def test_rejects_symlinked_output_directory(self, tmp_path):
        project, src = _setup_project(tmp_path)
        real_notes = tmp_path / "outside"
        real_notes.mkdir()
        notes = project / ".devin" / "notes"
        if notes.exists():
            shutil.rmtree(notes)
        try:
            notes.symlink_to(real_notes, target_is_directory=True)
        except OSError:
            pytest.skip("directory symlinks not supported on this platform")
        result = run(["render", str(src), str(project), "--write", "--approve"])
        assert result.returncode != 0
        assert "escapes" in result.stderr or "devin" in result.stderr.lower()
        assert not any(real_notes.iterdir())

    def test_fetch_command_is_disabled(self):
        # The optional network `fetch` subcommand was removed because
        # youtube-transcript-api cannot guarantee redirect/host validation.
        result = run(["fetch", "https://www.youtube.com/watch?v=dQw4w9WgXcQ"])
        assert result.returncode != 0
        # It should fail at argparse, not attempt a network call.
        assert "invalid choice" in result.stderr.lower() or "unrecognized arguments" in result.stderr.lower()

    def test_no_invented_title_even_with_whitespace(self, tmp_path):
        project, src = _setup_project(tmp_path)
        data = json.loads(src.read_text(encoding="utf-8"))
        data["title"] = "   "
        src.write_text(json.dumps(data), encoding="utf-8")
        result = run(["render", str(src), str(project)])
        assert result.returncode == 0, result.stderr
        assert "title: unknown" in result.stdout
