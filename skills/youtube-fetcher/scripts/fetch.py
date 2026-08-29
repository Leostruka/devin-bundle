#!/usr/bin/env python3
"""youtube-fetcher — Devin-native YouTube transcript/metadata capture.

Conceptually adapted from JimmySadek/youtube-fetcher-to-markdown (MIT) after
source review. No code, prompts, or templates are copied from the upstream
project. The core `validate` and `render` paths use only the Python standard
library. The skill never calls the network and never installs `youtube-
transcript-api`, `requests`, `yt-dlp`, or Whisper. Captions and metadata must
be supplied by a provider or fixture JSON.

Usage:
    python fetch.py validate <url-or-id>
    python fetch.py render <source.json> [project] [--write] [--approve] [--overwrite]
"""
import argparse
import hashlib
import json
import math
import os
import re
import sys
import time
from pathlib import Path
from urllib.parse import parse_qs, urlparse

SCHEMA_VERSION = "1.0.0"
NOTE_SUBDIR = Path("notes/youtube")
MAX_INPUT_BYTES = 50 * 1024 * 1024
MAX_OUTPUT_BYTES = 100 * 1024 * 1024
MAX_CAPTIONS = 100_000
MAX_URL_LENGTH = 2048
ALLOWED_HOSTS = {
    "www.youtube.com",
    "youtube.com",
    "youtu.be",
    "www.youtu.be",
    "m.youtube.com",
    "music.youtube.com",
}
VIDEO_ID_RE = re.compile(r"^[A-Za-z0-9_-]{11}$")


def err(msg):
    sys.stderr.write(str(msg) + "\n")


def emit_json(data):
    text = json.dumps(data, sort_keys=True, indent=2, ensure_ascii=False)
    sys.stdout.buffer.write((text + "\n").encode("utf-8"))


def emit_text(text):
    sys.stdout.buffer.write((text + "\n").encode("utf-8"))


def content_timestamp(source_sha256):
    """Return a content-deterministic UTC ISO 8601 timestamp.

    The first 8 hex characters of the source SHA-256 are interpreted as a Unix
    timestamp. This makes repeated runs byte-identical for unchanged inputs
    while avoiding dependence on file mtime or wall clock.
    """
    seconds = int(source_sha256[:8], 16)
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(seconds))


def _format_timestamp(seconds):
    """Render seconds as [HH:MM:SS.sss].

    Callers must have already validated that the value is finite and
    non-negative; this function does not clamp or invent timestamps.
    """
    seconds = float(seconds)
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = seconds % 60
    return f"{hours:02d}:{minutes:02d}:{secs:06.3f}"


def _normalize_netloc(netloc):
    """Strip username/password and port from a netloc string."""
    netloc = netloc.split("@")[-1]
    if ":" in netloc:
        # IPv6 brackets may contain colons; strip only trailing port if plain.
        if not netloc.endswith(")"):
            netloc = netloc.rsplit(":", 1)[0]
    return netloc.lower()


def _is_allowed_host(netloc):
    return _normalize_netloc(netloc) in ALLOWED_HOSTS


