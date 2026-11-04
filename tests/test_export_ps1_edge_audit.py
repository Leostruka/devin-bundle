"""Static assertions for export.ps1 edge-audit fixes (issues 08, 20).

PowerShell is not guaranteed in the test environment, so these tests verify
the script text matches the fixed behavior, in the same style as
tests/validation/test_install_export_scripts.py.
"""
import os
import re

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def read_export():
    with open(os.path.join(REPO_ROOT, 'export.ps1'), encoding='utf-8-sig') as f:
        return f.read()


# Issue 08: Get-FolderHash must hash relative paths so renames are detected.

def test_folder_hash_includes_relative_path():
    content = read_export()
    m = re.search(r'function Get-FolderHash.*?\n}\n', content, re.S)
    assert m, 'Get-FolderHash not found'
    body = m.group(0)
    # hashed material must include the relative path, not content hash alone
    assert '"  ./" + $rel' in body
    assert '$base.Length' in body


def test_folder_hash_supports_exclude():
    content = read_export()
    assert re.search(r'function Get-FolderHash\(\$path,\s*\$exclude', content)
    m = re.search(r'function Get-FolderHash.*?\n}\n', content, re.S)
    assert 'notmatch $exclude' in m.group(0)


# Issue 20: __pycache__ / *.pyc excluded from exported trees.

def test_export_defines_pycache_exclude():
    content = read_export()
    assert '__pycache__' in content
    assert '.pyc' in content


def test_skills_export_uses_filtered_copy():
    content = read_export()
    assert re.search(r'\$skillExclude\s*=\s*\'[^\']*__pycache__', content)
    assert 'Copy-FilteredDir $src $dst $skillExclude' in content
    assert 'Get-FolderHash $src $skillExclude' in content


def test_dir_recursive_copy_excludes_pycache_by_default():
    content = read_export()
    m = re.search(r'function Copy-DirRecursive.*?\n}\n', content, re.S)
    assert m, 'Copy-DirRecursive not found'
    body = m.group(0)
    assert '__pycache__' in body
    assert 'Copy-FilteredDir' in body
    # plain recursive Copy-Item must not remain in the non-dry-run path
    assert 'Copy-Item $src $dst -Recurse -Force' not in body
