import os, re, json, hashlib, sys, py_compile, subprocess, glob
from ._ctx import Ctx, text_hash_matches, _scan_py_files


def c10b(ctx):
    mcp_schema_errors = []
    if not isinstance(ctx.mcp.get('mcpServers'), dict):
        mcp_schema_errors.append('mcpServers must be an object')
    else:
        for sname, scfg in ctx.mcp_servers.items():
            if not isinstance(scfg, dict):
                mcp_schema_errors.append(sname + ' config must be an object')
                continue
            url = scfg.get('url', '')
            transport = scfg.get('transport', '')
            if not url.startswith('https://'):
                mcp_schema_errors.append(sname + ' url must use https')
            if transport not in ('https', 'stdio'):
                mcp_schema_errors.append(sname + ' transport must be https or stdio')
            if url.startswith('https://') and transport == 'http':
                mcp_schema_errors.append(sname + ' transport http does not match https url')
    if mcp_schema_errors:
        for e in mcp_schema_errors:
            ctx.errors.append('mcp_config.json: ' + e)
            print('  FAIL ' + e)
    else:
        print('  OK  mcp_config.json schema valid')

    # mcp_count = available MCP integrations declared in bundle-integrations.json
    bund_integ = json.load(open('data/bundle-integrations.json', encoding='utf-8-sig'))
    avail_mcp = len(bund_integ.get('mcp', {}))
    if ctx.manifest.get('mcp_count') == avail_mcp:
        print('  OK  mcp_count = ' + str(avail_mcp) + ' (bundle-integrations.json)')
    else:
        ctx.errors.append('manifest mcp_count ' + str(ctx.manifest.get('mcp_count')) + ' != bundle-integrations mcp ' + str(avail_mcp))
        print('  FAIL mcp_count (expected ' + str(avail_mcp) + ')')

    # 11. .gitignore coverage
    print()


def c11(ctx):
    gi = open('.gitignore', encoding='utf-8').read()
    required_ignores = ['__pycache__', '.devin/brainstorm/', '.devin/heartbeats/', '.devin/mailboxes/', '.devin/checkpoints/', '.devin/.refine-pending']
    for pattern in required_ignores:
        if pattern in gi:
            print('  OK  ' + pattern)
        else:
            ctx.warnings.append('.gitignore missing ' + pattern)
            print('  WARN .gitignore missing ' + pattern)
    # Also check for tracked __pycache__ files (on-disk caches are normal and
    # gitignored; only versioned pollution is a problem)
    try:
        import subprocess
        tracked = [p for p in subprocess.check_output(
            ['git', 'ls-files'], text=True, encoding="utf-8", errors="replace").split() if '__pycache__' in p]
    except Exception:
        tracked = []
    if tracked:
        ctx.warnings.append('tracked __pycache__ files: ' + ', '.join(tracked))
        print('  WARN tracked __pycache__ files: ' + ', '.join(tracked))
    else:
        print('  OK  no tracked __pycache__ files')

    # 12. CI workflow
    print()


def c12(ctx):
    ci_path = '.github/workflows/ci.yml'
    if os.path.exists(ci_path):
        ci = open(ci_path, encoding='utf-8').read()
        required_steps = ['Validate JSON', 'Validate Python', 'Validate skill frontmatter', 'Check for AI signatures', 'Verify manifest sync']
        for step in required_steps:
            if step in ci:
                print('  OK  step: ' + step)
            else:
                ctx.errors.append('CI missing step: ' + step)
                print('  FAIL CI missing step: ' + step)
    else:
        ctx.errors.append('CI workflow missing')
        print('  FAIL CI workflow missing')

    # 13. Issue/PR templates
    print()


def c13(ctx):
    templates = [
        '.github/ISSUE_TEMPLATE/config.yml',
        '.github/ISSUE_TEMPLATE/bug_report.yml',
        '.github/ISSUE_TEMPLATE/feature_request.yml',
        '.github/ISSUE_TEMPLATE/skill_improvement.yml',
        '.github/PULL_REQUEST_TEMPLATE.md',
    ]
    for ctx.t in templates:
        if os.path.exists(ctx.t):
            print('  OK  ' + ctx.t)
        else:
            ctx.errors.append('Template missing: ' + ctx.t)
            print('  FAIL ' + ctx.t + ' missing')

    # 13b. GitHub governance automation files
    print()


def c13b(ctx):
    governance = [
        '.github/release.yml',
        '.github/dependabot.yml',
        '.github/workflows/pr-quality.yml',
    ]
    for ctx.t in governance:
        if os.path.exists(ctx.t):
            print('  OK  ' + ctx.t)
        else:
            ctx.errors.append('Governance file missing: ' + ctx.t)
            print('  FAIL ' + ctx.t + ' missing')

    # 14. LICENSE, SECURITY, CONTRIBUTING, CHANGELOG
    print()