def extract_video_id(url_or_id):
    """Validate a YouTube URL or bare ID and return a canonical 11-char ID."""
    text = (url_or_id or "").strip()
    if not text:
        raise ValueError("empty URL or ID")
    # Detect bare IDs solely by full regex match, including IDs that contain
    # "http" or other URL-like substrings.
    if VIDEO_ID_RE.fullmatch(text):
        return text

    if len(text) > MAX_URL_LENGTH:
        raise ValueError("URL exceeds maximum length")
    parsed = urlparse(text)
    if parsed.scheme not in ("http", "https"):
        raise ValueError(f"unsupported URL scheme: {parsed.scheme}")
    if not _is_allowed_host(parsed.netloc):
        raise ValueError(f"unsupported host: {parsed.netloc}")

    # youtu.be/<id>
    if _normalize_netloc(parsed.netloc).endswith("youtu.be"):
        path = parsed.path.strip("/")
        parts = [p for p in path.split("/") if p]
        if parts and VIDEO_ID_RE.match(parts[0]):
            return parts[0]
        raise ValueError(f"no video ID in short URL: {text}")

    # youtube.com/watch?v=<id>
    if parsed.path in ("", "/", "/watch") or parsed.path.startswith("/watch"):
        query = parse_qs(parsed.query)
        v = query.get("v", [""])[0]
        if VIDEO_ID_RE.match(v):
            return v
        # Fragment fallback.
        if parsed.fragment and not v:
            frag = parse_qs(parsed.fragment)
            v = frag.get("v", [""])[0]
            if VIDEO_ID_RE.match(v):
                return v

    # youtube.com/shorts/<id>, /embed/<id>, /v/<id>, /watch/<id>
    for prefix in ("/shorts/", "/embed/", "/v/", "/watch/"):
        if parsed.path.startswith(prefix):
            parts = [p for p in parsed.path[len(prefix):].split("/") if p]
            if parts and VIDEO_ID_RE.match(parts[0]):
                return parts[0]

    raise ValueError(f"no supported YouTube ID in URL: {text}")


def canonical_url(video_id):
    return f"https://www.youtube.com/watch?v={video_id}"


def locate_devin(project):
    """Return (project_root, devin_dir) for a project or .devin path."""
    p = Path(project).expanduser().resolve()
    if p.name == ".devin" and p.is_dir():
        if p.is_symlink():
            raise ValueError(f"symlinked .devin not allowed: {project}")
        return p.parent.resolve(), p.resolve()
    devin = p / ".devin"
    if devin.is_dir() and not devin.is_symlink():
        return p.resolve(), devin.resolve()
    raise FileNotFoundError(f"no .devin directory in {project}")


def project_label(project):
    """Return a stable, cwd-independent project label that never leaks absolute paths."""
    return project.resolve().name


def _safe_note_path(devin, video_id, suffix):
    out = (devin / NOTE_SUBDIR).resolve()
    try:
        out.relative_to(devin.resolve())
    except ValueError:
        raise RuntimeError("output path escapes .devin")
    return out / f"{video_id}{suffix}"


def _read_json_source(path):
    """Read and validate a provider/fixture JSON file."""
    p = Path(path)
    if not p.is_file():
        raise FileNotFoundError(f"source not found: {path}")
    if p.is_symlink():
        raise ValueError(f"symlinked source not allowed: {path}")
    size = p.stat().st_size
    if size > MAX_INPUT_BYTES:
        raise ValueError(f"source JSON exceeds {MAX_INPUT_BYTES} bytes")
    raw = p.read_bytes()
    sha = hashlib.sha256(raw).hexdigest()
    data = json.loads(raw.decode("utf-8-sig"))
    if not isinstance(data, dict):
        raise ValueError("source JSON must be a single object")
    return data, sha


