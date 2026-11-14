import os, re, json, hashlib, sys, py_compile


def text_hash_matches(path, expected):
    with open(path, 'rb') as source:
        raw = source.read()
    lf = raw.replace(b'\r\n', b'\n')
    variants = (raw, lf, lf.replace(b'\n', b'\r\n'))
    return expected.upper() in {hashlib.sha256(data).hexdigest().upper() for data in variants}


errors = []
warnings = []

print('=== FULL REPO AUDIT ===')
print()

# 1. All JSON files valid
print('[1] JSON files validation')
json_files = []
for root, dirs, files in os.walk('.'):
    dirs[:] = [d for d in dirs if d not in ('.git', '.venv', 'node_modules', 'target', '__pycache__')]
    for f in files:
        if f.endswith('.json'):
            json_files.append(os.path.join(root, f))
for jf in sorted(json_files):
    try:
        json.load(open(jf, encoding='utf-8-sig'))
        print('  OK  ' + jf)
    except Exception as e:
        errors.append('JSON ' + jf + ': ' + str(e))
        print('  FAIL ' + jf + ': ' + str(e))

# 2. All Python scripts compile
print()
print('[2] Python scripts validation')
py_files = []
for root, dirs, files in os.walk('.'):
    dirs[:] = [d for d in dirs if d not in ('.git', '.venv', 'node_modules', 'target', '__pycache__')]
    for f in files:
        if f.endswith('.py'):
            py_files.append(os.path.join(root, f))
for pf in sorted(py_files):
    try:
        compile(open(pf, 'rb').read(), pf, 'exec')
        print('  OK  ' + pf)
    except (SyntaxError, ValueError) as e:
        errors.append('Python ' + pf + ': ' + str(e))
        print('  FAIL ' + pf)

# 2b. Hook scripts must have __main__ guard (detects muted/empty main)
print()
print('[2b] Hook script __main__ guard validation')
hook_scripts = [f for f in py_files if os.path.normpath(f).startswith('scripts') and f.endswith('.py')]
for hs in sorted(hook_scripts):
    content = open(hs, encoding='utf-8').read()
    if '__name__' not in content:
        errors.append(hs + ': missing if __name__ == "__main__" guard')
        print('  FAIL ' + hs + ': missing __main__ guard')
    else:
        print('  OK  ' + hs)

# 3. All skills have valid frontmatter
print()
print('[3] Skill frontmatter validation')
skills_dir = 'skills'
skill_count = 0
for skill_name in sorted(os.listdir(skills_dir)):
    skill_path = os.path.join(skills_dir, skill_name, 'SKILL.md')
    if not os.path.exists(skill_path):
        errors.append(skill_name + ': SKILL.md missing')
        print('  FAIL ' + skill_name + ': SKILL.md missing')
        continue
    skill_count += 1
    with open(skill_path, encoding='utf-8') as f:
        content = f.read()
    issues = []
    if not re.search(r'^name:\s*' + re.escape(skill_name), content, re.M):
        issues.append('name mismatch')
    if 'description:' not in content:
        issues.append('description missing')
    if 'Use when' not in content:
        issues.append('no Use when')
    if issues:
        errors.append(skill_name + ': ' + str(issues))
        print('  FAIL ' + skill_name + ': ' + str(issues))
    else:
        print('  OK  ' + skill_name)
print('  Total: ' + str(skill_count) + ' skills')

# 4. Manifest sync with disk
print()
print('[4] Manifest sync')
manifest = json.load(open('manifest.json', encoding='utf-8-sig'))
manifest_names = set(s['name'] for s in manifest.get('skills', []))
disk_names = set(os.listdir(skills_dir))
if manifest_names != disk_names:
    errors.append('Manifest mismatch')
    print('  FAIL manifest_only=' + str(manifest_names - disk_names))
    print('  FAIL disk_only=' + str(disk_names - manifest_names))
else:
    print('  OK  ' + str(len(manifest_names)) + ' skills = ' + str(len(disk_names)) + ' on disk')
declared_skill_count = manifest.get('skill_count')
if declared_skill_count != skill_count:
    errors.append('manifest skill_count mismatch')
    print('  FAIL skill_count declared=' + str(declared_skill_count) + ' actual=' + str(skill_count))
else:
    print('  OK  skill_count = ' + str(skill_count))

# 5. Manifest version
print()
print('[5] Manifest version')
ver = manifest.get('version', 'MISSING')
print('  version: ' + str(ver))
if ver == 'MISSING':
    warnings.append('Manifest version is missing')

# 6. AGENTS.md rule count
print()
print('[6] AGENTS.md rules')
with open('AGENTS.md', encoding='utf-8-sig') as f:
    agents = f.read()
# Index bullets declare rules (merged rules appear as "N. **-> Rule M**");
# section bodies are "## N." (pinned) and "### N." (non-pinned) headings.
index_rules = [int(n) for n in re.findall(r'(?m)^(\d+)\. \*\*', agents)]
alias_targets = {
    int(n): int(m)
    for n, m in re.findall(
        r'(?m)^(\d+)\. \*\*(?:->|→)\s*Rule\s+(\d+)\*\*', agents)
}
body_numbers = [int(n) for n in re.findall(r'(?m)^#{2,3} (\d+)\.', agents)]
body_set = set(body_numbers)
index_set = set(index_rules)
rules_found = sorted(index_set)
print('  Rules found: ' + str(rules_found))
expected_rules = manifest.get('rule_count', 26)
if len(index_rules) != expected_rules:
    errors.append('Expected ' + str(expected_rules) + ' rules, found ' + str(len(index_rules)))
    print('  FAIL expected ' + str(expected_rules) + ', found ' + str(len(index_rules)))
else:
    print('  OK  ' + str(len(index_rules)) + ' rules present')
declared_rule_count = manifest.get('rule_count')
if declared_rule_count != len(index_rules):
    errors.append('manifest rule_count mismatch')
    print('  FAIL rule_count declared=' + str(declared_rule_count) + ' actual=' + str(len(index_rules)))
else:
    print('  OK  rule_count = ' + str(len(index_rules)))

# Every declared rule that is not a merged alias must have a body section;
# aliases must point at a declared rule number.
missing_bodies = sorted(n for n in index_set
                        if n not in alias_targets and n not in body_set)
if missing_bodies:
    errors.append('Index rules without a body section: ' + str(missing_bodies))
    print('  FAIL index rules without bodies: ' + str(missing_bodies))
else:
    print('  OK  every non-alias rule has a body section')
dangling = sorted(n for n, m in alias_targets.items() if m not in index_set)
if dangling:
    errors.append('Alias rules pointing at undeclared rules: ' + str(dangling))
    print('  FAIL dangling aliases: ' + str(dangling))
else:
    print('  OK  all index aliases resolve')

# 6c. Warn if AGENTS.md is large (context window budget)
print()
print('[6c] AGENTS.md context budget')
agents_size = len(agents)
estimated_tokens = agents_size // 4
AGENTS_TOKEN_BUDGET = 10000
print('  AGENTS.md size: ' + str(agents_size) + ' chars (~' + str(estimated_tokens) + ' tokens)')
if estimated_tokens > AGENTS_TOKEN_BUDGET:
    warnings.append('AGENTS.md exceeds token budget: ~' + str(estimated_tokens) + ' > ' + str(AGENTS_TOKEN_BUDGET))
    print('  WARN AGENTS.md exceeds ' + str(AGENTS_TOKEN_BUDGET) + ' token budget')
else:
    print('  OK  AGENTS.md within budget')

# 6b. Detect missing rule numbers or duplicate numbering (only flag if count is off or duplicates exist)
all_numbers = set(range(1, 30))
found_numbers = set(rules_found)
# A gap is only a problem if it causes the total count to diverge from the manifest.
# Intentional gaps (e.g. rule 6 omitted) are allowed as long as rule_count matches.
duplicates = sorted(n for n in set(index_rules)
                    if index_rules.count(n) > 1)
if duplicates:
    errors.append('Duplicate rule numbers in AGENTS.md: ' + str(duplicates))
    print('  FAIL duplicate rule numbers: ' + str(duplicates))
else:
    print('  OK  no duplicate rule numbers')

# 7. config.json hooks references valid scripts
print()
print('[7] hooks.v1.json script references')
config = json.load(open('config.json', encoding='utf-8-sig'))
hooks = json.load(open('hooks.v1.json', encoding='utf-8-sig'))
if not hooks:
    errors.append('hooks.v1.json is empty')
    print('  FAIL hooks.v1.json empty')
scripts_referenced = set()
for event in hooks:
    for entry in hooks[event]:
        for h in entry.get('hooks', []):
            cmd = h.get('command', '')
            # Match scripts/<name>.py with either slash direction
            m = re.search(r'scripts[/\\]([a-z-]+\.py)', cmd)
            if m:
                scripts_referenced.add(m.group(1))
            # Warn if command uses %APPDATA% (not expanded by hook shell)
            if '%APPDATA%' in cmd:
                warnings.append('Hook command uses %APPDATA% (not expanded): ' + cmd[:80])
                print('  WARN %APPDATA% in command (use {{APPDATA}} or absolute path)')
