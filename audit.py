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
if ver != '2.5.0':
    warnings.append('Manifest version is ' + str(ver) + ', expected 2.5.0')

# 6. AGENTS.md rule count
print()
print('[6] AGENTS.md rules')
with open('AGENTS.md', encoding='utf-8-sig') as f:
    agents = f.read()
rules_found = []
for i in range(1, 22):
    # Anchor to start of line to avoid false positives (e.g. "6. **" in "16. **")
    if '\n' + str(i) + '. **' in agents:
        rules_found.append(i)
print('  Rules found: ' + str(rules_found))
if len(rules_found) != 20:
    errors.append('Expected 20 rules, found ' + str(len(rules_found)))
else:
    print('  OK  20 rules present')

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
    ('48 skills', skill_count == 48),
    ('20 rules', len(rules_found) == 20),  # 1-5,7-21 (Rule 6 removed)
    ('5 agents', agent_count == 5),
    ('11 scripts', len(script_files) == 11),
]
for label, ok in checks:
    status = 'OK' if ok else 'FAIL'
    print('  ' + status + ' ' + label)
    if not ok:
        errors.append('README count wrong: ' + label)

# 10. No unmasked secrets
print()
print('[10] Secrets check')
cred = open('credentials.toml', encoding='utf-8').read()
if 'MASKED' not in cred and cred.strip():
    errors.append('credentials.toml may have unmasked secrets')
    print('  FAIL credentials.toml unmasked')
else:
    print('  OK  credentials.toml masked')

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
live_base = r'C:\Users\leand\AppData\Roaming\devin'
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
            errors.append('scripts/' + s + ' live != bundle')
            print('  FAIL scripts/' + s + ' live=' + h1 + ' bundle=' + h2)

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
if '2.5.0' in changelog and ver == '2.5.0':
    print('  OK  CHANGELOG and manifest both at 2.5.0')
else:
    warnings.append('Version mismatch')
    print('  WARN CHANGELOG has 2.5.0: ' + str('2.5.0' in changelog) + ', manifest: ' + str(ver))

# 18. README badges
print()
print('[18] README badges')
if 'skills-48' in readme:
    print('  OK  skills badge = 48')
else:
    errors.append('README skills badge wrong')
    print('  FAIL skills badge')
if 'rules-20' in readme:
    print('  OK  rules badge = 20')
else:
    errors.append('README rules badge wrong')
    print('  FAIL rules badge')
if 'version-2.5.0' in readme:
    print('  OK  version badge = 2.5.0')
else:
    warnings.append('README version badge may be wrong')
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
    print('ALL 23 CHECKS PASSED - NO ERRORS, NO WARNINGS')