def _validate_source(data):
    """Normalize and validate caption+metadata JSON."""
    video_id = data.get("video_id", "")
    if not VIDEO_ID_RE.match(video_id):
        raise ValueError(f"invalid or missing video_id: {video_id}")
    data["video_id"] = video_id

    url = data.get("url", "")
    if url:
        # Validate that the URL matches the allowlist and the video ID.
        try:
            url_id = extract_video_id(url)
            if url_id != video_id:
                raise ValueError(f"URL video ID {url_id} does not match {video_id}")
        except ValueError as e:
            raise ValueError(f"invalid url in source: {e}")
    else:
        data["url"] = canonical_url(video_id)

    captions = data.get("captions")
    if not isinstance(captions, list):
        raise ValueError("source JSON must contain a 'captions' list")
    if len(captions) == 0:
        raise ValueError("no captions in source JSON; will not fabricate transcript")
    if len(captions) > MAX_CAPTIONS:
        raise ValueError(f"caption count {len(captions)} exceeds limit {MAX_CAPTIONS}")

    normalized = []
    for i, c in enumerate(captions):
        if not isinstance(c, dict):
            raise ValueError(f"caption[{i}] is not an object")
        text = c.get("text")
        if text is None or not isinstance(text, str):
            raise ValueError(f"caption[{i}] missing 'text' string")
        start = c.get("start")
        if start is None:
            raise ValueError(f"caption[{i}] missing 'start'")
        try:
            start = float(start)
        except (TypeError, ValueError):
            raise ValueError(f"caption[{i}] 'start' is not numeric")
        if not math.isfinite(start) or start < 0:
            raise ValueError(f"caption[{i}] 'start' must be a non-negative finite number")
        dur = c.get("duration")
        if dur is not None:
            try:
                dur = float(dur)
            except (TypeError, ValueError):
                raise ValueError(f"caption[{i}] 'duration' is not numeric")
            if not math.isfinite(dur) or dur < 0:
                raise ValueError(f"caption[{i}] 'duration' must be a non-negative finite number")
        normalized.append({"text": text, "start": start, "duration": dur, "_idx": i})

    # Sort by start time, preserving original order for ties.
    normalized.sort(key=lambda c: (c["start"], c["_idx"]))
    data["captions"] = [
        {"text": c["text"], "start": c["start"], "duration": c["duration"]}
        for c in normalized
    ]

    # Truthful language and caption type: do not invent.
    data.setdefault("language", "unknown")
    data.setdefault("caption_type", "unknown")
    data.setdefault("title", "")
    data.setdefault("author", "")
    data.setdefault("duration", 0)
    return data


def _render_markdown(data, project_str, source_sha256):
    """Render deterministic Markdown from validated caption+metadata JSON."""
    rendered_at = content_timestamp(source_sha256)
    video_id = data["video_id"]
    url = data["url"]
    title = (data.get("title") or "").strip() or "unknown"
    author = (data.get("author") or "").strip() or "unknown"
    duration = data.get("duration") or 0
    language = data.get("language") or "unknown"
    caption_type = data.get("caption_type") or "unknown"
    captions = data["captions"]

    lines = [
        "---",
        f"video_id: {video_id}",
        f"url: {url}",
        f"title: {title}",
        f"author: {author}",
        f"duration: {duration}",
        f"language: {language}",
        f"caption_type: {caption_type}",
        f"caption_count: {len(captions)}",
        f"source_sha256: {source_sha256}",
        f"rendered_at: {rendered_at}",
        f"schema_version: {SCHEMA_VERSION}",
        "---",
        "",
        f"# {title}",
        "",
        "## Metadata",
        "",
        "| Field | Value |",
        "|---|---|",
        f"| video_id | `{video_id}` |",
        f"| url | {url} |",
        f"| title | {title} |",
        f"| author | {author} |",
        f"| duration (s) | {duration} |",
        f"| language | {language} |",
        f"| caption_type | {caption_type} |",
        f"| caption_count | {len(captions)} |",
        "",
        "## Raw transcript",
        "",
        "> This section contains the raw captions exactly as supplied. No summary or inference is included.",
        "",
        "| Timestamp | Text |",
        "|---|---|",
    ]
    for c in captions:
        ts = _format_timestamp(c["start"])
        # Pipe characters would break the Markdown table; escape them.
        text = c["text"].replace("|", "\\|")
        text = text.replace("\n", " ")
        lines.append(f"| [{ts}] | {text} |")

    lines.extend([
        "",
        "## Provenance",
        "",
        f"- Source JSON SHA-256: `{source_sha256}`",
        f"- Rendered at: {rendered_at}",
        f"- Caption language: {language}",
        f"- Caption type: {caption_type}",
        f"- Project: `{project_str}`",
        "",
        "## Next step",
        "",
        "After reviewing the raw transcript, pass this note to `structured-knowledge-extraction` for entity, relation, and evidence extraction. Keep all summaries and inferences out of this file.",
    ])
    return "\n".join(lines) + "\n"


