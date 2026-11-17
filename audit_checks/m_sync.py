import os, re, json, hashlib, sys, py_compile, subprocess, glob
from ._ctx import Ctx, text_hash_matches, _scan_py_files


def c16(ctx):
    new_skills = sorted(d for d in os.listdir('skills') if os.path.isdir(os.path.join('skills', d)))
    for ctx.s in new_skills:
        lp = os.path.join(ctx.live_base, 'skills', ctx.s, 'SKILL.md')
        bp = os.path.join('skills', ctx.s, 'SKILL.md')
        if os.path.exists(lp) and os.path.exists(bp):
            h1 = hashlib.sha256(open(lp, 'rb').read()).hexdigest()[:16]
            h2 = hashlib.sha256(open(bp, 'rb').read()).hexdigest()[:16]
            if h1 == h2:
                print('  OK  skills/' + ctx.s + ' (live=bundle)')
            else:
                ctx.warnings.append('skills/' + ctx.s + ' live != bundle')
                print('  WARN skills/' + ctx.s + ' live=' + h1 + ' bundle=' + h2)

    # 17. CHANGELOG version matches manifest
    print()


def c17(ctx):
    changelog = open('CHANGELOG.md', encoding='utf-8').read()
    if ctx.ver != 'MISSING' and ctx.ver in changelog:
        print('  OK  CHANGELOG and manifest both at ' + str(ctx.ver))
    else:
        ctx.warnings.append('Version mismatch')
        print('  WARN CHANGELOG has ' + str(ctx.ver) + ': ' + str(ctx.ver in changelog) + ', manifest: ' + str(ctx.ver))

    # 18. README badges
    print()


def c18(ctx):
    expected_skills_badge = 'skills-' + str(ctx.skill_count)
    if expected_skills_badge in ctx.readme:
        print('  OK  skills badge = ' + str(ctx.skill_count))
    else:
        ctx.errors.append('README skills badge wrong (expected ' + expected_skills_badge + ')')
        print('  FAIL skills badge')
    expected_rules_badge = 'rules-' + str(len(ctx.rules_found))
    if expected_rules_badge in ctx.readme:
        print('  OK  rules badge = ' + str(len(ctx.rules_found)))
    else:
        ctx.errors.append('README rules badge wrong (expected ' + expected_rules_badge + ')')
        print('  FAIL rules badge')
    expected_version_badge = 'version-' + str(ctx.ver)
    if expected_version_badge in ctx.readme:
        print('  OK  version badge = ' + str(ctx.ver))
    else:
        ctx.warnings.append('README version badge may be wrong (expected ' + expected_version_badge + ')')
        print('  WARN version badge')

    # 19. agents/ profiles
    print()


def c19(ctx):
    expected_agents = sorted(f for f in os.listdir('agents') if f.endswith('.md'))
    manifest_agents = sorted(a['name'] + '.md' for a in ctx.manifest.get('agents', []))
    print('  Found: ' + str(expected_agents))
    for a in expected_agents:
        if a in manifest_agents:
            print('  OK  ' + a)
        else:
            ctx.errors.append('Agent not in manifest: ' + a)
            print('  FAIL ' + a + ' not in manifest')
    for a in manifest_agents:
        if a not in expected_agents:
            ctx.errors.append('Manifest agent missing on disk: ' + a)
            print('  FAIL ' + a + ' in manifest but not on disk')

    # 20. No temp files left
    print()


def c20(ctx):
    import subprocess
    _git_dir = subprocess.run(['git', 'rev-parse', '--git-dir'], capture_output=True, text=True, encoding="utf-8", errors="replace").stdout.strip()
    if _git_dir and os.path.isdir(_git_dir):
        temp_files = [f for f in os.listdir(_git_dir) if f.endswith('.tmp')]
    else:
        temp_files = []
    if temp_files:
        ctx.warnings.append('Temp files in .git: ' + str(temp_files))
        print('  WARN temp files in .git: ' + str(temp_files))
    else:
        print('  OK  no temp files')

    # 21. Git tag matches version
    print()


def c21(ctx):
    import subprocess
    result = subprocess.run(['git', 'tag', '-l'], capture_output=True, text=True, encoding="utf-8", errors="replace")
    tags = result.stdout.strip().split('\n') if result.stdout.strip() else []
    print('  Tags: ' + str(tags))
    expected_tag = 'v' + str(ctx.ver)
    if expected_tag in tags:
        print('  OK  ' + expected_tag + ' tag exists')
    elif 'v2.1.0' in tags:
        print('  OK  v2.1.0 tag exists (prior version)')
        ctx.warnings.append('v' + str(ctx.ver) + ' tag not yet created')
    else:
        ctx.warnings.append(expected_tag + ' tag missing')
        print('  WARN ' + expected_tag + ' tag missing')

    # 22. Export scripts exist and are executable
    print()


def c22(ctx):
    ctx.scripts_check = ['export.ps1', 'export.sh', 'install.ps1', 'install.sh']
    for ctx.s in ctx.scripts_check:
        if os.path.exists(ctx.s):
            print('  OK  ' + ctx.s)
        else:
            ctx.errors.append(ctx.s + ' missing')
            print('  FAIL ' + ctx.s + ' missing')

    # 22b. Structural validation for export/install scripts
    print()