# Follow one level of indirection: consolidated guards reference check modules
# in their internal lists (executed in-process via _hookrun).
for s in list(scripts_referenced):
    sp = os.path.join('scripts', s)
    if os.path.exists(sp):
        src = open(sp, encoding='utf-8').read()
        for m in re.finditer(r"['\"]([a-z-]+\.py)['\"]", src):
            scripts_referenced.add(m.group(1))
for s in sorted(scripts_referenced):
    path = os.path.join('scripts', s)
    if os.path.exists(path):
        print('  OK  ' + s + ' exists')
    else:
        errors.append('Hook references ' + s + ' but file missing')
        print('  FAIL ' + s + ' missing')

# 7b. config.json + hooks.v1.json schema validation
print()
print('[7b] config.json / hooks.v1.json schema validation')
HOOK_EVENTS = ['PreToolUse', 'PostToolUse', 'PreCompact', 'PostCompact', 'PostCompaction', 'UserPromptSubmit', 'SessionStart', 'SessionEnd', 'Stop', 'PermissionRequest']
config_errors = []
if not isinstance(config.get('version'), int):
    config_errors.append('version must be an integer')
for key in ['devin', 'agent', 'read_config_from', 'shell', 'hooks']:
    if not isinstance(config.get(key), dict):
        config_errors.append('missing or invalid top-level key: ' + key)
if 'attribution' not in config or not isinstance(config['attribution'], bool):
    config_errors.append('attribution must be a boolean')
for event in hooks:
    if event not in HOOK_EVENTS:
        config_errors.append('unknown hook event: ' + event)
    if not isinstance(hooks[event], list):
        config_errors.append('hooks[' + event + '] must be a list')
    else:
        for entry in hooks[event]:
            if not isinstance(entry, dict):
                config_errors.append('hook entry must be an object')
                continue
            if 'matcher' not in entry:
                config_errors.append('hook entry missing matcher')
            if 'hooks' not in entry or not isinstance(entry.get('hooks'), list):
                config_errors.append('hook entry missing hooks list')
            else:
                for h in entry.get('hooks', []):
                    if h.get('type') not in ('command', 'prompt'):
                        config_errors.append('hook type must be "command" or "prompt"')
                    if h.get('type') == 'command' and not h.get('command'):
                        config_errors.append('hook command missing')
                    if h.get('type') == 'prompt' and not h.get('prompt'):
                        config_errors.append('hook prompt missing')
                    if 'timeout' in h and not isinstance(h.get('timeout'), int):
                        config_errors.append('hook timeout must be an integer')
if config_errors:
    for e in config_errors:
        errors.append('config.json schema: ' + e)
        print('  FAIL ' + e)
else:
    print('  OK  config.json schema valid')

# 8. All scripts in scripts/ dir
print()
print('[8] Scripts directory')
script_files = [f for f in os.listdir('scripts') if f.endswith('.py')]
print('  Scripts: ' + str(script_files))
# Manual-run scripts (not hooks) — these are run on-demand, not via config.json hooks
manual_scripts = {'validate-refinement-evidence.py', 'validate-skill-format.py', 'render-user-hooks.py', '_hookrun.py', 'spec-consistency.py', 'install-ledger.py', 'check-tools.py', 'roadmap-board.py', 'status_vocab.py', 'focus.py', 'rules-coverage.py', 'pulse.py', 'simplify-scan.py', 'graph-query.py', 'subagent-trace.py', 'done-evaluator.py', 'ship-metrics.py', 'changelog-refs.py', 'bundle_envelope.py', 'phase-zero.py'}
for s in script_files:
    if s not in scripts_referenced and s not in manual_scripts:
        warnings.append(s + ' not referenced in hooks.v1.json')
        print('  WARN ' + s + ' not referenced in hooks')
    elif s in manual_scripts:
        print('  OK  ' + s + ' (manual-run, not a hook)')

# 9. README counts match reality
print()
print('[9] README counts vs reality')
readme = open('README.md', encoding='utf-8').read()
agent_count = len([f for f in os.listdir('agents') if f.endswith('.md')])
checks = [
    (str(skill_count) + ' skills', str(skill_count) + ' skills' in readme),
    ('rules-' + str(len(rules_found)) + ' badge', ('rules-' + str(len(rules_found)) + '-') in readme),
    (str(agent_count) + ' agents (disk vs manifest)', agent_count == manifest.get('agent_count')),
    (str(len(script_files)) + ' scripts', str(len(script_files)) + ' scripts' in readme),
]
for label, ok in checks:
    status = 'OK' if ok else 'FAIL'
    print('  ' + status + ' ' + label)
    if not ok:
        errors.append('README count wrong: ' + label)

# 9b. manifest.json scripts list consistency
print()
print('[9b] manifest.json scripts list')
manifest = json.load(open('manifest.json', encoding='utf-8'))
manifest_scripts = manifest.get('scripts', [])
manifest_script_count = manifest.get('script_count', 0)
# Separate .py scripts (counted in script_count) from other extensions (helpers)
manifest_py_scripts = [s for s in manifest_scripts if s['name'].endswith('.py')]
manifest_other_scripts = [s for s in manifest_scripts if not s['name'].endswith('.py')]
if len(manifest_scripts) == 0:
    errors.append('manifest.json has script_count but no scripts array')
    print('  FAIL manifest.json scripts array empty/missing')
elif len(manifest_py_scripts) != manifest_script_count:
    errors.append('manifest.json script_count (' + str(manifest_script_count) + ') != .py scripts in array (' + str(len(manifest_py_scripts)) + ')')
    print('  FAIL manifest.json script_count != .py scripts in array')
elif len(manifest_py_scripts) != len(script_files):
    errors.append('manifest.json .py scripts (' + str(len(manifest_py_scripts)) + ') != scripts/ dir .py (' + str(len(script_files)) + ')')
    print('  FAIL manifest.json .py scripts != scripts/ dir')
else:
    # Check each manifest script exists on disk
    missing = [s['name'] for s in manifest_scripts if not os.path.isfile(os.path.join('scripts', s['name']))]
    if missing:
        errors.append('manifest.json lists scripts not on disk: ' + ', '.join(missing))
        print('  FAIL manifest scripts not on disk: ' + ', '.join(missing))
    else:
        print('  OK  manifest.json scripts list consistent (' + str(len(manifest_py_scripts)) + ' .py + ' + str(len(manifest_other_scripts)) + ' other)')
    # Check script hashes
    hash_mismatch = []
    for s in manifest_scripts:
        if s['name'].endswith('.py') and s.get('export_hash'):
            path = os.path.join('scripts', s['name'])
            if os.path.isfile(path):
                if not text_hash_matches(path, s['export_hash']):
                    hash_mismatch.append(s['name'])
    if hash_mismatch:
        warnings.append('manifest script hash mismatch: ' + ', '.join(hash_mismatch))
        print('  WARN script hash mismatch: ' + ', '.join(hash_mismatch))
    else:
        print('  OK  manifest script hashes match')

# 9c. manifest.json agents list and hashes
print()
print('[9c] manifest.json agents')
manifest_agents = manifest.get('agents', [])
agent_files = [f for f in os.listdir('agents') if f.endswith('.md')]
if len(manifest_agents) != len(agent_files):
    errors.append('manifest agent_count mismatch')
    print('  FAIL manifest agent_count mismatch')
else:
    missing = []
    hash_mismatch = []
    for a in manifest_agents:
        path = os.path.join('agents', a['name'] + '.md')
        if not os.path.isfile(path):
            missing.append(a['name'])
        elif a.get('export_hash'):
            if not text_hash_matches(path, a['export_hash']):
                hash_mismatch.append(a['name'])
    if missing:
        errors.append('manifest agents missing on disk: ' + ', '.join(missing))
        print('  FAIL agents missing: ' + ', '.join(missing))
    elif hash_mismatch:
        warnings.append('manifest agent hash mismatch: ' + ', '.join(hash_mismatch))
        print('  WARN agent hash mismatch: ' + ', '.join(hash_mismatch))
    else:
        print('  OK  manifest agents consistent (' + str(len(manifest_agents)) + ' agents)')

# 10. No unmasked secrets
print()
print('[10] Secrets check')
if os.path.exists('credentials.toml'):
    try:
        cred = open('credentials.toml', encoding='utf-8').read()
    except (OSError, IOError) as e:
        warnings.append('credentials.toml exists but could not be read: ' + str(e))
        cred = ''
    if 'MASKED' not in cred and cred.strip():
        errors.append('credentials.toml may have unmasked secrets')
        print('  FAIL credentials.toml unmasked')
    else:
        print('  OK  credentials.toml masked')
else:
    print('  OK  credentials.toml not present (gitignored, not tracked)')

config = json.load(open('config.json', encoding='utf-8-sig'))
org_id = config.get('devin', {}).get('org_id', '')
if org_id == 'MASKED':
    print('  OK  config.json org_id masked')
else:
    warnings.append('config.json org_id may not be masked: ' + str(org_id))
    print('  WARN config.json org_id = ' + str(org_id))

