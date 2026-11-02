import os
import re
import subprocess
import sys

import pytest

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def read_script(name):
    path = os.path.join(REPO_ROOT, name)
    with open(path, encoding='utf-8-sig') as f:
        return f.read()


def test_export_ps1_has_security_gate():
    content = read_script('export.ps1')
    assert '[switch]$NoMask' in content
    assert '[switch]$Push' in content
    assert 'if ($Push -and $NoMask -and -not $DryRun)' in content
    assert 'aborting commit/push' in content.lower()


def test_export_ps1_runs_audit_and_pytest_on_push():
    content = read_script('export.ps1')
    assert 'audit.py' in content
    assert 'pytest -q' in content
    assert 'python' in content


def test_export_sh_has_security_gate():
    content = read_script('export.sh')
    assert 'NO_MASK=0' in content
    assert 'PUSH=0' in content
    assert 'if [[ $PUSH -eq 1 && $NO_MASK -eq 1 && $DRY_RUN -eq 0 ]]' in content
    assert 'FATAL' in content


def test_export_sh_runs_audit_and_pytest_on_push():
    content = read_script('export.sh')
    assert 'audit.py' in content
    assert 'pytest -q' in content


def test_install_ps1_has_expected_parameters():
    content = read_script('install.ps1')
    assert '[switch]$DryRun' in content
    assert '[switch]$Force' in content
    assert '[switch]$Backup' in content
    assert '[switch]$RestoreSecrets' in content
    assert '{{APPDATA}}' in content


def test_install_sh_has_expected_parameters():
    content = read_script('install.sh')
    assert '--dry-run' in content
    assert '--force' in content
    assert '--backup' in content
    assert '--restore-secrets' in content
    assert '{{APPDATA}}' in content
    assert content.startswith('#!')


def test_install_sh_skips_empty_extension_dirs():
    content = read_script('install.sh')
    assert 'mindepth 1 -type f -print -quit' in content
    assert 'is empty' in content


def test_export_ps1_has_expected_parameters():
    content = read_script('export.ps1')
    assert '[switch]$DryRun' in content
    assert '[switch]$Commit' in content
    assert '[switch]$Push' in content
    assert '[switch]$NoMask' in content
    assert 'normalize_config_paths' in content or '{{APPDATA}}' in content


def test_export_sh_has_expected_parameters():
    content = read_script('export.sh')
    assert 'DRY_RUN=0' in content
    assert 'COMMIT=0' in content
    assert 'PUSH=0' in content
    assert 'NO_MASK=0' in content
    assert 'normalize_config_paths' in content
    assert content.startswith('#!')


def _find_bash():
    """Locate a real GNU bash: (exe, path_style) or (None, None).

    On Windows CI runners, PATH 'bash' is the WSL stub in System32 (no
    distro → fails with UTF-16 error output). Prefer Git for Windows
    bash; accept PATH bash only if it answers --version like GNU bash.
    """
    candidates = []
    if sys.platform == 'win32':
        for env in ('PROGRAMFILES', 'PROGRAMFILES(X86)'):
            root = os.environ.get(env)
            if root:
                candidates.append(os.path.join(root, 'Git', 'bin', 'bash.exe'))
    candidates.append('bash')
    for exe in candidates:
        try:
            r = subprocess.run([exe, '--version'], capture_output=True,
                               text=True, timeout=10)
        except (FileNotFoundError, subprocess.TimeoutExpired, OSError):
            continue
        if r.returncode == 0 and 'GNU bash' in r.stdout:
            return exe, sys.platform == 'win32' and exe == 'bash'
    return None, False


def test_bash_scripts_pass_syntax_check():
    """If bash is available, validate syntax of install.sh and export.sh."""
    bash, needs_mount = _find_bash()
    if bash is None:
        pytest.skip('no GNU bash on this platform')
    for name in ['install.sh', 'export.sh']:
        path = os.path.join(REPO_ROOT, name)
        unix_path = path.replace('\\', '/')
        # Git bash accepts D:/path directly; a real WSL bash needs /mnt/d/path
        if needs_mount and ':' in unix_path:
            drive, rest = unix_path.split(':', 1)
            unix_path = f"/mnt/{drive.lower()}{rest}"
        result = subprocess.run(
            [bash, '-n', unix_path],
            capture_output=True,
            text=True,
            timeout=10,
        )
        assert result.returncode == 0, f"{name} has bash syntax errors: {result.stderr}"


# --- R7 export-hardening regressions ---


