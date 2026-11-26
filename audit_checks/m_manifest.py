import os, re, json, hashlib, sys, py_compile, subprocess, glob
from ._ctx import Ctx, text_hash_matches, _scan_py_files


def c8(ctx):
    ctx.script_files = [f for f in os.listdir('scripts') if f.endswith('.py')]
    print('  Scripts: ' + str(ctx.script_files))
    # Manual-run scripts (not hooks) — these are run on-demand, not via config.json hooks
    manual_scripts = {'validate-refinement-evidence.py', 'validate-skill-format.py', 'render-user-hooks.py', '_hookrun.py', '_gitscan.py', 'spec-consistency.py', 'install-ledger.py', 'check-tools.py', 'roadmap-board.py', 'status_vocab.py', 'focus.py', 'rules-coverage.py', 'pulse.py', 'simplify-scan.py', 'graph-query.py', 'subagent-trace.py', 'done-evaluator.py', 'ship-metrics.py', 'changelog-refs.py', 'bundle_envelope.py', 'phase-zero.py', 'log-refinement.py', 'laya-shadow-report.py', 'sync-manifest.py', 'behavioral-eval.py'}
    for ctx.s in ctx.script_files:
        if ctx.s not in ctx.scripts_referenced and ctx.s not in manual_scripts:
            ctx.warnings.append(ctx.s + ' not referenced in hooks.v1.json')
            print('  WARN ' + ctx.s + ' not referenced in hooks')
        elif ctx.s in manual_scripts:
            print('  OK  ' + ctx.s + ' (manual-run, not a hook)')

    # 9. README counts match reality
    print()


def c9(ctx):
    ctx.readme = open('README.md', encoding='utf-8').read()
    agent_count = len([f for f in os.listdir('agents') if f.endswith('.md')])
    checks = [
        (str(ctx.skill_count) + ' skills', str(ctx.skill_count) + ' skills' in ctx.readme),
        ('rules-' + str(len(ctx.rules_found)) + ' badge', ('rules-' + str(len(ctx.rules_found)) + '-') in ctx.readme),
        (str(agent_count) + ' agents (disk vs manifest)', agent_count == ctx.manifest.get('agent_count')),
        (str(len(ctx.script_files)) + ' scripts', str(len(ctx.script_files)) + ' scripts' in ctx.readme),
    ]
    for label, ok in checks:
        status = 'OK' if ok else 'FAIL'
        print('  ' + status + ' ' + label)
        if not ok:
            ctx.errors.append('README count wrong: ' + label)

    # 9b. manifest.json scripts list consistency
    print()


def c9b(ctx):
    ctx.manifest = json.load(open('manifest.json', encoding='utf-8'))
    manifest_scripts = ctx.manifest.get('scripts', [])
    manifest_script_count = ctx.manifest.get('script_count', 0)
    # Separate .py scripts (counted in script_count) from other extensions (helpers)
    manifest_py_scripts = [s for s in manifest_scripts if s['name'].endswith('.py')]
    manifest_other_scripts = [s for s in manifest_scripts if not s['name'].endswith('.py')]
    if len(manifest_scripts) == 0:
        ctx.errors.append('manifest.json has script_count but no scripts array')
        print('  FAIL manifest.json scripts array empty/missing')
    elif len(manifest_py_scripts) != manifest_script_count:
        ctx.errors.append('manifest.json script_count (' + str(manifest_script_count) + ') != .py scripts in array (' + str(len(manifest_py_scripts)) + ')')
        print('  FAIL manifest.json script_count != .py scripts in array')
    elif len(manifest_py_scripts) != len(ctx.script_files):
        ctx.errors.append('manifest.json .py scripts (' + str(len(manifest_py_scripts)) + ') != scripts/ dir .py (' + str(len(ctx.script_files)) + ')')
        print('  FAIL manifest.json .py scripts != scripts/ dir')
    else:
        # Check each manifest script exists on disk
        missing = [s['name'] for s in manifest_scripts if not os.path.isfile(os.path.join('scripts', s['name']))]
        if missing:
            ctx.errors.append('manifest.json lists scripts not on disk: ' + ', '.join(missing))
            print('  FAIL manifest scripts not on disk: ' + ', '.join(missing))
        else:
            print('  OK  manifest.json scripts list consistent (' + str(len(manifest_py_scripts)) + ' .py + ' + str(len(manifest_other_scripts)) + ' other)')
        # Check script hashes
        hash_mismatch = []
        for ctx.s in manifest_scripts:
            if ctx.s['name'].endswith('.py') and ctx.s.get('export_hash'):
                path = os.path.join('scripts', ctx.s['name'])
                if os.path.isfile(path):
                    if not text_hash_matches(path, ctx.s['export_hash']):
                        hash_mismatch.append(ctx.s['name'])
        if hash_mismatch:
            ctx.warnings.append('manifest script hash mismatch: ' + ', '.join(hash_mismatch))
            print('  WARN script hash mismatch: ' + ', '.join(hash_mismatch))
        else:
            print('  OK  manifest script hashes match')

    # 9c. manifest.json agents list and hashes
    print()


