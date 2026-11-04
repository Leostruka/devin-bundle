"""Static assertions for install.ps1 edge-audit fixes (issues 20, 27, 35, 41).

PowerShell is not guaranteed in the test environment, so these tests verify
the script text matches the fixed behavior, in the same style as
tests/validation/test_install_export_scripts.py.
"""
import os
import re

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def read_install():
    with open(os.path.join(REPO_ROOT, 'install.ps1'), encoding='utf-8-sig') as f:
        return f.read()


# Issue 20: __pycache__ / *.pyc never shipped to install targets.

def test_skills_copy_excludes_pycache():
    content = read_install()
    # skills install must pass an exclude regex covering __pycache__ and .pyc
    m = re.search(r'Install-SkillDir[^\n]*skillsDst[^\n]*-exclude\s+\'([^\']+)\'', content)
    assert m, 'skills Install-SkillDir call must pass -exclude'
    assert '__pycache__' in m.group(1)
    assert '.pyc' in m.group(1) or 'pyc' in m.group(1)


def test_extensions_copy_excludes_pycache():
    content = read_install()
    m = re.search(r'Install-SkillDir[^\n]*extDst[^\n]*-exclude\s+\'([^\']+)\'', content)
    assert m, 'extensions Install-SkillDir call must pass -exclude'
    assert '__pycache__' in m.group(1)
    assert 'pyc' in m.group(1)


# Issue 27: render-user-hooks.py output is captured, not piped to Out-Null.

def test_render_hooks_output_captured():
    content = read_install()
    assert re.search(r'\$renderOut\s*=\s*&\s+python\s+\$renderHooks[^\n]*2>&1', content)
    # the render invocation must not be silenced
    render_line = [l for l in content.splitlines() if '& python $renderHooks' in l]
    assert render_line, 'render-user-hooks invocation missing'
    for line in render_line:
        assert 'Out-Null' not in line


def test_render_hooks_failure_reports_exit_and_output():
    content = read_install()
    assert 'render-user-hooks.py failed (exit $LASTEXITCODE)' in content
    assert 'Select-Object -Last 5' in content


# Issue 35: AGENTS.md case-variant dedup enumerates real dir entries.

def test_agents_md_dedup_enumerates_variants():
    content = read_install()
    assert "Get-ChildItem $dir -File" in content
    assert "-ieq 'agents.md'" in content
    assert "-cne 'AGENTS.md'" in content


def test_agents_md_dedup_removes_variants_on_all_fs():
    content = read_install()
    # variant removal must not be gated behind Test-CaseSensitive only;
    # the removal loop appears before the case-sensitivity warning path
    assert 'Remove-Item $v.FullName -Force' in content
    assert 'case-insensitive FS' in content  # warn path retained


# Issue 41: extension venv drift revalidation via deps marker.

def test_venv_deps_marker_written_after_pip_install():
    content = read_install()
    assert '.deps.sha256' in content
    assert re.search(r'Set-Content[^\n]*\.deps\.sha256[^\n]*Get-FileHash256\s+\$extReq', content)


def test_venv_revalidation_checks_missing_marker_and_drift():
    content = read_install()
    assert '.venv missing' in content
    assert 'no deps marker' in content
    assert 'requirements.txt changed since venv build' in content
    assert 'venv deps verified' in content


def test_venv_revalidation_is_fail_soft():
    content = read_install()
    # drift paths warn only - nothing throws or aborts the install
    start = content.find('venv drift revalidation')
    end = content.find('--- 8b.', start)
    assert start != -1 and end != -1
    section = content[start:end]
    assert 'throw' not in section
    assert '$LASTEXITCODE' not in section