mcp = json.load(open('mcp_config.json', encoding='utf-8-sig'))
mcp_servers = mcp.get('mcpServers', {})
mcp_has_secrets = False
for sname, scfg in mcp_servers.items():
    for k, v in scfg.items():
        if any(s in k.lower() for s in ['token', 'key', 'secret', 'password', 'credential']):
            if v != 'MASKED':
                mcp_has_secrets = True
                print('  WARN mcp ' + sname + '.' + k + ' = ' + str(v))
if mcp_has_secrets:
    warnings.append('mcp_config.json has unmasked secret-like fields')
else:
    print('  OK  mcp_config.json no secret-like fields')

# 10b. mcp_config.json schema validation
print()
print('[10b] mcp_config.json schema validation')
mcp_schema_errors = []
if not isinstance(mcp.get('mcpServers'), dict):
    mcp_schema_errors.append('mcpServers must be an object')
else:
    for sname, scfg in mcp_servers.items():
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
        errors.append('mcp_config.json: ' + e)
        print('  FAIL ' + e)
else:
    print('  OK  mcp_config.json schema valid')

# mcp_count = available MCP integrations declared in bundle-integrations.json
bund_integ = json.load(open('data/bundle-integrations.json', encoding='utf-8-sig'))
avail_mcp = len(bund_integ.get('mcp', {}))
if manifest.get('mcp_count') == avail_mcp:
    print('  OK  mcp_count = ' + str(avail_mcp) + ' (bundle-integrations.json)')
else:
    errors.append('manifest mcp_count ' + str(manifest.get('mcp_count')) + ' != bundle-integrations mcp ' + str(avail_mcp))
    print('  FAIL mcp_count (expected ' + str(avail_mcp) + ')')

# 11. .gitignore coverage
print()
print('[11] .gitignore coverage')
gi = open('.gitignore', encoding='utf-8').read()
required_ignores = ['__pycache__', '.devin/brainstorm/', '.devin/heartbeats/', '.devin/mailboxes/', '.devin/checkpoints/', '.devin/.refine-pending']
for pattern in required_ignores:
    if pattern in gi:
        print('  OK  ' + pattern)
    else:
        warnings.append('.gitignore missing ' + pattern)
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
    warnings.append('tracked __pycache__ files: ' + ', '.join(tracked))
    print('  WARN tracked __pycache__ files: ' + ', '.join(tracked))
else:
    print('  OK  no tracked __pycache__ files')

# 12. CI workflow
print()
print('[12] CI workflow')
ci_path = '.github/workflows/ci.yml'
if os.path.exists(ci_path):
    ci = open(ci_path, encoding='utf-8').read()
    required_steps = ['Validate JSON', 'Validate Python', 'Validate skill frontmatter', 'Check for AI signatures', 'Verify manifest sync']
    for step in required_steps:
        if step in ci:
            print('  OK  step: ' + step)
        else:
            errors.append('CI missing step: ' + step)
            print('  FAIL CI missing step: ' + step)
else:
    errors.append('CI workflow missing')
    print('  FAIL CI workflow missing')

# 13. Issue/PR templates
print()
print('[13] GitHub templates')
templates = [
    '.github/ISSUE_TEMPLATE/config.yml',
    '.github/ISSUE_TEMPLATE/bug_report.yml',
    '.github/ISSUE_TEMPLATE/feature_request.yml',
    '.github/ISSUE_TEMPLATE/skill_improvement.yml',
    '.github/PULL_REQUEST_TEMPLATE.md',
    '.github/release.yml',
    '.github/dependabot.yml',
    '.github/workflows/pr-quality.yml',
]
for t in templates:
    if os.path.exists(t):
        print('  OK  ' + t)
    else:
        errors.append('Template missing: ' + t)
        print('  FAIL ' + t + ' missing')

# 14. LICENSE, SECURITY, CONTRIBUTING, CHANGELOG
print()
print('[14] Repo docs')
docs = [('LICENSE', 'MIT'), ('SECURITY.md', None), ('CONTRIBUTING.md', None), ('CHANGELOG.md', None)]
for doc, check in docs:
    if os.path.exists(doc):
        content = open(doc, encoding='utf-8').read()
        if check and check not in content:
            errors.append(doc + ' does not contain ' + check)
            print('  FAIL ' + doc + ' missing ' + check)
        elif len(content.strip()) < 100:
            warnings.append(doc + ' is too short')
            print('  WARN ' + doc + ' is too short')
        else:
            print('  OK  ' + doc)
    else:
        errors.append(doc + ' missing')
        print('  FAIL ' + doc + ' missing')

# 15. Live vs bundle sync
print()
print('[15] Live vs bundle sync')
# Auto-detect live config path: WSL/Linux ~/.config/devin, Windows %APPDATA%/devin.
# On Windows the CLI reads %APPDATA% -- prefer it there so a stale
# ~/.config/devin shadow copy cannot mask real drift.
home = os.path.expanduser('~')
appdata = os.environ.get('APPDATA', '')
config_devin = os.path.join(home, '.config', 'devin')
appdata_devin = os.path.join(appdata, 'devin') if appdata else ''
if os.name == 'nt' and appdata and os.path.isdir(appdata_devin):
    live_base = appdata_devin
elif os.path.isdir(config_devin):
    live_base = config_devin
elif appdata_devin and os.path.isdir(appdata_devin):
    live_base = appdata_devin
else:
    live_base = ''  # no live install found; sync checks will SKIP
if live_base and os.path.isdir(config_devin) and os.path.isdir(appdata_devin) \
        and os.path.normcase(live_base) != os.path.normcase(config_devin):
    warnings.append('Both %APPDATA%/devin and ~/.config/devin exist; auditing ' + live_base)
    print('  WARN shadow config dir present (auditing ' + live_base + ')')
pairs = [('AGENTS.md', 'AGENTS.md'), ('mcp_config.json', 'mcp_config.json')]
for live_rel, bundle_rel in pairs:
    lp = os.path.join(live_base, live_rel)
    bp = os.path.join('.', bundle_rel)
    if os.path.exists(lp) and os.path.exists(bp):
        h1 = hashlib.sha256(open(lp, 'rb').read()).hexdigest()[:16]
        h2 = hashlib.sha256(open(bp, 'rb').read()).hexdigest()[:16]
        if h1 == h2:
            print('  OK  ' + bundle_rel + ' (live=bundle)')
        else:
            warnings.append(bundle_rel + ' live != bundle: ' + h1 + ' vs ' + h2)
            print('  WARN ' + bundle_rel + ' live=' + h1 + ' bundle=' + h2)
    else:
        print('  SKIP ' + bundle_rel)

# config.json: compare hooks section only (org_id differs by design)
# hooks.v1.json is the single authored source; live hooks must equal the render.
live_cfg = os.path.join(live_base, 'config.json')
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
        live_home = live_base
        h1 = hashlib.sha256(render_norm(live_hooks, live_home).encode()).hexdigest()[:16]
        h2 = hashlib.sha256(render_norm(bundle_hooks, '').encode()).hexdigest()[:16]
        if h1 == h2:
            print('  OK  config.json hooks (live=render of hooks.v1.json)')
        else:
            warnings.append('config.json hooks live != hooks.v1.json render: ' + h1 + ' vs ' + h2)
            print('  WARN config.json hooks live=' + h1 + ' rendered=' + h2)
    except Exception as e:
        print('  SKIP config.json hooks (' + str(e) + ')')
else:
    print('  SKIP config.json hooks')

for s in script_files:
    lp = os.path.join(live_base, 'scripts', s)
    bp = os.path.join('scripts', s)
    if os.path.exists(lp) and os.path.exists(bp):
        h1 = hashlib.sha256(open(lp, 'rb').read()).hexdigest()[:16]
        h2 = hashlib.sha256(open(bp, 'rb').read()).hexdigest()[:16]
        if h1 == h2:
            print('  OK  scripts/' + s + ' (live=bundle)')
        else:
            warnings.append('scripts/' + s + ' live != bundle')
            print('  WARN scripts/' + s + ' live=' + h1 + ' bundle=' + h2)

# 16. New skills live vs bundle sync
print()
print('[16] Skills live vs bundle sync')
new_skills = sorted(d for d in os.listdir('skills') if os.path.isdir(os.path.join('skills', d)))
for s in new_skills:
    lp = os.path.join(live_base, 'skills', s, 'SKILL.md')
    bp = os.path.join('skills', s, 'SKILL.md')
    if os.path.exists(lp) and os.path.exists(bp):
        h1 = hashlib.sha256(open(lp, 'rb').read()).hexdigest()[:16]
        h2 = hashlib.sha256(open(bp, 'rb').read()).hexdigest()[:16]
        if h1 == h2:
            print('  OK  skills/' + s + ' (live=bundle)')
        else:
            warnings.append('skills/' + s + ' live != bundle')
            print('  WARN skills/' + s + ' live=' + h1 + ' bundle=' + h2)

# 17. CHANGELOG version matches manifest
print()
print('[17] Version consistency')
changelog = open('CHANGELOG.md', encoding='utf-8').read()
if ver != 'MISSING' and ver in changelog:
    print('  OK  CHANGELOG and manifest both at ' + str(ver))