def test_export_sh_audit_and_pytest_run_inside_bundle_dir():
    """audit.py is cwd-dependent (walks '.', reads manifest.json) -- the
    pre-push gate must cd into BUNDLE_DIR or it audits the caller's tree."""
    content = read_script('export.sh')
    assert 'cd "$BUNDLE_DIR" && python audit.py' in content
    assert 'cd "$BUNDLE_DIR" && python -m pytest' in content


def test_export_ps1_audit_and_pytest_run_inside_bundle_dir():
    content = read_script('export.ps1')
    audit_idx = content.find('python audit.py')
    push_idx = content.rfind('Push-Location $bundleRoot', 0, audit_idx)
    assert audit_idx != -1 and push_idx != -1, (
        'audit.py must run under Push-Location $bundleRoot')


def test_export_sh_commit_stages_only_export_paths():
    """git add -A sweeps unrelated dirty files into the export commit."""
    content = read_script('export.sh')
    assert 'git add -A' not in content
    assert 'git add -- AGENTS.md' in content


def test_export_ps1_commit_stages_only_export_paths():
    content = read_script('export.ps1')
    assert 'git add -A' not in content
    assert '$exportPaths' in content
    assert 'git add -- $exportPaths' in content


def test_export_sh_mcp_mask_matches_key_names():
    """Value-only masking leaks secrets under custom keys (GITHUB_PAT,
    Authorization). The mask must also inspect key names."""
    content = read_script('export.sh')
    assert 'SECRET_KEY' in content
    for pat in ('token', 'secret', 'api[_-]?key', 'bearer', 'credential', 'pat'):
        assert pat in content


def test_export_ps1_mcp_mask_matches_key_names():
    content = read_script('export.ps1')
    assert 'token|secret|key|password|passwd|auth|bearer|credential|private|pat' in content


def test_export_sh_python_blocks_use_argv_paths():
    """Interpolating '$var' paths into python -c source mangles quotes and
    backslashes; paths must arrive via sys.argv."""
    content = read_script('export.sh')
    assert "'$config_src'" not in content
    assert "'$mcp_src'" not in content
    assert "'$mcp_dst'" not in content
    assert 'sys.argv[1]' in content


def test_export_sh_toml_mask_drops_multiline_continuations():
    """sed 's/=.*/MASKED/' leaks multiline TOML values (lines inside
    `key = [ ... ]` have no `=`). Masking must track the opener."""
    content = read_script('export.sh')
    assert "sed 's/=.*/" not in content
    assert 'skip_until' in content
    assert 'report_stale' in content


def test_export_ps1_toml_mask_drops_multiline_continuations():
    content = read_script('export.ps1')
    assert '$skipUntil' in content


def test_export_stale_entry_reporting():
    assert 'report_stale' in read_script('export.sh')
    assert 'Report-Stale' in read_script('export.ps1')


# --- R8 install-target regressions ---


def test_install_sh_resolves_appdata_on_windows():
    """Git Bash on Windows must target %APPDATA%\\devin -- the CLI does
    not read ~/.config/devin there (shadow dir bug)."""
    content = read_script('install.sh')
    assert 'MINGW*|MSYS*|CYGWIN*' in content
    assert 'cygpath' in content
    assert '${APPDATA:-}' in content


def test_install_ps1_skips_empty_extension_dirs():
    """Parity with the install.sh R6 guard."""
    content = read_script('install.ps1')
    assert 'is empty' in content
    assert '-Recurse -File' in content


def test_audit_prefers_appdata_on_windows():
    """On os.name == 'nt' the CLI reads %APPDATA%/devin; auditing the
    .config shadow instead masks real drift."""
    content = read_script('audit.py')
    assert "os.name == 'nt'" in content
    assert 'shadow config dir' in content


# --- R9 placeholder regressions ---


def test_ask_bundle_no_unexpanded_cli_placeholder():
    for f in ('skills/ask-bundle/SKILL.md',
              'skills/ask-bundle/modes/orchestration-detail.md'):
        assert '{{VALIDATED_CLI_VERSION}}' not in read_script(f)


def test_bundle_identity_has_real_values():
    import json
    d = json.load(open(os.path.join(REPO_ROOT, 'data/bundle-identity.json'),
                       encoding='utf-8'))
    for key in ('bundle_name', 'owner', 'repo', 'source_url',
                'license_holder', 'license_year'):
        assert '{{' not in str(d[key]), key + ' still a placeholder'


def test_blender_posix_ps_has_timeout():
    content = read_script('extensions/blender-operator/wrapper.py')
    ps_idx = content.find('"ps", "-axo"')
    assert 'timeout=15' in content[ps_idx:ps_idx + 400]


