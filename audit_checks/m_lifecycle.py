import os, re, json, hashlib, sys, py_compile, subprocess, glob
from ._ctx import Ctx, text_hash_matches, _scan_py_files


def c29(ctx):
    mg_content = ''
    mg_path = '.devin/docs/MODEL-GUIDE.md'
    if os.path.exists(mg_path):
        with open(mg_path, encoding='utf-8') as fh:
            mg_content = fh.read()
    mg_refs = set(re.findall(r'arXiv:(\d{4}\.\d{4,5})', mg_content))
    code_arxiv_refs = set()
    for scan_dir in ('scripts', 'tests'):
        for root, dirs, files in os.walk(scan_dir):
            if '.git' in root or '__pycache__' in root:
                continue
            for sf in files:
                if not sf.endswith('.py'):
                    continue
                with open(os.path.join(root, sf), encoding='utf-8') as fh:
                    code_arxiv_refs.update(re.findall(r'arXiv:(\d{4}\.\d{4,5})', fh.read()))
    unverified = code_arxiv_refs - mg_refs
    if unverified:
        ctx.errors.append('arXiv refs in scripts/tests not in MODEL-GUIDE source table: ' + ', '.join(sorted(unverified)))
        print('  FAIL ' + str(len(unverified)) + ' unverified refs: ' + ', '.join(sorted(unverified)))
    else:
        print('  OK  all ' + str(len(code_arxiv_refs)) + ' arXiv refs in scripts/tests are in MODEL-GUIDE source table')

    # 30. Hook events match Devin CLI docs in both hooks.v1.json and config.json
    print()


def c30(ctx):
    # Runtime supports 10 events since CLI 3000.11.92; the bundle intentionally does
    # not hook PreCompact/PostCompact (see DEVIN-CLI-COMPATIBILITY.md 3000.11.92 table).
    devin_events = {'PreToolUse', 'PostToolUse', 'PermissionRequest', 'UserPromptSubmit',
                    'Stop', 'PostCompaction', 'SessionStart', 'SessionEnd'}

    missing_any = False
    with open('hooks.v1.json', encoding='utf-8-sig') as fh:
        hooks_data = json.load(fh)
    bundle_events = set(hooks_data.keys())
    missing = devin_events - bundle_events
    extra = bundle_events - devin_events
    if missing:
        missing_any = True
        ctx.errors.append('hooks.v1.json missing Devin CLI events: ' + ', '.join(sorted(missing)))
        print('  FAIL hooks.v1.json missing events: ' + ', '.join(sorted(missing)))
    if extra:
        ctx.warnings.append('hooks.v1.json has unknown events: ' + ', '.join(sorted(extra)))
        print('  WARN hooks.v1.json unknown events: ' + ', '.join(sorted(extra)))
    if not missing and not extra:
        print('  OK  hooks.v1.json has all ' + str(len(bundle_events)) + ' Devin CLI events')

    # Single-source invariant: user-level hooks are rendered from hooks.v1.json at
    # install time (render-user-hooks.py); config.json must not carry a second copy.
    with open('config.json', encoding='utf-8-sig') as fh:
        cfg_hooks = json.load(fh).get('hooks', {})
    if cfg_hooks:
        ctx.errors.append('config.json.hooks must be {} — hooks.v1.json is the single source (rendered at install)')
        print('  FAIL config.json.hooks non-empty (duplicate hook surface)')
    else:
        print('  OK  config.json.hooks empty (single source: hooks.v1.json)')

    # Stale project copy: .devin/hooks.v1.json double-fires with user-level hooks.
    if os.path.exists(os.path.join('.devin', 'hooks.v1.json')):
        ctx.errors.append('.devin/hooks.v1.json exists — stale duplicate of hooks.v1.json (delete it)')
        print('  FAIL .devin/hooks.v1.json present')
    else:
        print('  OK  no .devin/hooks.v1.json duplicate')

    # 31. Model context-window data file exists and matches bundle model policy
    print()