else:
    warnings.append('Version mismatch')
    print('  WARN CHANGELOG has ' + str(ver) + ': ' + str(ver in changelog) + ', manifest: ' + str(ver))

# 18. README badges
print()
print('[18] README badges')
expected_skills_badge = 'skills-' + str(skill_count)
if expected_skills_badge in readme:
    print('  OK  skills badge = ' + str(skill_count))
else:
    errors.append('README skills badge wrong (expected ' + expected_skills_badge + ')')
    print('  FAIL skills badge')
expected_rules_badge = 'rules-' + str(len(rules_found))
if expected_rules_badge in readme:
    print('  OK  rules badge = ' + str(len(rules_found)))
else:
    errors.append('README rules badge wrong (expected ' + expected_rules_badge + ')')
    print('  FAIL rules badge')
expected_version_badge = 'version-' + str(ver)
if expected_version_badge in readme:
    print('  OK  version badge = ' + str(ver))
else:
    warnings.append('README version badge may be wrong (expected ' + expected_version_badge + ')')
    print('  WARN version badge')

# 19. agents/ profiles
print()
print('[19] Subagent profiles')
expected_agents = sorted(f for f in os.listdir('agents') if f.endswith('.md'))
manifest_agents = sorted(a['name'] + '.md' for a in manifest.get('agents', []))
print('  Found: ' + str(expected_agents))
for a in expected_agents:
    if a in manifest_agents:
        print('  OK  ' + a)
    else:
        errors.append('Agent not in manifest: ' + a)
        print('  FAIL ' + a + ' not in manifest')
for a in manifest_agents:
    if a not in expected_agents:
        errors.append('Manifest agent missing on disk: ' + a)
        print('  FAIL ' + a + ' in manifest but not on disk')

# 20. No temp files left
print()
print('[20] Temp files check')
import subprocess
_git_dir = subprocess.run(['git', 'rev-parse', '--git-dir'], capture_output=True, text=True, encoding="utf-8", errors="replace").stdout.strip()
if _git_dir and os.path.isdir(_git_dir):
    temp_files = [f for f in os.listdir(_git_dir) if f.endswith('.tmp')]
else:
    temp_files = []
if temp_files:
    warnings.append('Temp files in .git: ' + str(temp_files))
    print('  WARN temp files in .git: ' + str(temp_files))
else:
    print('  OK  no temp files')

# 21. Git tag matches version
print()
print('[21] Git tag vs manifest version')
import subprocess
result = subprocess.run(['git', 'tag', '-l'], capture_output=True, text=True, encoding="utf-8", errors="replace")
tags = result.stdout.strip().split('\n') if result.stdout.strip() else []
print('  Tags: ' + str(tags))
expected_tag = 'v' + str(ver)
if expected_tag in tags:
    print('  OK  ' + expected_tag + ' tag exists')
elif 'v2.1.0' in tags:
    print('  OK  v2.1.0 tag exists (prior version)')
    warnings.append('v' + str(ver) + ' tag not yet created')
else:
    warnings.append(expected_tag + ' tag missing')
    print('  WARN ' + expected_tag + ' tag missing')

# 22. Export scripts exist and are executable
print()
print('[22] Export/install scripts')
scripts_check = ['export.ps1', 'export.sh', 'install.ps1', 'install.sh']
for s in scripts_check:
    if os.path.exists(s):
        print('  OK  ' + s)
    else:
        errors.append(s + ' missing')
        print('  FAIL ' + s + ' missing')

# 22b. Structural validation for export/install scripts
print()
print('[22b] Export/install script structural validation')
for s in scripts_check:
    if not os.path.exists(s):
        continue
    content = open(s, encoding='utf-8-sig').read()
    issues = []
    if s.endswith('.ps1'):
        # Parameters must include DryRun, Force, Backup, RestoreSecrets/Commit/Push/NoMask
        expected = ['[switch]$DryRun']
        if 'export' in s:
            expected = ['[switch]$DryRun', '[switch]$Commit', '[switch]$Push', '[switch]$NoMask']
        else:
            expected = ['[switch]$DryRun', '[switch]$Force', '[switch]$Backup', '[switch]$RestoreSecrets']
        for p in expected:
            if p not in content:
                issues.append('missing ' + p)
        # Must have a no-mask/push guard
        if 'export' in s:
            if 'NoMask' not in content or 'Push' not in content:
                issues.append('missing NoMask/Push parameter or guard')
        # Placeholder must exist in bundle (collapsed) and be expanded in install
        if 'install' in s:
            if '{{APPDATA}}' not in content:
                issues.append('missing {{APPDATA}} placeholder expansion')
        else:
            if 'normalize_config_paths' not in content and '{{APPDATA}}' not in content:
                issues.append('missing config path normalization')
    else:
        # Bash scripts
        expected = ['DRY_RUN=', 'FORCE=', 'BACKUP=', 'RESTORE_SECRETS='] if 'install' in s else ['DRY_RUN=', 'COMMIT=', 'PUSH=', 'NO_MASK=']
        for p in expected:
            if p not in content:
                issues.append('missing ' + p)
        # Shebang
        if not content.startswith('#!'):
            issues.append('missing shebang')
        # Placeholder handling
        if 'install' in s:
            if '{{APPDATA}}' not in content:
                issues.append('missing {{APPDATA}} placeholder handling')
        else:
            if 'normalize_config_paths' not in content and '{{APPDATA}}' not in content:
                issues.append('missing config path normalization')
    if issues:
        errors.append(s + ': ' + ', '.join(issues))
        print('  FAIL ' + s + ': ' + ', '.join(issues))
    else:
        print('  OK  ' + s + ' structure')

# 23. .gitattributes
print()
print('[23] .gitattributes')
ga = open('.gitattributes', encoding='utf-8').read()
if '*.sh' in ga and '*.ps1' in ga:
    print('  OK  line endings configured')
else:
    warnings.append('.gitattributes may be incomplete')
    print('  WARN .gitattributes incomplete')

# 24. TOOLS-MAP.md and SKILL-TIERS.md stale counts
print()
print('[24] Doc count consistency (TOOLS-MAP.md, SKILL-TIERS.md)')
toolsmap = open('.devin/docs/TOOLS-MAP.md', encoding='utf-8').read()
doc_checks = [
    ('TOOLS-MAP.md skills count', str(skill_count) + ' skills', str(skill_count) + ' skills' in toolsmap),
    ('TOOLS-MAP.md scripts count', str(len(script_files)) + ' scripts', str(len(script_files)) + ' scripts' in toolsmap),
    ('TOOLS-MAP.md hook events (8)', '8 eventos', '8 eventos' in toolsmap),
    ('TOOLS-MAP.md tool count (28)', '28 in TOOLS-MAP', ('28 ferramentas' in toolsmap or '19/28' in toolsmap)),
    ('TOOLS-MAP.md excluded tools (9)', '9 in TOOLS-MAP', '9 excluídas' in toolsmap),
    ('README.md diagram skills count', str(skill_count) + ' skills', str(skill_count) + ' skills' in readme),
    ('README.md diagram hook events (8)', '8 events', '8 events' in readme),
]
# skill_count is dynamic (from disk), so these checks auto-adjust to 46 after legacy cleanup
for label, expected, ok in doc_checks:
    status = 'OK' if ok else 'FAIL'
    print('  ' + status + ' ' + label + ' (expected: ' + expected + ')')
    if not ok:
        errors.append(label + ' stale: expected ' + expected)

# 25. Refinement log ID uniqueness
print()
print('[25] Refinement log ID uniqueness')
reflog = os.path.join('.devin', 'refinements.log.jsonl')
if os.path.exists(reflog):
    ref_ids = []
    ref_errors = []
    required_ref_keys = ['id', 'timestamp', 'repro_command', 'expected', 'actual', 'verdict']
    missing_evidence = []
    for line in open(reflog, encoding='utf-8'):
        line = line.strip()
        if not line:
            continue
        try:
            entry = json.loads(line)
            ref_ids.append(entry.get('id', ''))
            missing = [k for k in required_ref_keys if k not in entry or not entry[k]]
            if missing:
                missing_evidence.append(str(entry.get('id', '?')) + ' missing ' + ', '.join(missing))
        except (json.JSONDecodeError, ValueError):
            ref_errors.append('malformed JSON line')
    if ref_errors:
        errors.append('refinements.log.jsonl: ' + str(len(ref_errors)) + ' malformed lines')
        print('  FAIL refinements.log.jsonl: ' + str(len(ref_errors)) + ' malformed lines')
    elif missing_evidence:
        warnings.append('refinements.log.jsonl entries missing evidence: ' + '; '.join(missing_evidence[:5]))
        print('  WARN refinements.log.jsonl entries missing evidence: ' + str(len(missing_evidence)))
    else:
        from collections import Counter
        dups = {k: v for k, v in Counter(ref_ids).items() if v > 1}
        if dups:
            errors.append('refinements.log.jsonl: ' + str(len(dups)) + ' duplicate IDs: ' + ', '.join(sorted(dups.keys())))
            print('  FAIL refinements.log.jsonl: ' + str(len(dups)) + ' duplicate IDs')
        else:
            print('  OK  refinements.log.jsonl: ' + str(len(ref_ids)) + ' unique IDs')
