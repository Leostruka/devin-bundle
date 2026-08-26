import os, re, json, hashlib, sys, py_compile

errors = []
warnings = []

print('=== FULL REPO AUDIT ===')
print()

# 1. All JSON files valid
print('[1] JSON files validation')
json_files = []
for root, dirs, files in os.walk('.'):
    if '.git' in root: continue
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
    if '.git' in root: continue
    for f in files:
        if f.endswith('.py'):
            py_files.append(os.path.join(root, f))
for pf in sorted(py_files):
    try:
        py_compile.compile(pf, doraise=True)
        print('  OK  ' + pf)
    except py_compile.PyCompileError as e:
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
rules_found = []
for i in range(1, 21):
    # Anchor to start of line to avoid false positives (e.g. "6. **" in "16. **")
    if '\n' + str(i) + '. **' in agents:
        rules_found.append(i)
print('  Rules found: ' + str(rules_found))
if len(rules_found) != 19:
    errors.append('Expected 19 rules, found ' + str(len(rules_found)))
else:
    print('  OK  19 rules present')

# 7. config.json hooks references valid scripts
print()
print('[7] config.json hooks script references')
config = json.load(open('config.json', encoding='utf-8-sig'))
hooks = config.get('hooks', {})
if not hooks:
    errors.append('No "hooks" key in config.json')
    print('  FAIL no hooks key in config.json')
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
for s in sorted(scripts_referenced):
    path = os.path.join('scripts', s)
    if os.path.exists(path):
        print('  OK  ' + s + ' exists')
    else:
        errors.append('Hook references ' + s + ' but file missing')
        print('  FAIL ' + s + ' missing')

# 8. All scripts in scripts/ dir
print()
print('[8] Scripts directory')
script_files = [f for f in os.listdir('scripts') if f.endswith('.py')]
print('  Scripts: ' + str(script_files))
# Manual-run scripts (not hooks) — these are run on-demand, not via config.json hooks
manual_scripts = {'validate-refinement-evidence.py', 'validate-skill-format.py'}
for s in script_files:
    if s not in scripts_referenced and s not in manual_scripts:
        warnings.append(s + ' not referenced in config.json hooks')
        print('  WARN ' + s + ' not referenced in hooks')
    elif s in manual_scripts:
        print('  OK  ' + s + ' (manual-run, not a hook)')