# --- R12 recipe regression ---

# Canonical 28-tool set, mirroring .devin/docs/TOOLS-MAP.md table.
VALID_TOOLS = {'read', 'write', 'edit', 'apply_patch', 'notebook_read',
               'notebook_edit', 'grep', 'glob', 'find_file_by_name', 'exec',
               'get_output', 'write_to_process', 'kill_shell', 'web_search',
               'webfetch', 'run_subagent', 'read_subagent', 'skill',
               'todo_write', 'ask_user_question', 'browser_preview',
               'close_browser_preview', 'request_scope', 'mcp_call_tool',
               'mcp_list_tools', 'mcp_list_servers', 'mcp_read_resource',
               'exit_plan_mode'}


def test_recipes_tools_exist():
    import json
    recipes = json.load(open(os.path.join(REPO_ROOT, 'data/recipes.json'),
                             encoding='utf-8'))['recipes']
    for name, r in recipes.items():
        for t in r.get('tools', []):
            assert t in VALID_TOOLS, f'{name}: unknown tool {t}'


def test_skill_allowed_tools_exist():
    """allowed-tools frontmatter must name real CLI tools (inline and
    YAML-list forms), across skills and agent profiles."""
    import re
    bad = []
    files = []
    skills_dir = os.path.join(REPO_ROOT, 'skills')
    for d in os.listdir(skills_dir):
        p = os.path.join(skills_dir, d, 'SKILL.md')
        if os.path.isfile(p):
            files.append((d, p))
    for agents_dir in ('agents', os.path.join('.devin', 'agents')):
        ad = os.path.join(REPO_ROOT, agents_dir)
        if not os.path.isdir(ad):
            continue
        for f in os.listdir(ad):
            p = os.path.join(ad, f)
            if f.endswith('.md') and os.path.isfile(p):
                files.append((agents_dir + '/' + f, p))
    for name, p in files:
        c = open(p, encoding='utf-8').read()
        m = re.match(r'^---\n(.*?)\n---', c, re.S)
        if not m:
            continue
        in_at = False
        for ln in m.group(1).splitlines():
            if ln.startswith('allowed-tools:'):
                in_at = True
                for t in re.split(r'[,\s]+', ln.split(':', 1)[1]):
                    t = t.strip().strip('[]')
                    if t and t not in VALID_TOOLS:
                        bad.append(f'{name}: {t}')
            elif in_at and re.match(r'^\s+- ', ln):
                t = ln.split('- ', 1)[1].split('#')[0].strip()
                if t and t not in VALID_TOOLS:
                    bad.append(f'{name}: {t}')
            elif in_at:
                in_at = False
    assert not bad, 'unknown allowed-tools: ' + ', '.join(bad)


# --- R20 dependency drift regression ---

PIP_TO_IMPORT = {'pillow': 'pil', 'opencv-python': 'cv2',
                 'opencv-python-headless': 'cv2', 'pywavelets': 'pywt',
                 'websocket-client': 'websocket', 'scrapling': 'scrapling',
                 'pywinpty': 'winpty', 'winrt-runtime': 'winrt'}


def _extension_declared_imports(ext_dir):
    """Pip names in an extension's requirements*.txt, normalized to the
    module names they install (Pillow -> PIL, pywinpty -> winpty)."""
    import glob as _glob
    import re
    reqs = set()
    for rf in _glob.glob(os.path.join(ext_dir, 'requirements*.txt')):
        for ln in open(rf, encoding='utf-8'):
            ln = ln.strip().lower()
            if ln and not ln.startswith('#'):
                name = re.split(r'[=<>!~;\[\s]', ln)[0].strip()
                name = PIP_TO_IMPORT.get(
                    name, 'winrt' if name.startswith('winrt-') else name)
                reqs.add(name)
    return reqs


def test_extension_declared_deps_used():
    """Every requirement declared by an extension must be imported by
    that extension's own Python code (catches orphaned deps)."""
    import glob as _glob
    bad = []
    for ext in sorted(os.listdir(os.path.join(REPO_ROOT, 'extensions'))):
        d = os.path.join(REPO_ROOT, 'extensions', ext)
        if not os.path.isdir(d):
            continue
        reqs = _extension_declared_imports(d)
        if not reqs:
            continue
        import ast
        imps = set()
        for pf in _glob.glob(os.path.join(d, '**', '*.py'),
                             recursive=True):
            if '.venv' in pf or '__pycache__' in pf:
                continue
            src = open(pf, encoding='utf-8', errors='ignore').read()
            try:
                tree = ast.parse(src)
            except SyntaxError:
                continue
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    imps.update(a.name.split('.')[0] for a in node.names)
                elif isinstance(node, ast.ImportFrom) and node.module:
                    imps.add(node.module.split('.')[0])
        for r in reqs:
            if r.replace('-', '_') not in {i.lower() for i in imps}:
                bad.append(f'{ext}: {r} declared but never imported')
    assert not bad, 'orphaned requirements: ' + ', '.join(bad)


