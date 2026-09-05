"""Model catalog drift detection tests.

Tests verify that bundle-cached model facts can be compared against a
`devin models list` fixture and that stale entries are reported.
"""
import sys
from pathlib import Path

ROOT = Path(__file__).parents[2]
# Allow importing scripts/ modules during tests
sys.path.insert(0, str(ROOT / "scripts"))

import model_catalog  # noqa: E402


def test_parse_devin_models_list_extracts_ids_and_windows():
    fixture = ROOT / "tests" / "fixtures" / "model-catalog" / "sample-models.txt"
    output = fixture.read_text(encoding="utf-8")
    models = model_catalog.parse_devin_models_list(output)
    ids = {m["id"] for m in models}
    assert "glm-5-2" in ids
    assert "glm-5-2-max" in ids
    assert "swe-1-7" in ids
    glm = next(m for m in models if m["id"] == "glm-5-2")
    assert glm["context_window"] == 200000


def test_detect_drift_reports_missing_bundle_models():
    bundle = [{"id": "glm-5-2", "context_window": 200000}]
    cli = [
        {"id": "glm-5-2", "context_window": 200000},
        {"id": "swe-1-7", "context_window": 262000},
    ]
    errors, warnings = model_catalog.compare_catalogs(cli, bundle)
    assert any("swe-1-7" in e and "missing from bundle" in e for e in errors)


def test_detect_drift_reports_wrong_context_window():
    bundle = [{"id": "glm-5-2", "context_window": 100000}]
    cli = [{"id": "glm-5-2", "context_window": 200000}]
    errors, warnings = model_catalog.compare_catalogs(cli, bundle)
    assert any("glm-5-2" in e and "context_window" in e for e in errors)


def test_parse_realistic_output_includes_uppercase_ids():
    fixture = ROOT / "tests" / "fixtures" / "model-catalog" / "realistic-models.txt"
    output = fixture.read_text(encoding="utf-8")
    models = model_catalog.parse_devin_models_list(output)
    ids = {m["id"] for m in models}
    assert "MODEL_GPT_5_2_LOW" in ids
    assert "claude-opus-5-medium" in ids
    assert "swe-1-7" in ids


def test_detect_drift_passes_when_synchronized():
    bundle = [{"id": "glm-5-2", "context_window": 200000}]
    cli = [{"id": "glm-5-2", "context_window": 200000}]
    errors, warnings = model_catalog.compare_catalogs(cli, bundle)
    assert not errors