def _in_devin(path, devin):
    """Return True if a resolved path is inside or equal to devin."""
    try:
        path.resolve().relative_to(devin.resolve())
        return True
    except (ValueError, OSError):
        return False


def _atomic_write(path, text, overwrite, devin):
    """Write a note atomically, preserving existing files unless approved.

    Containment is checked before and immediately before the final rename.
    Any symlink component that would escape `.devin` causes a failure. On any
    failure the temporary file is removed and the target is never left partial.
    """
    devin = Path(devin).resolve()
    path = Path(path)
    if not _in_devin(path, devin):
        raise RuntimeError("output path escapes .devin")
    path = path.resolve()
    if not _in_devin(path, devin):
        raise RuntimeError("resolved output path escapes .devin")
    if path.exists() and not overwrite:
        raise FileExistsError(f"note already exists: {path}")

    parent = path.parent
    parent.mkdir(parents=True, exist_ok=True)
    if not _in_devin(parent, devin):
        raise RuntimeError("output directory escapes .devin")
    # Use a content-derived unique temp name to avoid collisions.
    tmp_name = f"{path.name}.{hashlib.sha256(text.encode('utf-8')).hexdigest()[:16]}.tmp"
    tmp = parent / tmp_name
    try:
        if not _in_devin(tmp, devin):
            raise RuntimeError("temporary file path escapes .devin")
        tmp.write_text(text, encoding="utf-8", newline="\n")
        if os.path.getsize(tmp) > MAX_OUTPUT_BYTES:
            raise ValueError(f"output exceeds {MAX_OUTPUT_BYTES} bytes")
        # Revalidate containment immediately before the replace. A symlink
        # could have been swapped in between validation and the rename.
        for candidate in (tmp, path):
            if not _in_devin(candidate, devin):
                raise RuntimeError(f"{candidate} escapes .devin")
        os.replace(tmp, path)
    except Exception:
        if tmp.exists():
            try:
                tmp.unlink()
            except OSError:
                pass
        raise


def cmd_validate(args):
    try:
        video_id = extract_video_id(args.url_or_id)
        emit_json({"valid": True, "video_id": video_id, "url": canonical_url(video_id)})
        return 0
    except ValueError as e:
        err(f"validation failed: {e}")
        return 1


def cmd_render(args):
    if args.write and not args.approve:
        err("--approve is required when using --write")
        return 1
    try:
        data, sha = _read_json_source(args.source)
        data = _validate_source(data)
        project = Path(args.project).expanduser().resolve()
        project_root, devin = locate_devin(project)
        project_str = project_label(project_root)
        md = _render_markdown(data, project_str, sha)

        if args.write:
            md_path = _safe_note_path(devin, data["video_id"], ".md")
            _atomic_write(md_path, md, overwrite=args.overwrite, devin=devin)
        emit_text(md)
        return 0
    except Exception as e:
        err(f"render failed: {e}")
        return 1


def main(argv=None):
    parser = argparse.ArgumentParser(
        description="YouTube transcript/metadata fetcher for .devin/notes/youtube/"
    )
    sub = parser.add_subparsers(dest="command", required=True)

    p_val = sub.add_parser("validate", help="validate a YouTube URL or video ID")
    p_val.add_argument("url_or_id", help="YouTube URL or 11-character video ID")

    p_render = sub.add_parser("render", help="render caption JSON to Markdown")
    p_render.add_argument("source", help="path to caption+metadata JSON")
    p_render.add_argument("project", nargs="?", default=".", help="project root (default .)")
    p_render.add_argument("--write", action="store_true", help="write the Markdown note")
    p_render.add_argument("--approve", action="store_true", help="confirm persistence")
    p_render.add_argument("--overwrite", action="store_true", help="overwrite an existing note")

    args = parser.parse_args(argv)
    if args.command == "validate":
        return cmd_validate(args)
    if args.command == "render":
        return cmd_render(args)
    return 1


if __name__ == "__main__":
    sys.exit(main())