# --- R21 used -> declared direction ---

# Modules supplied by a host application, not pip-provisionable for the
# bundle env: bpy/mathutils come from Blender's embedded interpreter
# (blender-operator code runs inside the Blender process).
HOST_PROVIDED = {'bpy', 'mathutils'}


def test_extension_used_deps_declared():
    """Module-scope third-party imports in extension code must be covered
    by that extension's requirements*.txt (catches undeclared hard deps).

    Function/try-scope imports are lazy optionals and exempt. Module roots
    resolvable anywhere under extensions/ are internal (the sanctioned
    cross-extension sys.path pattern); test files are exempt since the
    repo test env provides their deps.
    """
    import ast
    import sys as _sys
    internal = ({m.lower() for m in _sys.stdlib_module_names}
                | set(_sys.builtin_module_names))
    ext_root = os.path.join(REPO_ROOT, 'extensions')
    ext_modules = set()
    for r, ds, fs in os.walk(ext_root):
        ds[:] = [x for x in ds
                 if x not in ('.venv', '__pycache__', 'node_modules')]
        ext_modules.update(x.lower() for x in ds)
        ext_modules.update(os.path.splitext(f)[0].lower() for f in fs
                           if f.endswith('.py'))
    bad = []
    for ext in sorted(os.listdir(ext_root)):
        d = os.path.join(ext_root, ext)
        if not os.path.isdir(d):
            continue
        declared = _extension_declared_imports(d)
        for r, ds, fs in os.walk(d):
            ds[:] = [x for x in ds if x not in (
                '.venv', '__pycache__', 'node_modules', 'tests', 'test')]
            for f in fs:
                if (not f.endswith('.py') or f.startswith('test_')
                        or f.endswith('_test.py')):
                    continue
                pf = os.path.join(r, f)
                try:
                    tree = ast.parse(
                        open(pf, encoding='utf-8').read())
                except SyntaxError:
                    bad.append(f'{ext}: {os.path.basename(pf)} syntax error')
                    continue
                mods = set()
                for node in tree.body:
                    if isinstance(node, ast.Import):
                        mods.update(a.name.split('.')[0].lower()
                                    for a in node.names)
                    elif (isinstance(node, ast.ImportFrom)
                          and node.level == 0 and node.module):
                        mods.add(node.module.split('.')[0].lower())
                for m in mods - internal - ext_modules - HOST_PROVIDED:
                    if m != 'pytest' and m not in declared:
                        bad.append(f'{ext}: {m} imported by '
                                   f'{os.path.basename(pf)} but undeclared')
    assert not bad, 'undeclared hard dependencies: ' + ', '.join(bad)


# --- R13 hook import-boundary regression (Nx-style module boundaries) ---


def test_scripts_import_boundary():
    """scripts/*.py must not import third-party pip modules.

    Allowed non-stdlib imports: in-dir siblings (_hookrun) and the
    documented laya-guard -> extensions/laya-tools exception.
    """
    import ast
    import sys as _sys
    stdlib = set(_sys.stdlib_module_names)
    siblings = {os.path.basename(f)[:-3] for f in os.listdir(
        os.path.join(REPO_ROOT, 'scripts')) if f.endswith('.py')}
    exceptions = {'laya-guard.py': {'decision_contract', 'laya_client'}}
    viol = []
    script_files = [os.path.join(REPO_ROOT, 'scripts', f) for f in
                    os.listdir(os.path.join(REPO_ROOT, 'scripts'))
                    if f.endswith('.py')]
    for f in script_files:
        base = os.path.basename(f)
        tree = ast.parse(open(f, encoding='utf-8').read())
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                mods = [a.name.split('.')[0] for a in node.names]
            elif isinstance(node, ast.ImportFrom):
                mods = [(node.module or '').split('.')[0]]
            else:
                continue
            for m in mods:
                if not m or m in stdlib or m in siblings:
                    continue
                if m in exceptions.get(base, set()):
                    continue
                viol.append((base, m))
    assert not viol, f'hook boundary violations: {viol}'
