import os, re, json, hashlib, sys, py_compile, subprocess, glob
from ._ctx import Ctx, text_hash_matches, _scan_py_files


def c1(ctx):
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
            ctx.errors.append('JSON ' + jf + ': ' + str(e))
            print('  FAIL ' + jf + ': ' + str(e))

    # 2. All Python scripts compile
    print()


def c2(ctx):
    ctx.py_files = []
    for root, dirs, files in os.walk('.'):
        dirs[:] = [d for d in dirs if d not in ('.git', '.venv', 'node_modules', 'target', '__pycache__')]
        for f in files:
            if f.endswith('.py'):
                ctx.py_files.append(os.path.join(root, f))
    for pf in sorted(ctx.py_files):
        try:
            compile(open(pf, 'rb').read(), pf, 'exec')
            print('  OK  ' + pf)
        except (SyntaxError, ValueError) as e:
            ctx.errors.append('Python ' + pf + ': ' + str(e))
            print('  FAIL ' + pf)

    # 2b. Hook scripts must have __main__ guard (detects muted/empty main)
    print()


def c2b(ctx):
    hook_scripts = [f for f in ctx.py_files if os.path.normpath(f).startswith('scripts') and f.endswith('.py')]
    for hs in sorted(hook_scripts):
        content = open(hs, encoding='utf-8').read()
        if '__name__' not in content:
            ctx.errors.append(hs + ': missing if __name__ == "__main__" guard')
            print('  FAIL ' + hs + ': missing __main__ guard')
        else:
            print('  OK  ' + hs)

    # 3. All skills have valid frontmatter
    print()


_FM_KEY_RE = re.compile(r"^([A-Za-z][A-Za-z0-9_-]*):\s*(.*)$")
_FM_YAML_BREAKERS = (
    (re.compile(r":\s"), "': ' inside an unquoted value is a new mapping key to YAML"),
    (re.compile(r"\s#"), "' #' inside an unquoted value starts a YAML comment"),
    (re.compile(r"^[*!%@`&?,:|]"), "value starts with a YAML indicator char"),
    (re.compile(r"^-\s"), "leading '- ' turns the value into a YAML sequence"),
)


def _fm_naive_scalar(value):
    v = value.strip()
    if len(v) >= 2 and v[0] == v[-1] and v[0] in "\"'":
        return v[1:-1]
    if v[:1] in (">", "|"):
        return v[2:].lstrip() if v[1:2] in ("-", "+") else v[1:].lstrip()
    return v


def _frontmatter_yaml_issues(frontmatter_text):
    """Strict-YAML gate (issue #721): the CLI skills loader parses
    frontmatter as real YAML and drops the skill on a parse error or a
    silently truncated value, while naive key: value checks pass."""
    naive = {}
    last_key = None
    for line in frontmatter_text.split("\n"):
        if not line.strip():
            continue
        m = _FM_KEY_RE.match(line)
        if m and not line[0].isspace():
            last_key = m.group(1).strip()
            naive[last_key] = m.group(2).strip()
        elif last_key is not None:
            naive[last_key] = (naive[last_key] + " " + line.strip()).strip()
    try:
        import yaml
    except ImportError:
        yaml = None
    if yaml is not None:
        try:
            parsed = yaml.safe_load(frontmatter_text)
        except Exception as exc:
            return ["frontmatter is not valid YAML: " + str(exc).split("\n")[0]]
        if not isinstance(parsed, dict):
            return ["frontmatter is not a YAML mapping"]
        issues = []
        for key, nv in naive.items():
            pv = parsed.get(key)
            if isinstance(pv, str) and " ".join(_fm_naive_scalar(nv).split()) != " ".join(pv.split()):
                issues.append("'" + key + "': value differs under strict YAML")
        return issues
    issues = []
    for key, value in naive.items():
        if not value or value[0] in "\"'[{>|":
            continue
        for pat, why in _FM_YAML_BREAKERS:
            if pat.search(value):
                issues.append("'" + key + "': " + why)
                break
    return issues


def c3(ctx):
    ctx.skills_dir = 'skills'
    ctx.skill_count = 0
    for skill_name in sorted(os.listdir(ctx.skills_dir)):
        skill_path = os.path.join(ctx.skills_dir, skill_name, 'SKILL.md')
        if not os.path.exists(skill_path):
            ctx.errors.append(skill_name + ': SKILL.md missing')
            print('  FAIL ' + skill_name + ': SKILL.md missing')
            continue
        ctx.skill_count += 1
        with open(skill_path, encoding='utf-8') as f:
            content = f.read()
        issues = []
        fm_match = re.match(r'^---\s*\n(.*?)\n---', content, re.S)
        if fm_match:
            issues.extend(_frontmatter_yaml_issues(fm_match.group(1)))
        if not re.search(r'^name:\s*' + re.escape(skill_name), content, re.M):
            issues.append('name mismatch')
        if 'description:' not in content:
            issues.append('description missing')
        if 'Use when' not in content:
            issues.append('no Use when')
        if issues:
            ctx.errors.append(skill_name + ': ' + str(issues))
            print('  FAIL ' + skill_name + ': ' + str(issues))
        else:
            print('  OK  ' + skill_name)
    print('  Total: ' + str(ctx.skill_count) + ' skills')

    # 4. Manifest sync with disk
    print()


def c4(ctx):
    ctx.manifest = json.load(open('manifest.json', encoding='utf-8-sig'))
    manifest_names = set(s['name'] for s in ctx.manifest.get('skills', []))
    disk_names = set(os.listdir(ctx.skills_dir))
    if manifest_names != disk_names:
        ctx.errors.append('Manifest mismatch')
        print('  FAIL manifest_only=' + str(manifest_names - disk_names))
        print('  FAIL disk_only=' + str(disk_names - manifest_names))
    else:
        print('  OK  ' + str(len(manifest_names)) + ' skills = ' + str(len(disk_names)) + ' on disk')
    declared_skill_count = ctx.manifest.get('skill_count')
    if declared_skill_count != ctx.skill_count:
        ctx.errors.append('manifest skill_count mismatch')
        print('  FAIL skill_count declared=' + str(declared_skill_count) + ' actual=' + str(ctx.skill_count))
    else:
        print('  OK  skill_count = ' + str(ctx.skill_count))

    # 5. Manifest version
    print()


def c5(ctx):
    ctx.ver = ctx.manifest.get('version', 'MISSING')
    print('  version: ' + str(ctx.ver))
    if ctx.ver == 'MISSING':
        ctx.warnings.append('Manifest version is missing')

    # 6. AGENTS.md rule count
    print()