def c14(ctx):
    docs = [('LICENSE', 'MIT'), ('SECURITY.md', None), ('CONTRIBUTING.md', None), ('CHANGELOG.md', None)]
    for doc, check in docs:
        if os.path.exists(doc):
            content = open(doc, encoding='utf-8').read()
            if check and check not in content:
                ctx.errors.append(doc + ' does not contain ' + check)
                print('  FAIL ' + doc + ' missing ' + check)
            elif len(content.strip()) < 100:
                ctx.warnings.append(doc + ' is too short')
                print('  WARN ' + doc + ' is too short')
            else:
                print('  OK  ' + doc)
        else:
            ctx.errors.append(doc + ' missing')
            print('  FAIL ' + doc + ' missing')

    # 15. Live vs bundle sync
    print()


def c15(ctx):
    # Auto-detect live config path: WSL/Linux ~/.config/devin, Windows %APPDATA%/devin.
    # On Windows the CLI reads %APPDATA% -- prefer it there so a stale
    # ~/.config/devin shadow copy cannot mask real drift.
    home = os.path.expanduser('~')
    appdata = os.environ.get('APPDATA', '')
    config_devin = os.path.join(home, '.config', 'devin')
    appdata_devin = os.path.join(appdata, 'devin') if appdata else ''
    if os.name == 'nt' and appdata and os.path.isdir(appdata_devin):
        ctx.live_base = appdata_devin
    elif os.path.isdir(config_devin):
        ctx.live_base = config_devin
    elif appdata_devin and os.path.isdir(appdata_devin):
        ctx.live_base = appdata_devin
    else:
        ctx.live_base = ''  # no live install found; sync checks will SKIP
    if ctx.live_base and os.path.isdir(config_devin) and os.path.isdir(appdata_devin) \
            and os.path.normcase(ctx.live_base) != os.path.normcase(config_devin):
        ctx.warnings.append('Both %APPDATA%/devin and ~/.config/devin exist; auditing ' + ctx.live_base)
        print('  WARN shadow config dir present (auditing ' + ctx.live_base + ')')
    pairs = [('AGENTS.md', 'AGENTS.md'), ('mcp_config.json', 'mcp_config.json')]
    for live_rel, bundle_rel in pairs:
        lp = os.path.join(ctx.live_base, live_rel)
        bp = os.path.join('.', bundle_rel)
        if os.path.exists(lp) and os.path.exists(bp):
            live_bytes = open(lp, 'rb').read()
            bundle_bytes = open(bp, 'rb').read()
            # AGENTS.md installs as managed block + preserved user content by
            # design (install.ps1 Get-ManagedBlockState). Full-file compare is
            # a permanent false positive; compare the managed portion only.
            if live_rel == 'AGENTS.md':
                mblock = re.search(
                    rb'<!-- devin-bundle:begin -->(.*?)<!-- devin-bundle:end -->',
                    live_bytes, re.S)
                if mblock:
                    live_bytes = mblock.group(1).strip()
                    bundle_bytes = bundle_bytes.strip()
            h1 = hashlib.sha256(live_bytes).hexdigest()[:16]
            h2 = hashlib.sha256(bundle_bytes).hexdigest()[:16]
            if h1 == h2:
                print('  OK  ' + bundle_rel + ' (live=bundle)')
            else:
                ctx.warnings.append(bundle_rel + ' live != bundle: ' + h1 + ' vs ' + h2)
                print('  WARN ' + bundle_rel + ' live=' + h1 + ' bundle=' + h2)
        else:
            print('  SKIP ' + bundle_rel)

    # config.json: compare hooks section only (org_id differs by design)
    # hooks.v1.json is the single authored source; live hooks must equal the render.
    live_cfg = os.path.join(ctx.live_base, 'config.json')
    bundle_hooks_src = 'hooks.v1.json'
    if os.path.exists(live_cfg) and os.path.exists(bundle_hooks_src):
        try:
            live_hooks = json.load(open(live_cfg, encoding='utf-8-sig')).get('hooks', {})
            bundle_hooks = json.load(open(bundle_hooks_src, encoding='utf-8-sig'))
            # Normalize: strip the devin-home prefix (live) and quote wrappers so both
            # sides compare as `python /scripts/x.py` — equivalent to render-user-hooks.py output.
            def render_norm(obj, home):
                s = json.dumps(obj, sort_keys=True)
                if home:
                    s = s.replace(home.replace('\\', '/').rstrip('/'), '')
                # render-user-hooks.py now emits a resolved interpreter path
                # (sys.executable / detected python); collapse it to `python`.
                # Scoop shims resolve to `...\current\python` (no .exe). In the
                # serialized JSON the trailing quote arrives escaped as `\"`, so
                # the next char may be a backslash — require only "not a path char".
                s = re.sub(r'[A-Za-z]:[\\/][^"\']*?[\\/]pythonw?(?:\.exe)?(?=(?:\\[\'"])|[\s\'"]|$)',
                           'python', s)
                s = re.sub(r'(?<![\w./\\-])pythonw?\.exe', 'python', s)
                s = s.replace('pythonw ', 'python ')
                s = s.replace('python scripts/', 'python /scripts/')
                s = s.replace('\\"', '').replace('"', '')
                return s
            live_home = ctx.live_base
            h1 = hashlib.sha256(render_norm(live_hooks, live_home).encode()).hexdigest()[:16]
            h2 = hashlib.sha256(render_norm(bundle_hooks, '').encode()).hexdigest()[:16]
            if h1 == h2:
                print('  OK  config.json hooks (live=render of hooks.v1.json)')
            else:
                ctx.warnings.append('config.json hooks live != hooks.v1.json render: ' + h1 + ' vs ' + h2)
                print('  WARN config.json hooks live=' + h1 + ' rendered=' + h2)
        except Exception as e:
            print('  SKIP config.json hooks (' + str(e) + ')')
    else:
        print('  SKIP config.json hooks')

    for ctx.s in ctx.script_files:
        lp = os.path.join(ctx.live_base, 'scripts', ctx.s)
        bp = os.path.join('scripts', ctx.s)
        if os.path.exists(lp) and os.path.exists(bp):
            h1 = hashlib.sha256(open(lp, 'rb').read()).hexdigest()[:16]
            h2 = hashlib.sha256(open(bp, 'rb').read()).hexdigest()[:16]
            if h1 == h2:
                print('  OK  scripts/' + ctx.s + ' (live=bundle)')
            else:
                ctx.warnings.append('scripts/' + ctx.s + ' live != bundle')
                print('  WARN scripts/' + ctx.s + ' live=' + h1 + ' bundle=' + h2)

    # 16. Skills live vs bundle sync lives in m_sync.c16 (single copy).
    # 16b. Managed-tree repo->live drift: full skill trees (not just
    # SKILL.md), agents, data, extensions, and the .devin -> docs remaps
    # install.ps1 exports. Direction is repo->live only: live-only extras
    # (state, build artifacts, per-user plans) are never flagged.
    if ctx.live_base:
        _skip_dirs = ('.venv', '__pycache__', 'node_modules', 'target')
        _maps = (
            ('skills', 'skills'),
            ('agents', 'agents'),
            ('data', 'data'),
            ('extensions', 'extensions'),
            ('.devin/docs', 'docs'),
            ('.devin/plans', os.path.join('docs', 'plans')),
            ('.devin/templates', os.path.join('docs', 'templates')),
        )
        _drift = []
        for _f in ('manifest.json',):
            _bp = _f
            _lp = os.path.join(ctx.live_base, _f)
            if os.path.isfile(_lp) and hashlib.sha256(
                    open(_lp, 'rb').read()).hexdigest() != hashlib.sha256(
                    open(_bp, 'rb').read()).hexdigest():
                _drift.append(_f)
        for repo_dir, live_rel in _maps:
            if not os.path.isdir(repo_dir):
                continue
            for _dp, _dns, _fns in os.walk(repo_dir):
                _dns[:] = [d for d in _dns if d not in _skip_dirs]
                for _fn in _fns:
                    if _fn.endswith('.pyc'):
                        continue
                    bp2 = os.path.join(_dp, _fn)
                    rel = os.path.relpath(bp2, repo_dir)
                    lp = os.path.join(ctx.live_base, live_rel, rel)
                    tag = repo_dir + '/' + rel.replace(os.sep, '/')
                    if not os.path.isfile(lp):
                        _drift.append(tag + ' (missing live)')
                    elif hashlib.sha256(open(lp, 'rb').read()).hexdigest() != \
                            hashlib.sha256(open(bp2, 'rb').read()).hexdigest():
                        _drift.append(tag)
        if _drift:
            ctx.warnings.append('repo->live drift: ' + str(len(_drift))
                                + ' file(s): ' + ', '.join(_drift[:15]))
            print('  WARN repo->live drift ' + str(len(_drift)) + ' file(s):')
            for _d in _drift[:15]:
                print('       ' + _d)
        else:
            print('  OK  managed trees live=bundle '
                  '(skills/agents/data/extensions/docs/plans/templates)')