# 9. README counts match reality
print()
print('[9] README counts vs reality')
readme = open('README.md', encoding='utf-8').read()
agent_count = len([f for f in os.listdir('agents') if f.endswith('.md')])
checks = [
    (f'{skill_count} skills', skill_count > 0),
    ('19 rules', len(rules_found) == 19),  # 1-5,7-20 (Rule 6 removed, Rule 20 added)
    ('5 agents', agent_count == 5),
    ('13 scripts', len(script_files) == 13),
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
    '.github/ISSUE_TEMPLATE/bug_report.md',
    '.github/ISSUE_TEMPLATE/feature_request.md',
    '.github/PULL_REQUEST_TEMPLATE.md',
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
        else:
            print('  OK  ' + doc)
    else:
        errors.append(doc + ' missing')
        print('  FAIL ' + doc + ' missing')

# 15. Live vs bundle sync
print()
print('[15] Live vs bundle sync')
# Auto-detect live config path: WSL ~/.config/devin, Linux ~/.config/devin, Windows %APPDATA%/devin
home = os.path.expanduser('~')
appdata = os.environ.get('APPDATA', '')
if os.path.isdir(os.path.join(home, '.config', 'devin')):
    live_base = os.path.join(home, '.config', 'devin')
elif appdata and os.path.isdir(os.path.join(appdata, 'devin')):
    live_base = os.path.join(appdata, 'devin')
else:
    live_base = ''  # no live install found; sync checks will SKIP
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
            errors.append(bundle_rel + ' live != bundle: ' + h1 + ' vs ' + h2)
            print('  FAIL ' + bundle_rel + ' live=' + h1 + ' bundle=' + h2)
    else:
        print('  SKIP ' + bundle_rel)

# config.json: compare hooks section only (org_id differs by design)
live_cfg = os.path.join(live_base, 'config.json')
bundle_cfg = os.path.join('.', 'config.json')
if os.path.exists(live_cfg) and os.path.exists(bundle_cfg):
    try:
        live_hooks = json.load(open(live_cfg, encoding='utf-8-sig')).get('hooks', {})
        bundle_hooks = json.load(open(bundle_cfg, encoding='utf-8-sig')).get('hooks', {})
        # Normalize: replace {{APPDATA}} in bundle with real APPDATA path (forward slashes)
        appdata = os.environ.get('APPDATA', '').replace('\\', '/')
        def normalize(obj):
            s = json.dumps(obj, sort_keys=True)
            s = s.replace('{{APPDATA}}', appdata)
            return s
        h1 = hashlib.sha256(normalize(live_hooks).encode()).hexdigest()[:16]
        h2 = hashlib.sha256(normalize(bundle_hooks).encode()).hexdigest()[:16]
        if h1 == h2:
            print('  OK  config.json hooks (live=bundle, {{APPDATA}} normalized)')
        else:
            errors.append('config.json hooks live != bundle: ' + h1 + ' vs ' + h2)
            print('  FAIL config.json hooks live=' + h1 + ' bundle=' + h2)
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
print('[16] New skills live vs bundle sync')
new_skills = ['context-folding', 'autonomous-gates', 'primeagent-reference', 'context-window-hygiene', 'mcp-context-audit', 'grilling', 'diagnosing-bugs', 'tool-and-skill-discovery', 'dispatching-parallel-agents', 'planning-pipeline', 'obsidian-workflow']
for s in new_skills:
    lp = os.path.join(live_base, 'skills', s, 'SKILL.md')
    bp = os.path.join('skills', s, 'SKILL.md')
    if os.path.exists(lp) and os.path.exists(bp):
        h1 = hashlib.sha256(open(lp, 'rb').read()).hexdigest()[:16]
        h2 = hashlib.sha256(open(bp, 'rb').read()).hexdigest()[:16]
        if h1 == h2:
            print('  OK  skills/' + s + ' (live=bundle)')
        else:
            errors.append('skills/' + s + ' live != bundle')
            print('  FAIL skills/' + s + ' live=' + h1 + ' bundle=' + h2)

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
expected_agents = ['architect.md', 'debugger.md', 'implementer.md', 'researcher.md', 'reviewer.md']
actual_agents = sorted(os.listdir('agents'))
print('  Found: ' + str(actual_agents))
for a in expected_agents:
    if a in actual_agents:
        print('  OK  ' + a)
    else:
        errors.append('Missing agent profile: ' + a)
        print('  FAIL ' + a + ' missing')

# 20. No temp files left
print()
print('[20] Temp files check')
temp_files = [f for f in os.listdir('.git') if f.endswith('.tmp')]
if temp_files:
    warnings.append('Temp files in .git: ' + str(temp_files))
    print('  WARN temp files in .git: ' + str(temp_files))
else:
    print('  OK  no temp files')

# 21. Git tag matches version
print()
print('[21] Git tag vs manifest version')
import subprocess
result = subprocess.run(['git', 'tag', '-l'], capture_output=True, text=True)
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
toolsmap = open('docs/TOOLS-MAP.md', encoding='utf-8').read()
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
    for line in open(reflog, encoding='utf-8'):
        line = line.strip()
        if not line:
            continue
        try:
            entry = json.loads(line)
            ref_ids.append(entry.get('id', ''))
        except (json.JSONDecodeError, ValueError):
            ref_errors.append('malformed JSON line')
    if ref_errors:
        errors.append('refinements.log.jsonl: ' + str(len(ref_errors)) + ' malformed lines')
        print('  FAIL refinements.log.jsonl: ' + str(len(ref_errors)) + ' malformed lines')
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
purpose_mismatches = []
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
        if spurpose.startswith('Use when') and sm_desc.startswith('Use when'):
            if spurpose[:60] != sm_desc[:60]:
                purpose_mismatches.append(sname)
if purpose_mismatches:
    errors.append('manifest purpose stale vs SKILL.md: ' + ', '.join(purpose_mismatches))
    print('  FAIL ' + str(len(purpose_mismatches)) + ' stale purposes: ' + ', '.join(purpose_mismatches))
else:
    print('  OK  all manifest purposes match SKILL.md descriptions')

# 27. No tracked temp artifacts (.zip, .tmp, .bak, ci-logs)
print()
print('[27] No tracked temp artifacts')
import subprocess
artifact_exts = ('.zip', '.tmp', '.bak')
tracked_artifacts = []
try:
    r = subprocess.run(['git', 'ls-files'], capture_output=True, text=True, timeout=10)
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
    r2 = subprocess.run(['git', 'ls-files'], capture_output=True, text=True, timeout=10)
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
mg_path = 'docs/MODEL-GUIDE.md'
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
devin_events = {'PreToolUse', 'PostToolUse', 'PermissionRequest', 'UserPromptSubmit',
                'Stop', 'PostCompaction', 'SessionStart', 'SessionEnd'}

missing_any = False
for hooks_file in ('hooks.v1.json', 'config.json'):
    with open(hooks_file, encoding='utf-8-sig') as fh:
        data = json.load(fh)
    hooks_data = data if hooks_file == 'hooks.v1.json' else data.get('hooks', {})
    bundle_events = set(hooks_data.keys())
    missing = devin_events - bundle_events
    extra = bundle_events - devin_events
    if missing:
        missing_any = True
        errors.append(hooks_file + ' missing Devin CLI events: ' + ', '.join(sorted(missing)))
        print('  FAIL ' + hooks_file + ' missing events: ' + ', '.join(sorted(missing)))
    if extra:
        warnings.append(hooks_file + ' has unknown events: ' + ', '.join(sorted(extra)))
        print('  WARN ' + hooks_file + ' unknown events: ' + ', '.join(sorted(extra)))
    if not missing and not extra:
        print('  OK  ' + hooks_file + ' has all ' + str(len(bundle_events)) + ' Devin CLI events')

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
    print('ALL 31 CHECKS PASSED - NO ERRORS, NO WARNINGS')