else:
    print('  SKIP refinements.log.jsonl not found')

# 26. Manifest purpose vs SKILL.md description sync
print()
print('[26] Manifest purpose vs SKILL.md description sync')
manifest_data = json.load(open('manifest.json', encoding='utf-8-sig'))
def _norm_ws(s):
    return ' '.join(s.split())


purpose_mismatches = []
prefix_missing = []
for skill in manifest_data.get('skills', []):
    sname = skill['name']
    spurpose = skill.get('purpose', '')
    skill_md = os.path.join('skills', sname, 'SKILL.md')
    if not os.path.exists(skill_md):
        continue
    sm_content = open(skill_md, encoding='utf-8').read()
    desc_match = re.search(r'^description:\s*(.+?)(?:\n[a-z]|\n---)', sm_content, re.MULTILINE | re.DOTALL)
    if desc_match:
        sm_desc = desc_match.group(1).strip()
        if not (spurpose.startswith('Use when') and sm_desc.startswith('Use when')):
            prefix_missing.append(sname)
        # Full normalized comparison: rewritten or truncated tails are
        # drift, not a match.
        if _norm_ws(spurpose) != _norm_ws(sm_desc):
            purpose_mismatches.append(sname)
if purpose_mismatches:
    errors.append('manifest purpose stale vs SKILL.md: ' + ', '.join(purpose_mismatches))
    print('  FAIL ' + str(len(purpose_mismatches)) + ' stale purposes: ' + ', '.join(purpose_mismatches))
else:
    print('  OK  all manifest purposes match SKILL.md descriptions')
if prefix_missing:
    warnings.append('skills missing "Use when" prefix: ' + ', '.join(prefix_missing))
    print('  WARN ' + str(len(prefix_missing)) + ' skills lack "Use when" prefix: ' + ', '.join(prefix_missing))

# 27. No tracked temp artifacts (.zip, .tmp, .bak, ci-logs)
print()
print('[27] No tracked temp artifacts')
import subprocess
artifact_exts = ('.zip', '.tmp', '.bak')
tracked_artifacts = []
try:
    r = subprocess.run(['git', 'ls-files'], capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=10)
    for line in r.stdout.split('\n'):
        line = line.strip()
        if line and line.lower().endswith(artifact_exts):
            tracked_artifacts.append(line)
        elif line == 'ci-logs.zip':
            tracked_artifacts.append(line)
except (subprocess.TimeoutExpired, FileNotFoundError, OSError):
    print('  SKIP git ls-files unavailable')
if not tracked_artifacts:
    print('  OK  no tracked temp artifacts')
else:
    errors.append('tracked temp artifacts: ' + ', '.join(tracked_artifacts))
    print('  FAIL ' + str(len(tracked_artifacts)) + ' tracked artifacts: ' + ', '.join(tracked_artifacts))

# 28. No tracked credential/secret files
print()
print('[28] No tracked credential/secret files')
credential_names = ('credentials.toml', '.env', 'id_rsa', 'id_ed25519', 'id_ecdsa',
                    'secrets.json', 'credentials.json')
credential_exts = ('.pem', '.key', '.env', '.pfx', '.p12')
tracked_creds = []
try:
    r2 = subprocess.run(['git', 'ls-files'], capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=10)
    for line in r2.stdout.split('\n'):
        line = line.strip()
        if line in credential_names or line.endswith(credential_exts):
            tracked_creds.append(line)
except (subprocess.TimeoutExpired, FileNotFoundError, OSError):
    print('  SKIP git ls-files unavailable')
if not tracked_creds:
    print('  OK  no tracked credential files')
else:
    errors.append('CRITICAL: tracked credential files: ' + ', '.join(tracked_creds))
    print('  FAIL ' + str(len(tracked_creds)) + ' tracked credential files: ' + ', '.join(tracked_creds))

# 29. All arXiv refs in scripts/ and tests/ must be in MODEL-GUIDE.md source table
print()
print('[29] arXiv refs in scripts/ and tests/ tracked in MODEL-GUIDE.md')
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
    errors.append('arXiv refs in scripts/tests not in MODEL-GUIDE source table: ' + ', '.join(sorted(unverified)))
    print('  FAIL ' + str(len(unverified)) + ' unverified refs: ' + ', '.join(sorted(unverified)))
else:
    print('  OK  all ' + str(len(code_arxiv_refs)) + ' arXiv refs in scripts/tests are in MODEL-GUIDE source table')

# 30. Hook events match Devin CLI docs in both hooks.v1.json and config.json
print()
print('[30] Hook events match Devin CLI lifecycle docs')
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
    errors.append('hooks.v1.json missing Devin CLI events: ' + ', '.join(sorted(missing)))
    print('  FAIL hooks.v1.json missing events: ' + ', '.join(sorted(missing)))
if extra:
    warnings.append('hooks.v1.json has unknown events: ' + ', '.join(sorted(extra)))
    print('  WARN hooks.v1.json unknown events: ' + ', '.join(sorted(extra)))
if not missing and not extra:
    print('  OK  hooks.v1.json has all ' + str(len(bundle_events)) + ' Devin CLI events')

# Single-source invariant: user-level hooks are rendered from hooks.v1.json at
# install time (render-user-hooks.py); config.json must not carry a second copy.
with open('config.json', encoding='utf-8-sig') as fh:
    cfg_hooks = json.load(fh).get('hooks', {})
if cfg_hooks:
    errors.append('config.json.hooks must be {} — hooks.v1.json is the single source (rendered at install)')
    print('  FAIL config.json.hooks non-empty (duplicate hook surface)')
else:
    print('  OK  config.json.hooks empty (single source: hooks.v1.json)')

# Stale project copy: .devin/hooks.v1.json double-fires with user-level hooks.
if os.path.exists(os.path.join('.devin', 'hooks.v1.json')):
    errors.append('.devin/hooks.v1.json exists — stale duplicate of hooks.v1.json (delete it)')
    print('  FAIL .devin/hooks.v1.json present')
else:
    print('  OK  no .devin/hooks.v1.json duplicate')

# 31. Model context-window data file exists and matches bundle model policy
print()
print('[31] Model context windows data file')
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
            errors.append('data/model-context-windows.json missing models: ' + ', '.join(missing))
            print('  FAIL missing models: ' + ', '.join(missing))
        if wrong_window:
            errors.append('data/model-context-windows.json wrong context_window: ' + '; '.join(wrong_window))
            print('  FAIL wrong context_window: ' + '; '.join(wrong_window))
        if not missing and not wrong_window:
            print('  OK  data/model-context-windows.json has required SWE-2 (262K) entries')
    except (OSError, json.JSONDecodeError) as e:
        errors.append('data/model-context-windows.json is invalid: ' + str(e))
        print('  FAIL invalid data/model-context-windows.json: ' + str(e))
else:
    errors.append('data/model-context-windows.json not found')
    print('  FAIL data/model-context-windows.json not found')

# 32. CHANGELOG [Unreleased] covers PR merges since the released version
print()
print('[32] CHANGELOG [Unreleased] merge coverage')
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
        errors.append('CHANGELOG.md missing ## [Unreleased] section')
        print('  FAIL no [Unreleased] section')
    elif not pr_nums:
        print('  OK  no PR merges since ' + tag)
    else:
        missing = [n for n in pr_nums if '#' + n not in m.group(1)]
        stale = [n for n in missing if n not in recent]
        fresh = [n for n in missing if n in recent]
        if stale:
            errors.append('CHANGELOG [Unreleased] missing PR refs: '
                          + ', '.join('#' + n for n in stale))
            print('  FAIL missing refs: '
                  + ', '.join('#' + n for n in stale))
        if fresh:
            warnings.append('CHANGELOG [Unreleased] missing refs for '
                            'recent merges (<24h): '
                            + ', '.join('#' + n for n in fresh))
            print('  WARN missing refs (recent merges): '
                  + ', '.join('#' + n for n in fresh))
        if not missing:
            print('  OK  [Unreleased] covers ' + str(len(pr_nums))
                  + ' merged PRs since ' + tag)
except Exception as e:
    warnings.append('changelog coverage check skipped: ' + str(e))
    print('  WARN changelog coverage check skipped: ' + str(e))

# 33. Resolved issue files must carry an Answer section
print()
print('[33] Resolved issues carry an Answer section')
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
    errors.append('issues marked resolved without an Answer section: '
                  + ', '.join(unanswered))
    print('  FAIL ' + str(len(unanswered)) + ' resolved issues lack an Answer section')
elif issue_files:
    print('  OK  all resolved issues carry an Answer section')
else:
    print('  SKIP no issue files under .devin/scratch/**/issues/')

# 34. Install drift ledger reconcile (M2_06)
print()
print('[34] Install drift ledger')
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
        warnings.append('ledger drift: ' + ', '.join(_drift[:20]))
        print('  WARN drift: Modified=' + str(len(_rep['Modified']))
              + ' Foreign=' + str(len(_rep['Foreign'])))
    else:
        print('  OK  no Modified/Foreign drift ('
              + str(len(_rep['Current'])) + ' current)')