def c9c(ctx):
    manifest_agents = ctx.manifest.get('agents', [])
    agent_files = [f for f in os.listdir('agents') if f.endswith('.md')]
    if len(manifest_agents) != len(agent_files):
        ctx.errors.append('manifest agent_count mismatch')
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
            ctx.errors.append('manifest agents missing on disk: ' + ', '.join(missing))
            print('  FAIL agents missing: ' + ', '.join(missing))
        elif hash_mismatch:
            ctx.warnings.append('manifest agent hash mismatch: ' + ', '.join(hash_mismatch))
            print('  WARN agent hash mismatch: ' + ', '.join(hash_mismatch))
        else:
            print('  OK  manifest agents consistent (' + str(len(manifest_agents)) + ' agents)')

    # 9d. manifest.json skill export_hash drift (warning level, repair
    # with scripts/sync-manifest.py; reproduced gap 2026-11-26: 73 stale
    # skill hashes accumulated because detection covered only scripts and
    # agents)
    print()


def c9d(ctx):
    manifest_skills = ctx.manifest.get('skills', [])
    hash_mismatch = []
    missing = []
    no_hash = []
    for s in manifest_skills:
        path = os.path.join('skills', s['name'], 'SKILL.md')
        if not os.path.isfile(path):
            missing.append(s['name'])
        elif not s.get('export_hash'):
            no_hash.append(s['name'])
        elif not text_hash_matches(path, s['export_hash']):
            hash_mismatch.append(s['name'])
    if missing:
        ctx.errors.append('manifest skills missing on disk: ' + ', '.join(missing))
        print('  FAIL skills missing: ' + ', '.join(missing))
    if no_hash:
        ctx.warnings.append('manifest skills without export_hash (repair: python scripts/sync-manifest.py): ' + ', '.join(no_hash))
        print('  WARN skills missing export_hash: ' + ', '.join(no_hash))
    if hash_mismatch:
        ctx.warnings.append('manifest skill hash mismatch (repair: python scripts/sync-manifest.py): ' + ', '.join(hash_mismatch))
        print('  WARN skill hash mismatch: ' + ', '.join(hash_mismatch))
    if not missing and not no_hash and not hash_mismatch:
        print('  OK  manifest skill hashes consistent (' + str(len(manifest_skills)) + ' skills)')

    # 10. No unmasked secrets
    print()


def c10(ctx):
    if os.path.exists('credentials.toml'):
        try:
            cred = open('credentials.toml', encoding='utf-8').read()
        except (OSError, IOError) as e:
            ctx.warnings.append('credentials.toml exists but could not be read: ' + str(e))
            cred = ''
        if 'MASKED' not in cred and cred.strip():
            ctx.errors.append('credentials.toml may have unmasked secrets')
            print('  FAIL credentials.toml unmasked')
        else:
            print('  OK  credentials.toml masked')
    else:
        print('  OK  credentials.toml not present (gitignored, not tracked)')

    ctx.config = json.load(open('config.json', encoding='utf-8-sig'))
    org_id = ctx.config.get('devin', {}).get('org_id', '')
    if org_id == 'MASKED':
        print('  OK  config.json org_id masked')
    else:
        ctx.warnings.append('config.json org_id may not be masked: ' + str(org_id))
        print('  WARN config.json org_id = ' + str(org_id))

    ctx.mcp = json.load(open('mcp_config.json', encoding='utf-8-sig'))
    ctx.mcp_servers = ctx.mcp.get('mcpServers', {})
    mcp_has_secrets = False
    for sname, scfg in ctx.mcp_servers.items():
        for k, v in scfg.items():
            if any(s in k.lower() for s in ['token', 'key', 'secret', 'password', 'credential']):
                if v != 'MASKED':
                    mcp_has_secrets = True
                    print('  WARN mcp ' + sname + '.' + k + ' = ' + str(v))
    if mcp_has_secrets:
        ctx.warnings.append('mcp_config.json has unmasked secret-like fields')
    else:
        print('  OK  mcp_config.json no secret-like fields')

    # 10b. mcp_config.json schema validation
    print()
