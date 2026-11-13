"""CLI-CONTRACT.md must keep naming the real envelope machinery: the
v2 fields, every shared per-dir envelope module on disk, and the
documented protocol/bare-array exclusions that must exist as files.

Companion to tests/test_envelope_contract_v2.py (runtime probes) -
this one pins the document to the code it describes.
"""
import os
import re

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
DOC = os.path.join(ROOT, ".devin", "docs", "CLI-CONTRACT.md")


def _doc():
    return open(DOC, encoding="utf-8").read()


def test_doc_names_envelope_v2_fields():
    doc = _doc()
    for field in ("api_version", "answered_by", "meta"):
        assert field in doc, f"CLI-CONTRACT.md lost field mention: {field}"


def test_doc_named_shared_modules_exist():
    doc = _doc()
    named = set(re.findall(r"`([a-z\-]+/[a-z_]*envelope\.py)`", doc))
    assert named, "doc names no shared envelope modules"
    missing = {n for n in named
               if not os.path.isfile(os.path.join(ROOT, "extensions", n))
               and not os.path.isfile(os.path.join(ROOT, n))}
    assert not missing, f"doc names modules absent on disk: {sorted(missing)}"


def test_doc_exclusion_files_exist():
    doc = _doc()
    for path in re.findall(r"`((?:computer-use|system-control)/[a-z_]+\.py)`",
                           doc):
        p = os.path.join(ROOT, "extensions", path)
        assert os.path.isfile(p), f"excluded file missing: {path}"