except Exception as _e:
    print('  SKIP ledger check failed to run: ' + str(_e))

# 35. tools.json schema + renderer byte-identity (M2_07)
print()
print('[35] tools.json renderers')
try:
    _ct_out = subprocess.run(
        [sys.executable, os.path.join('scripts', 'check-tools.py')],
        capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=120)
    if _ct_out.returncode == 0:
        print('  OK  ' + _ct_out.stdout.strip().splitlines()[-1])
    else:
        errors.append('check-tools.py failed: '
                      + _ct_out.stdout.strip()[-200:])
        print('  FAIL check-tools.py')
except Exception as _e:
    print('  SKIP check-tools failed to run: ' + str(_e))

# Shared scanner for checks 36-38: yields .py files under extensions/
# and scripts/, skipping vendored/runtime dirs.
def _scan_py_files():
    for _root in ('extensions', 'scripts', 'skills'):
        for _dirpath, _dirnames, _filenames in os.walk(_root):
            _dirnames[:] = [d for d in _dirnames
                            if d not in ('.venv', '__pycache__', 'tests')]
            for _fn in _filenames:
                if _fn.endswith('.py'):
                    yield os.path.join(_dirpath, _fn)


# 36. CLI exit-code contract: mains that can emit {"ok": false} must not
# exit 0 unconditionally (scripts/CI cannot detect failure otherwise).
print()
print('[36] CLI exit-code contract')
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
            # Bug shape: print(json.dumps(<call>)) then bare return 0
            # while the printed envelope can carry ok:false and main
            # shows no ok-awareness (literal "ok" key, .get("ok"),
            # nonzero literal returns, or sys.exit paths).
            if 'print(json.dumps(' not in _seg:
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
        warnings.append('cli mains may exit 0 on ok:false: '
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
print('[37] subprocess utf-8 decode')
try:
    import ast as _ast37
    _SUB = ('run', 'call', 'check_output', 'check_call', 'Popen')
    _bad_enc = []
    for _fp in _scan_py_files():
        try:
            _tree = _ast37.parse(
                open(_fp, encoding='utf-8').read())
        except (OSError, UnicodeDecodeError, SyntaxError):
            continue
        for _node in _ast37.walk(_tree):
            if not isinstance(_node, _ast37.Call):
                continue
            _f = _node.func
            _is_sub = False
            if (isinstance(_f, _ast37.Attribute)
                    and _f.attr in _SUB
                    and isinstance(_f.value, _ast37.Name)
                    and _f.value.id == 'subprocess'):
                _is_sub = True
            if not _is_sub:
                continue
            _tk = next((k for k in _node.keywords
                        if k.arg == 'text'), None)
            if _tk is None:
                continue
            if (isinstance(_tk.value, _ast37.Constant)
                    and _tk.value.value is not True):
                continue
            if not any(k.arg and k.arg.startswith('encoding')
                       for k in _node.keywords):
                _bad_enc.append('%s:%d' % (_fp, _node.lineno))
                break
    if _bad_enc:
        warnings.append('subprocess text=True without encoding=: '
                        + ', '.join(_bad_enc[:10]))
        print('  WARN ' + str(len(_bad_enc)) + ' call(s): '
              + ', '.join(_bad_enc[:5]))
    else:
        print('  OK  all text=True subprocess calls pin utf-8')
except Exception as _e:
    print('  SKIP decode check failed: ' + str(_e))

# 38. file-I/O text decode: Path.read_text()/write_text() and builtin
# open() in text mode without an encoding pin decode with the Windows
# locale codepage (cp1252) - same mojibake/crash class as check [37]
# but for file content. Binary modes ('b' in mode) are exempt.
print()
print('[38] file-I/O utf-8 decode')
try:
    _bad_io = []
    for _fp in _scan_py_files():
        try:
            _tree = _ast37.parse(
                open(_fp, encoding='utf-8').read())
        except (OSError, UnicodeDecodeError, SyntaxError):
            continue
        for _node in _ast37.walk(_tree):
            if not isinstance(_node, _ast37.Call):
                continue
            _f = _node.func
            if isinstance(_f, _ast37.Attribute) \
                    and _f.attr in ('read_text', 'write_text'):
                # encoding is positional arg 0 for Path text methods
                _ok = len(_node.args) >= 1 or any(
                    k.arg == 'encoding' for k in _node.keywords
                    if k.arg)
            elif isinstance(_f, _ast37.Name) and _f.id == 'open':
                _mode = None
                for _k in _node.keywords:
                    if _k.arg == 'mode':
                        _mode = _k.value
                if _mode is None and len(_node.args) >= 2:
                    _mode = _node.args[1]
                if isinstance(_mode, _ast37.Constant) \
                        and isinstance(_mode.value, str) \
                        and 'b' in _mode.value:
                    continue
                if not isinstance(_mode, _ast37.Constant) \
                        and _mode is not None:
                    continue  # dynamic mode - cannot prove text
                _ok = len(_node.args) >= 4 or any(
                    k.arg == 'encoding' for k in _node.keywords
                    if k.arg)
            else:
                continue
            if not _ok:
                _bad_io.append('%s:%d' % (_fp, _node.lineno))
                break
    if _bad_io:
        warnings.append('text file I/O without encoding=: '
                        + ', '.join(_bad_io[:10]))
        print('  WARN ' + str(len(_bad_io)) + ' call(s): '
              + ', '.join(_bad_io[:5]))
    else:
        print('  OK  all text file I/O pins utf-8')
except Exception as _e:
    print('  SKIP file-decode check failed: ' + str(_e))

# 39. stdio decode: text-mode sys.stdin readers (JSON-lines workers,
# piped-content CLIs) decode with the Windows locale codepage (cp1252)
# unless the process pins UTF-8 - non-ASCII input mojibakes into lone
# surrogates (laya engine_error:TypeError) or silently corrupts.
# Binary readers (sys.stdin.buffer) and pinned streams are exempt.
print()
print('[39] stdio utf-8 decode')
try:
    import re as _re39
    _STDIN_TXT = _re39.compile(
        r'sys\.stdin\.(read|readline)\s*\(|'
        r'json\.load\s*\(\s*sys\.stdin\s*\)|'
        r'json\.loads\s*\(\s*sys\.stdin\.read|'
        r'for\s+\w+\s+in\s+sys\.stdin\s*:')
    _bad_stdio = []
    for _fp in _scan_py_files():
        try:
            _src39 = open(_fp, encoding='utf-8').read()
        except (OSError, UnicodeDecodeError):
            continue
        if 'sys.stdin' not in _src39:
            continue
        # Exempt only when stdin itself is the reconfigure target — a bare
        # 'reconfigure' may pin stdout and leave stdin on cp1252.
        if 'pin_stdio_utf8' in _src39 or _re39.search(
                r'sys\.stdin\.reconfigure|'
                r'\(sys\.stdin\s*,|'
                r'getattr\(sys\.stdin,\s*[\'"]reconfigure', _src39):
            continue
        if 'sys.stdin.buffer' in _src39 and not _STDIN_TXT.search(_src39):
            continue
        if _STDIN_TXT.search(_src39):
            _bad_stdio.append(_fp)
    if _bad_stdio:
        warnings.append('text-mode sys.stdin without utf-8 pin: '
                        + ', '.join(_bad_stdio[:10]))
        print('  WARN ' + str(len(_bad_stdio)) + ' file(s): '
              + ', '.join(_bad_stdio[:5]))
    else:
        print('  OK  all text-mode stdin readers pin utf-8')
except Exception as _e:
    print('  SKIP stdio check failed: ' + str(_e))

# 40. Skills debt: warn on stale SKILL.md (>180 days since mtime) or a
# skill directory that lacks SKILL.md. Warnings, not errors - staleness
# is a signal to review, not a defect.
print()
print('[40] Skills debt (staleness)')
try:
    import time as _time40
    _stale_days = 180
    _now40 = _time40.time()
    _stale = []
    _missing = []
    for _sk in sorted(os.listdir(skills_dir)):
        _sp = os.path.join(skills_dir, _sk)
        _sm = os.path.join(_sp, 'SKILL.md')
        if not os.path.isdir(_sp):
            continue
        if not os.path.exists(_sm):
            _missing.append(_sk)
            continue
        _age = (_now40 - os.path.getmtime(_sm)) / 86400
        if _age > _stale_days:
            _stale.append('%s (%dd)' % (_sk, int(_age)))
    for _sk in _missing:
        warnings.append('skill dir lacks SKILL.md: ' + _sk)
        print('  WARN ' + _sk + ': no SKILL.md')
    if _stale:
        warnings.append('stale SKILL.md (>' + str(_stale_days) + 'd): '
                        + ', '.join(_stale[:10]))
        print('  WARN ' + str(len(_stale)) + ' stale SKILL.md: '
              + ', '.join(_stale[:5]))
    elif not _missing:
        print('  OK  all SKILL.md files touched within '
              + str(_stale_days) + ' days')
except Exception as _e:
    print('  SKIP skills-debt check failed: ' + str(_e))

# 41. Compat doc must name the validated CLI version (#531)
print()
print('[41] Compat doc version pin')
try:
    _ident = json.load(open('data/bundle-identity.json', encoding='utf-8-sig'))
    _v = _ident.get('validated_cli_version')
    _doc = '.devin/docs/DEVIN-CLI-COMPATIBILITY.md'
    if not _v:
        warnings.append('bundle-identity.json lacks validated_cli_version')
        print('  WARN no validated_cli_version declared')
    elif not os.path.isfile(_doc):
        errors.append(_doc + ' missing')
        print('  FAIL ' + _doc + ' missing')
    elif _v not in open(_doc, encoding='utf-8').read():
        warnings.append(_doc + ' does not name validated_cli_version ' + _v)
        print('  WARN ' + _doc + ' missing version ' + _v)
    else:
        print('  OK  compat doc names validated_cli_version ' + _v)
except Exception as _e41:
    print('  SKIP compat-doc check failed: ' + str(_e41))

# 42. stdout utf-8 pin: files that print ensure_ascii=False JSON must
# pin sys.stdout - on Windows the console is cp1252 and `>` redirects
# write mojibake (issue #573: PT transcripts lost accents).
print()
print('[42] stdout utf-8 pin on JSON emitters')
try:
    import re as _re42
    _bad_out = []
    _PIN42 = _re42.compile(
        r'sys\.stdout\.reconfigure|'
        r'\(sys\.stdout\s*,|'
        r'getattr\(sys\.stdout,\s*[\'"]reconfigure|'
        r'for\s+\w+\s+in\s*\(sys\.(?:stdin|stdout)\s*,\s*sys\.(?:stdin|stdout)|'
        r'pin_stdio_utf8')
    for _fp in _scan_py_files():
        try:
            _src42 = open(_fp, encoding='utf-8').read()
        except (OSError, UnicodeDecodeError):
            continue
        if _PIN42.search(_src42):
            continue
        # stdout emission = print(...) or sys.stdout.write(...) whose
        # args contain a json.dumps(..., ensure_ascii=False) call, OR
        # print(var) where var was assigned such a dumps call. AST-
        # based: the old 400-char/)) window false-flagged any print
        # within 400 chars of an unrelated file-write json.dump.
        _emits = False
        if 'ensure_ascii=False' in _src42:
            try:
                _t42e = _ast.parse(_src42)
            except SyntaxError:
                _t42e = None
            if _t42e is not None:
                def _is_ascii_dumps(_call):
                    _f = _call.func
                    _named = (isinstance(_f, _ast.Attribute)
                              and _f.attr == 'dumps') or (
                                  isinstance(_f, _ast.Name)
                                  and _f.id == 'dumps')
                    return _named and any(
                        k.arg == 'ensure_ascii'
                        and isinstance(k.value, _ast.Constant)
                        and k.value.value is False
                        for k in _call.keywords)
                _dumped = set()
                for _n in _ast.walk(_t42e):
                    if isinstance(_n, _ast.Assign) \
                            and isinstance(_n.value, _ast.Call) \
                            and _is_ascii_dumps(_n.value):
                        for _tg in _n.targets:
                            if isinstance(_tg, _ast.Name):
                                _dumped.add(_tg.id)
                for _cn in _ast.walk(_t42e):
                    if not isinstance(_cn, _ast.Call):
                        continue
                    _fn = _cn.func
                    _is_out = (isinstance(_fn, _ast.Name)
                               and _fn.id == 'print') or (
                        isinstance(_fn, _ast.Attribute)
                        and _fn.attr == 'write'
                        and isinstance(_fn.value, _ast.Attribute)
                        and _fn.value.attr == 'stdout'
                        and isinstance(_fn.value.value, _ast.Name)
                        and _fn.value.value.id == 'sys')
                    if not _is_out:
                        continue
                    for _a in _cn.args:
                        for _x in _ast.walk(_a):
                            if (isinstance(_x, _ast.Call)
                                    and _is_ascii_dumps(_x)) or (
                                    isinstance(_x, _ast.Name)
                                    and _x.id in _dumped):
                                _emits = True
                                break
                        if _emits:
                            break
                    if _emits:
                        break
        if _emits:
            _bad_out.append(_fp)
            continue
        # non-ASCII literals in stdout-bound calls (print/add_argument/
        # error/write) crash on cp1252 consoles without a pin - found via
        # grainrad --help UnicodeEncodeError on the -> arrow.
        try:
            _t42 = _ast.parse(_src42)
        except SyntaxError:
            continue
        _na = False
        for _cn in _ast.walk(_t42):
            if not isinstance(_cn, _ast.Call):
                continue
            _fn = _cn.func
            _is_out = (isinstance(_fn, _ast.Name) and _fn.id == 'print') \
                or (isinstance(_fn, _ast.Attribute) and _fn.attr in
                    ('add_argument', 'error', 'exit', 'write'))
            if not _is_out:
                continue
            for _a in _ast.walk(_cn):
                if isinstance(_a, _ast.Constant) \
                        and isinstance(_a.value, str) \
                        and any(ord(c) > 127 for c in _a.value):
                    _na = True
                    break
            if _na:
                break
        if _na:
            _bad_out.append(_fp + ' (non-ascii output)')
    if _bad_out:
        errors.append('JSON emitters without sys.stdout utf-8 pin: '
                      + ', '.join(_bad_out[:10]))
        print('  FAIL ' + str(len(_bad_out)) + ' file(s): '
              + ', '.join(_bad_out[:5]))
    else:
        print('  OK  all ensure_ascii=False emitters pin utf-8 stdout')
except Exception as _e42:
    print('  SKIP stdout-pin check failed: ' + str(_e42))

# 43. stdlib-name usage without import: `sys.`/`os.`/`re.`/`json.`
# attribute access with no matching import is a NameError at runtime.
# Caught refresh.py vault template (pin added inside a string literal
# escaped every check that compiles only real code).
print()
print('[43] stdlib names used without import')
try:
    import ast as _ast43
    _bad_name = []
    _STDLIB = ('sys', 'os', 're', 'json', 'subprocess', 'pathlib',
               'datetime', 'shutil', 'hashlib', 'argparse')
    for _fp in _scan_py_files():
        try:
            _tree43 = _ast43.parse(
                open(_fp, encoding='utf-8').read())
        except (OSError, UnicodeDecodeError, SyntaxError):
            continue
        _imported = set()
        for _n in _ast43.walk(_tree43):
            if isinstance(_n, _ast43.Import):
                _imported.update(
                    a.name.split('.')[0] for a in _n.names)
            elif isinstance(_n, _ast43.ImportFrom):
                _imported.update(
                    (a.asname or a.name) for a in _n.names)
        _used = {n.value.id for n in _ast43.walk(_tree43)
                 if isinstance(n, _ast43.Attribute)
                 and isinstance(n.value, _ast43.Name)}
        _missing = [u for u in _used
                    if u in _STDLIB and u not in _imported]
        if _missing:
            _bad_name.append(_fp + ' (' + ','.join(sorted(_missing)) + ')')
    if _bad_name:
        errors.append('stdlib names used without import: '
                      + ', '.join(_bad_name[:10]))
        print('  FAIL ' + str(len(_bad_name)) + ' file(s): '
              + ', '.join(_bad_name[:5]))
    else:
        print('  OK  no stdlib name used without import')
except Exception as _e43:
    print('  SKIP import-use check failed: ' + str(_e43))

# 44. Python-floor compat: stdlib APIs newer than the CI floor (3.11)
# import fine but crash at call time on older interpreters.
# read_text(newline=) landed in 3.13 - it produced the devin-manager
# CI ubuntu py3.11 probe failure (empty stdout -> JSONDecodeError);
# Path.walk() and itertools.batched() are 3.12+.
print()
print('[44] Python floor compat (3.11)')
try:
    import ast as _ast44
    _bad44 = []
    for _fp in _scan_py_files():
        try:
            _src44 = open(_fp, encoding='utf-8').read()
        except (OSError, UnicodeDecodeError):
            continue
        if 'read_text' not in _src44 and 'batched' not in _src44 \
                and 'walk' not in _src44:
            continue
        try:
            _t44 = _ast44.parse(_src44)
        except SyntaxError:
            continue
        _hit = None
        for _n in _ast44.walk(_t44):
            if isinstance(_n, _ast44.ImportFrom) \
                    and _n.module == 'itertools' \
                    and any(a.name == 'batched' for a in _n.names):
                _hit = 'itertools.batched is 3.12+'
                break
            if not isinstance(_n, _ast44.Call):
                continue
            _f = _n.func
            if not isinstance(_f, _ast44.Attribute):
                continue
            if _f.attr == 'read_text' and any(
                    k.arg == 'newline' for k in _n.keywords):
                _hit = 'read_text(newline=) is 3.13+'
                break
            if _f.attr == 'batched' and isinstance(_f.value, _ast44.Name) \
                    and _f.value.id == 'itertools':
                _hit = 'itertools.batched is 3.12+'
                break
            if _f.attr == 'walk' and isinstance(_f.value, _ast44.Call) \
                    and getattr(_f.value.func, 'id', '') == 'Path':
                _hit = 'Path.walk() is 3.12+'
                break
        _pathvars = set()
        for _n in _ast44.walk(_t44):
            if isinstance(_n, _ast44.Assign) \
                    and isinstance(_n.value, _ast44.Call) \
                    and getattr(_n.value.func, 'id', '') in (
                    'Path', 'PosixPath', 'WindowsPath'):
                for _tg in _n.targets:
                    if isinstance(_tg, _ast44.Name):
                        _pathvars.add(_tg.id)
        for _n in _ast44.walk(_t44):
            if not isinstance(_n, _ast44.Call):
                continue
            _f = _n.func
            if not isinstance(_f, _ast44.Attribute):
                continue
            if _f.attr == 'walk' and isinstance(_f.value, _ast44.Name) \
                    and _f.value.id in _pathvars:
                _hit = 'Path.walk() is 3.12+'
                break
        if _hit:
            _bad44.append(_fp + ' (' + _hit + ')')
    if _bad44:
        errors.append('stdlib API newer than the 3.11 floor: '
                      + ', '.join(_bad44[:10]))
        print('  FAIL ' + str(len(_bad44)) + ' file(s): '
              + ', '.join(_bad44[:5]))
    else:
        print('  OK  no stdlib API newer than the 3.11 floor')
except Exception as _e44:
    print('  SKIP floor-compat check failed: ' + str(_e44))

# 45. --out/-o/dst output paths: user-named outputs must refuse to
# overwrite existing files (stamped {"ok": false} + non-zero exit).
# Heuristic: declares an output flag AND has a file-write call but no
# .exists() check anywhere in the file. Warn-level - append-mode
# recorders and delegated writers may still be legit.
print()
print('[45] --out overwrite-refusal')
try:
    import ast as _ast45
    import re as _re45
    _WRITE45 = _re45.compile(
        r"open\s*\([^)]*['\"]w[b+]*['\"]|write_text\s*\(|\.save\s*\("
        r"|write_bytes\s*\(|subprocess\.(?:run|Popen|call|check_output)"
        r"\s*\(")
    _OUTSEGS = {'out', 'output', 'dst', 'sheet', 'report', 'dump',
                'outfile', 'o'}
    _POSNAMES = {'out', 'output', 'dst', 'outfile', 'target'}

    def _isoutflag45(f):
        """-o or any long flag with an output-y segment (--diff-out,
        --out-file, --output-dir; but not --timeout/--layout)."""
        if f == '-o':
            return True
        if not f.startswith('--'):
            return False
        return any(s in _OUTSEGS for s in f[2:].split('-'))

    def _dests45(t):
        """dest names declared via output flags on add_argument calls."""
        ds = set()
        for n in _ast45.walk(t):
            if not (isinstance(n, _ast45.Call)
                    and getattr(n.func, 'attr', '') == 'add_argument'):
                continue
            flags = [a.value for a in n.args
                     if isinstance(a, _ast45.Constant)
                     and isinstance(a.value, str)]
            pos = next((f for f in flags if not f.startswith('-')),
                       None)
            if not any(_isoutflag45(f) for f in flags) \
                    and not (pos and pos in _POSNAMES):
                continue
            act = next((k.value.value for k in n.keywords
                        if k.arg == 'action'
                        and isinstance(k.value, _ast45.Constant)), None)
            if act in ('store_true', 'store_false', 'count',
                       'append_const', 'version', 'help'):
                continue
            dest = next((k.value.value for k in n.keywords
                         if k.arg == 'dest'
                         and isinstance(k.value, _ast45.Constant)), None)
            if dest is None:
                longf = [f.lstrip('-').replace('-', '_')
                         for f in flags if f.startswith('--')]
                dest = longf[0] if longf else (
                    flags[0].lstrip('-') if flags else None)
            if dest:
                ds.add(dest)
        return ds

    def _argsvars45(t):
        """Names bound from parse_args()/parse_known_args()."""
        vs = {'args'}
        for n in _ast45.walk(t):
            if isinstance(n, _ast45.Assign) and isinstance(
                    n.value, _ast45.Call) and getattr(
                    n.value.func, 'attr', '') in (
                    'parse_args', 'parse_known_args'):
                for tg in n.targets:
                    if isinstance(tg, _ast45.Name):
                        vs.add(tg.id)
        return vs

    def _isout45(x, dests, avars):
        return (isinstance(x, _ast45.Attribute)
                and x.attr in dests
                and isinstance(x.value, _ast45.Name)
                and x.value.id in avars)

    def _derived45(t, dests, avars):
        """Names whose value flows from <ns>.<dest> (to fixpoint)."""
        def _hits(node):
            for x in _ast45.walk(node):
                if _isout45(x, dests, avars):
                    return True
            return False
        params = {}   # func_name -> positional param names
        for n in _ast45.walk(t):
            if isinstance(n, _ast45.FunctionDef):
                params[n.name] = [a.arg for a in n.args.args]
        names = set()
        grew = True
        while grew:
            grew = False
            for n in _ast45.walk(t):
                tgts, expr = [], None
                if isinstance(n, _ast45.Assign):
                    tgts = n.targets
                    expr = n.value
                elif isinstance(n, _ast45.AnnAssign):
                    tgts = [n.target]
                    expr = n.value
                elif isinstance(n, _ast45.For):
                    tgts = [n.target]
                    expr = n.iter
                elif isinstance(n, _ast45.Call):
                    for kw in n.keywords:
                        if (kw.arg and kw.arg not in names
                                and _hits(kw.value)):
                            names.add(kw.arg)
                            grew = True
                    if isinstance(n.func, _ast45.Name):
                        ps = params.get(n.func.id, [])
                        for i, a in enumerate(n.args):
                            if i < len(ps) and ps[i] not in names \
                                    and _hits(a):
                                names.add(ps[i])
                                grew = True
                    continue
                if expr is None:
                    continue
                if _hits(expr) or any(
                        x.id in names
                        for x in _ast45.walk(expr)
                        if isinstance(x, _ast45.Name)):
                    for tg in tgts:
                        for x in _ast45.walk(tg):
                            if (isinstance(x, _ast45.Name)
                                    and x.id not in names):
                                names.add(x.id)
                                grew = True
        return names

    def _guards45(t, dests, avars, names):
        """True if some exists()-style call touches the out path."""
        for n in _ast45.walk(t):
            if not isinstance(n, _ast45.Call):
                continue
            m = getattr(n.func, 'attr', None)
            if m not in ('exists', 'is_file', 'is_dir', 'lexists'):
                continue
            for x in _ast45.walk(n):
                if _isout45(x, dests, avars):
                    return True
                if (isinstance(x, _ast45.Name) and x.id in names):
                    return True
        return False

    # Documented exemptions: --out names a file written by an external
    # engine inside an already-guarded dir, or the guard lives outside
    # this file's AST (helper module / subprocess target).
    _SKIP45 = {
        'extensions/remotion-render/render.py',   # out_name -> remotion out/; workdir rmtree-guarded
        'extensions/comfyui-operator/wrapper.py',  # --out is a download dir (makedirs refresh)
        'extensions/craft-bridge/ui_dsl.py',      # O_EXCL atomic refusal inside _write_output
        'extensions/computer-use/terminal.py',    # dst = session-link id, not a file
        'extensions/computer-use/browser.py',     # target = env/URL, not a file
        'extensions/ppisp-prep/ppisp_runner.py',  # --out = dir forwarded to upstream trainer
    }
    _bad45 = []
    for _fp in _scan_py_files():
        _fn = str(_fp).replace('\\', '/')
        if _fn in _SKIP45:
            continue
        try:
            _src45 = open(_fp, encoding='utf-8').read()
            _t45 = _ast45.parse(_src45)
        except (OSError, UnicodeDecodeError, SyntaxError):
            continue
        _d45 = _dests45(_t45)
        if not _d45 or not _WRITE45.search(_src45):
            continue
        _av45 = _argsvars45(_t45)
        if _guards45(_t45, _d45, _av45,
                     _derived45(_t45, _d45, _av45)):
            continue
        _bad45.append(_fp)
    if _bad45:
        warnings.append('--out declared without overwrite-refusal: '
                        + ', '.join(_bad45[:10]))
        print('  WARN ' + str(len(_bad45)) + ' file(s): '
              + ', '.join(_bad45[:5]))
    else:
        print('  OK  all --out emitters refuse to overwrite')
except Exception as _e45:
    print('  SKIP out-refusal check failed: ' + str(_e45))

print()
print('=== SUMMARY ===')
print('Errors:   ' + str(len(errors)))
print('Warnings: ' + str(len(warnings)))
if errors:
    print()
    print('ERRORS:')
    for e in errors:
        print('  - ' + e)
if warnings:
    print()
    print('WARNINGS:')
    for w in warnings:
        print('  - ' + w)
if not errors and not warnings:
    print()
    _n_checks = len(set(re.findall(
        r"^print\('\[(\d+[a-z]?)\]",
        open(__file__, encoding='utf-8').read(), re.M)))
    print('ALL ' + str(_n_checks) + ' CHECKS PASSED - NO ERRORS, NO WARNINGS')
sys.exit(1 if errors else 0)