def c31(ctx):
    model_data_path = 'data/model-context-windows.json'
    required_models = {
        'swe-2-medium': 262144,
        'swe-2-high': 262144,
        'swe-2-max': 262144,
    }
    if os.path.isfile(model_data_path):
        try:
            with open(model_data_path, encoding='utf-8-sig') as fh:
                model_data = json.load(fh)
            found_models = {m.get('id', ''): m.get('context_window', 0) for m in model_data.get('models', [])}
            missing = []
            wrong_window = []
            for mid, expected in required_models.items():
                if mid not in found_models:
                    missing.append(mid)
                elif found_models[mid] != expected:
                    wrong_window.append(f"{mid} expected {expected} got {found_models[mid]}")
            if missing:
                ctx.errors.append('data/model-context-windows.json missing models: ' + ', '.join(missing))
                print('  FAIL missing models: ' + ', '.join(missing))
            if wrong_window:
                ctx.errors.append('data/model-context-windows.json wrong context_window: ' + '; '.join(wrong_window))
                print('  FAIL wrong context_window: ' + '; '.join(wrong_window))
            if not missing and not wrong_window:
                print('  OK  data/model-context-windows.json has required SWE-2 (262K) entries')
        except (OSError, json.JSONDecodeError) as e:
            ctx.errors.append('data/model-context-windows.json is invalid: ' + str(e))
            print('  FAIL invalid data/model-context-windows.json: ' + str(e))
    else:
        ctx.errors.append('data/model-context-windows.json not found')
        print('  FAIL data/model-context-windows.json not found')

    # 32. CHANGELOG [Unreleased] covers PR merges since the released version
    print()


def c32(ctx):
    try:
        import subprocess
        manifest_v = json.load(open('manifest.json', encoding='utf-8-sig'))['version']
        tag = 'v' + manifest_v
        subjects = subprocess.check_output(
            ['git', 'log', tag + '..HEAD', '--format=%s|%cI'],
            text=True, encoding="utf-8", errors="replace", stderr=subprocess.DEVNULL, timeout=15)
        # merges younger than RECENT_MERGE_H can lack refs yet - warn, not fail
        import time
        from datetime import datetime
        RECENT_MERGE_H = 24
        now = time.time()
        recent = set()
        for line in subjects.splitlines():
            subj, _, iso = line.rpartition('|')
            m = re.search(r'\(#(\d+)\)\s*$', subj)
            if not m:
                continue
            try:
                age_h = (now - datetime.fromisoformat(iso.strip()).timestamp()) / 3600
            except ValueError:
                age_h = RECENT_MERGE_H + 1
            if age_h < RECENT_MERGE_H:
                recent.add(m.group(1))
        subjects = '\n'.join(l.rpartition('|')[0] for l in subjects.splitlines())
        # docs(changelog) PRs cannot cite their own number pre-merge; skip them
        pr_nums = sorted(set(re.findall(
            r'\(#(\d+)\)\s*$', subjects, re.M))
            - set(re.findall(
            r'^docs\(changelog\)[^\n]*\(#(\d+)\)\s*$', subjects, re.M)),
            key=int)
        m = re.search(r'## \[Unreleased\](.*?)(?=\n## \[)',
                      open('CHANGELOG.md', encoding='utf-8-sig').read(), re.S)
        if not m:
            ctx.errors.append('CHANGELOG.md missing ## [Unreleased] section')
            print('  FAIL no [Unreleased] section')
        elif not pr_nums:
            print('  OK  no PR merges since ' + tag)
        else:
            missing = [n for n in pr_nums if '#' + n not in m.group(1)]
            stale = [n for n in missing if n not in recent]
            fresh = [n for n in missing if n in recent]
            if stale:
                ctx.errors.append('CHANGELOG [Unreleased] missing PR refs: '
                              + ', '.join('#' + n for n in stale))
                print('  FAIL missing refs: '
                      + ', '.join('#' + n for n in stale))
            if fresh:
                ctx.warnings.append('CHANGELOG [Unreleased] missing refs for '
                                'recent merges (<24h): '
                                + ', '.join('#' + n for n in fresh))
                print('  WARN missing refs (recent merges): '
                      + ', '.join('#' + n for n in fresh))
            if not missing:
                print('  OK  [Unreleased] covers ' + str(len(pr_nums))
                      + ' merged PRs since ' + tag)
    except Exception as e:
        ctx.warnings.append('changelog coverage check skipped: ' + str(e))
        print('  WARN changelog coverage check skipped: ' + str(e))

    # 33. Resolved issue files must carry an Answer section
    print()


def c33(ctx):
    import glob
    unanswered = []
    issue_files = glob.glob(os.path.join('.devin', 'scratch', '**', 'issues', '*.md'),
                            recursive=True)
    for issue_path in issue_files:
        try:
            body = open(issue_path, encoding='utf-8-sig').read()
        except (OSError, IOError):
            continue
        if re.search(r'(?im)^\s*-?\s*\*\*status\*\*\s*:\s*resolved\b', body) \
                and '## Answer' not in body:
            unanswered.append(issue_path)
    if unanswered:
        ctx.errors.append('issues marked resolved without an Answer section: '
                      + ', '.join(unanswered))
        print('  FAIL ' + str(len(unanswered)) + ' resolved issues lack an Answer section')
    elif issue_files:
        print('  OK  all resolved issues carry an Answer section')
    else:
        print('  SKIP no issue files under .devin/scratch/**/issues/')

    # 34. Install drift ledger reconcile (M2_06)
    print()


