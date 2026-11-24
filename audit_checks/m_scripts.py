import os, re, json, hashlib, sys, py_compile, subprocess, glob
from ._ctx import Ctx, text_hash_matches, _scan_py_files


def c22b(ctx):
    for ctx.s in ctx.scripts_check:
        if not os.path.exists(ctx.s):
            continue
        content = open(ctx.s, encoding='utf-8-sig').read()
        issues = []
        if ctx.s.endswith('.ps1'):
            # Parameters must include DryRun, Force, Backup, RestoreSecrets/Commit/Push/NoMask
            expected = ['[switch]$DryRun']
            if 'export' in ctx.s:
                expected = ['[switch]$DryRun', '[switch]$Commit', '[switch]$Push', '[switch]$NoMask']
            else:
                expected = ['[switch]$DryRun', '[switch]$Force', '[switch]$Backup', '[switch]$RestoreSecrets']
            for p in expected:
                if p not in content:
                    issues.append('missing ' + p)
            # Must have a no-mask/push guard
            if 'export' in ctx.s:
                if 'NoMask' not in content or 'Push' not in content:
                    issues.append('missing NoMask/Push parameter or guard')
            # Placeholder must exist in bundle (collapsed) and be expanded in install
            if 'install' in ctx.s:
                if '{{APPDATA}}' not in content:
                    issues.append('missing {{APPDATA}} placeholder expansion')
            else:
                if 'normalize_config_paths' not in content and '{{APPDATA}}' not in content:
                    issues.append('missing config path normalization')
        else:
            # Bash scripts
            expected = ['DRY_RUN=', 'FORCE=', 'BACKUP=', 'RESTORE_SECRETS='] if 'install' in ctx.s else ['DRY_RUN=', 'COMMIT=', 'PUSH=', 'NO_MASK=']
            for p in expected:
                if p not in content:
                    issues.append('missing ' + p)
            # Shebang
            if not content.startswith('#!'):
                issues.append('missing shebang')
            # Placeholder handling
            if 'install' in ctx.s:
                if '{{APPDATA}}' not in content:
                    issues.append('missing {{APPDATA}} placeholder handling')
            else:
                if 'normalize_config_paths' not in content and '{{APPDATA}}' not in content:
                    issues.append('missing config path normalization')
        if issues:
            ctx.errors.append(ctx.s + ': ' + ', '.join(issues))
            print('  FAIL ' + ctx.s + ': ' + ', '.join(issues))
        else:
            print('  OK  ' + ctx.s + ' structure')

    # 23. .gitattributes
    print()


def c23(ctx):
    ga = open('.gitattributes', encoding='utf-8').read()
    if '*.sh' in ga and '*.ps1' in ga:
        print('  OK  line endings configured')
    else:
        ctx.warnings.append('.gitattributes may be incomplete')
        print('  WARN .gitattributes incomplete')

    # 24. TOOLS-MAP.md and SKILL-TIERS.md stale counts
    print()


def c24(ctx):
    toolsmap = open('.devin/docs/TOOLS-MAP.md', encoding='utf-8').read()
    doc_checks = [
        ('TOOLS-MAP.md skills count', str(ctx.skill_count) + ' skills', str(ctx.skill_count) + ' skills' in toolsmap),
        ('TOOLS-MAP.md scripts count', str(len(ctx.script_files)) + ' scripts', str(len(ctx.script_files)) + ' scripts' in toolsmap),
        ('TOOLS-MAP.md hook events (8)', '8 eventos', '8 eventos' in toolsmap),
        ('TOOLS-MAP.md tool count (28)', '28 in TOOLS-MAP', ('28 ferramentas' in toolsmap or '19/28' in toolsmap)),
        ('TOOLS-MAP.md excluded tools (9)', '9 in TOOLS-MAP', '9 excluídas' in toolsmap),
        ('README.md diagram skills count', str(ctx.skill_count) + ' skills', str(ctx.skill_count) + ' skills' in ctx.readme),
        ('README.md diagram hook events (8)', '8 events', '8 events' in ctx.readme),
    ]
    # skill_count is dynamic (from disk), so these checks auto-adjust to 46 after legacy cleanup
    for label, expected, ok in doc_checks:
        status = 'OK' if ok else 'FAIL'
        print('  ' + status + ' ' + label + ' (expected: ' + expected + ')')
        if not ok:
            ctx.errors.append(label + ' stale: expected ' + expected)

    # 25. Refinement log ID uniqueness
    print()


def c25(ctx):
    reflog = os.path.join('.devin', 'refinements.log.jsonl')
    if os.path.exists(reflog):
        ref_ids = []
        ref_errors = []
        required_ref_keys = ['id', 'timestamp', 'type', 'target', 'evidence', 'status']
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
            ctx.errors.append('refinements.log.jsonl: ' + str(len(ref_errors)) + ' malformed lines')
            print('  FAIL refinements.log.jsonl: ' + str(len(ref_errors)) + ' malformed lines')
        elif missing_evidence:
            ctx.warnings.append('refinements.log.jsonl entries missing evidence: ' + '; '.join(missing_evidence[:5]))
            print('  WARN refinements.log.jsonl entries missing evidence: ' + str(len(missing_evidence)))
        else:
            from collections import Counter
            dups = {k: v for k, v in Counter(ref_ids).items() if v > 1}
            if dups:
                ctx.errors.append('refinements.log.jsonl: ' + str(len(dups)) + ' duplicate IDs: ' + ', '.join(sorted(dups.keys())))
                print('  FAIL refinements.log.jsonl: ' + str(len(dups)) + ' duplicate IDs')
            else:
                print('  OK  refinements.log.jsonl: ' + str(len(ref_ids)) + ' unique IDs')
    else:
        print('  SKIP refinements.log.jsonl not found')

    # 26. Manifest purpose vs SKILL.md description sync
    print()


def c26(ctx):
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
        ctx.errors.append('manifest purpose stale vs SKILL.md: ' + ', '.join(purpose_mismatches))
        print('  FAIL ' + str(len(purpose_mismatches)) + ' stale purposes: ' + ', '.join(purpose_mismatches))
    else:
        print('  OK  all manifest purposes match SKILL.md descriptions')
    if prefix_missing:
        ctx.warnings.append('skills missing "Use when" prefix: ' + ', '.join(prefix_missing))
        print('  WARN ' + str(len(prefix_missing)) + ' skills lack "Use when" prefix: ' + ', '.join(prefix_missing))

    # 27. No tracked temp artifacts (.zip, .tmp, .bak, ci-logs)
    print()


def c27(ctx):
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
        ctx.errors.append('tracked temp artifacts: ' + ', '.join(tracked_artifacts))
        print('  FAIL ' + str(len(tracked_artifacts)) + ' tracked artifacts: ' + ', '.join(tracked_artifacts))

    # 28. No tracked credential/secret files
    print()


def c28(ctx):
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
        ctx.errors.append('CRITICAL: tracked credential files: ' + ', '.join(tracked_creds))
        print('  FAIL ' + str(len(tracked_creds)) + ' tracked credential files: ' + ', '.join(tracked_creds))

    # 29. All arXiv refs in scripts/ and tests/ must be in MODEL-GUIDE.md source table
    print()
