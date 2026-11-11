import importlib.util
import sys

sys.path.insert(0, "scripts")


def _mod():
    spec = importlib.util.spec_from_file_location(
        "check_push_green", "scripts/check-push-green.py")
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


def test_doc_path_classification():
    m = _mod()
    assert m._is_doc_path("docs/a.md")
    assert m._is_doc_path("CHANGELOG.md")
    assert m._is_doc_path(".devin/scratch/x/tasks.json")
    assert m._is_doc_path(".devin/issues/ISSUE_01.md")
    assert m._is_doc_path("skills/foo/SKILL.md")          # agent content
    assert m._is_doc_path("README.md")
    assert not m._is_doc_path("scripts/check-push-green.py")
    assert not m._is_doc_path("extensions/api-bridge/bridge.py")
    assert not m._is_doc_path(".devin/hooks/hooks.v1.json")  # runtime config
    assert not m._is_doc_path("tests/test_x.py")
    assert not m._is_doc_path("data/bundle-models.json")     # runtime data


def test_changed_paths_real_repo():
    m = _mod()
    paths = m._changed_paths(".")
    assert paths is not None and isinstance(paths, set)