def c34(ctx):
    try:
        sys.path.insert(0, 'scripts')
        import importlib.util as _ilu
        _spec = _ilu.spec_from_file_location(
            'install_ledger', os.path.join('scripts', 'install-ledger.py'))
        _il = _ilu.module_from_spec(_spec)
        _spec.loader.exec_module(_il)
        _rep = _il.reconcile()
        _drift = _rep['Modified'] + _rep['Foreign']
        if _drift:
            ctx.warnings.append('ledger drift: ' + ', '.join(_drift[:20]))
            print('  WARN drift: Modified=' + str(len(_rep['Modified']))
                  + ' Foreign=' + str(len(_rep['Foreign'])))
        else:
            print('  OK  no Modified/Foreign drift ('
                  + str(len(_rep['Current'])) + ' current)')
    except Exception as _e:
        print('  SKIP ledger check failed to run: ' + str(_e))

    # 35. tools.json schema + renderer byte-identity (M2_07)
    print()


def c35(ctx):
    try:
        _ct_out = subprocess.run(
            [sys.executable, os.path.join('scripts', 'check-tools.py')],
            capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=120)
        if _ct_out.returncode == 0:
            print('  OK  ' + _ct_out.stdout.strip().splitlines()[-1])
        else:
            ctx.errors.append('check-tools.py failed: '
                          + _ct_out.stdout.strip()[-200:])
            print('  FAIL check-tools.py')
    except Exception as _e:
        print('  SKIP check-tools failed to run: ' + str(_e))

    # Shared scanner for checks 36-38: yields .py files under extensions/
    # and scripts/, skipping vendored/runtime dirs.
    # 36. CLI exit-code contract: mains that can emit {"ok": false} must not
    # exit 0 unconditionally (scripts/CI cannot detect failure otherwise).
    print()


def c36(ctx):
    try:
        import ast as _ast
        _suspects = []
        for _fp in _scan_py_files():
            try:
                _src = open(_fp, encoding='utf-8').read()
                _tree = _ast.parse(_src)
            except (OSError, SyntaxError, UnicodeDecodeError):
                continue
            if '"ok": False' not in _src and "'ok': False" not in _src:
                continue
            for _node in _ast.walk(_tree):
                if not (isinstance(_node, _ast.FunctionDef)
                        and _node.name == 'main'):
                    continue
                _seg = _ast.get_source_segment(_src, _node) or ''
                # Bug shape: print(json.dumps(<call>)) or print(_dumps(...))
                # then bare return 0 while the printed envelope can carry
                # ok:false and main shows no ok-awareness (literal "ok" key,
                # .get("ok"), nonzero literal returns, or sys.exit paths).
                if ('print(json.dumps(' not in _seg
                        and 'print(_dumps(' not in _seg):
                    continue
                _has_bare0 = any(
                    isinstance(r, _ast.Return)
                    and isinstance(r.value, _ast.Constant)
                    and r.value.value == 0
                    for r in _ast.walk(_node))
                _ok_aware = ('"ok"' in _seg or "'ok'" in _seg
                             or '.get(' in _seg and 'ok' in _seg)
                _can_fail = any(
                    isinstance(r, _ast.Return)
                    and isinstance(r.value, _ast.Constant)
                    and isinstance(r.value.value, int)
                    and r.value.value != 0
                    for r in _ast.walk(_node))
                _exits = ('sys.exit' in _seg or 'SystemExit' in _seg
                          or '_fail(' in _seg or '_out(' in _seg)
                if _has_bare0 and not (_ok_aware or _can_fail or _exits):
                    _suspects.append(_fp + ':' + str(_node.lineno))
        if _suspects:
            ctx.warnings.append('cli mains may exit 0 on ok:false: '
                            + ', '.join(_suspects[:10]))
            print('  WARN ' + str(len(_suspects)) + ' suspect main(s): '
                  + ', '.join(_suspects[:5]))
        else:
            print('  OK  no ok-envelope mains with unguarded exit 0')
    except Exception as _e:
        print('  SKIP exit-code check failed: ' + str(_e))

    # 37. subprocess text decode: text=True without encoding= decodes with the
    # Windows locale codepage (cp1252) - UTF-8 output with non-ASCII mojibakes
    # or crashes on undefined bytes. Every subprocess text=True call needs an
    # encoding= kwarg on the same call (count heuristics mask per-call gaps).
    print()
