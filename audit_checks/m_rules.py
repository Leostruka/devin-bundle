import os, re, json, hashlib, sys, py_compile, subprocess, glob
from ._ctx import Ctx, text_hash_matches, _scan_py_files


def c6(ctx):
    with open('AGENTS.md', encoding='utf-8-sig') as f:
        ctx.agents = f.read()
    # Index bullets declare rules (merged rules appear as "N. **-> Rule M**");
    # section bodies are "## N." (pinned) and "### N." (non-pinned) headings.
    ctx.index_rules = [int(n) for n in re.findall(r'(?m)^(\d+)\. \*\*', ctx.agents)]
    alias_targets = {
        int(n): int(m)
        for n, m in re.findall(
            r'(?m)^(\d+)\. \*\*(?:->|→)\s*Rule\s+(\d+)\*\*', ctx.agents)
    }
    body_numbers = [int(n) for n in re.findall(r'(?m)^#{2,3} (\d+)\.', ctx.agents)]
    body_set = set(body_numbers)
    index_set = set(ctx.index_rules)
    ctx.rules_found = sorted(index_set)
    print('  Rules found: ' + str(ctx.rules_found))
    expected_rules = ctx.manifest.get('rule_count', 26)
    if len(ctx.index_rules) != expected_rules:
        ctx.errors.append('Expected ' + str(expected_rules) + ' rules, found ' + str(len(ctx.index_rules)))
        print('  FAIL expected ' + str(expected_rules) + ', found ' + str(len(ctx.index_rules)))
    else:
        print('  OK  ' + str(len(ctx.index_rules)) + ' rules present')
    declared_rule_count = ctx.manifest.get('rule_count')
    if declared_rule_count != len(ctx.index_rules):
        ctx.errors.append('manifest rule_count mismatch')
        print('  FAIL rule_count declared=' + str(declared_rule_count) + ' actual=' + str(len(ctx.index_rules)))
    else:
        print('  OK  rule_count = ' + str(len(ctx.index_rules)))

    # Every declared rule that is not a merged alias must have a body section;
    # aliases must point at a declared rule number.
    missing_bodies = sorted(n for n in index_set
                            if n not in alias_targets and n not in body_set)
    if missing_bodies:
        ctx.errors.append('Index rules without a body section: ' + str(missing_bodies))
        print('  FAIL index rules without bodies: ' + str(missing_bodies))
    else:
        print('  OK  every non-alias rule has a body section')
    dangling = sorted(n for n, m in alias_targets.items() if m not in index_set)
    if dangling:
        ctx.errors.append('Alias rules pointing at undeclared rules: ' + str(dangling))
        print('  FAIL dangling aliases: ' + str(dangling))
    else:
        print('  OK  all index aliases resolve')

    # 6c. Warn if AGENTS.md is large (context window budget)
    print()


def c6c(ctx):
    agents_size = len(ctx.agents)
    estimated_tokens = agents_size // 4
    AGENTS_TOKEN_BUDGET = 10000
    print('  AGENTS.md size: ' + str(agents_size) + ' chars (~' + str(estimated_tokens) + ' tokens)')
    if estimated_tokens > AGENTS_TOKEN_BUDGET:
        ctx.warnings.append('AGENTS.md exceeds token budget: ~' + str(estimated_tokens) + ' > ' + str(AGENTS_TOKEN_BUDGET))
        print('  WARN AGENTS.md exceeds ' + str(AGENTS_TOKEN_BUDGET) + ' token budget')
    else:
        print('  OK  AGENTS.md within budget')

    # 6b. Detect missing rule numbers or duplicate numbering (only flag if count is off or duplicates exist)
    all_numbers = set(range(1, 30))
    found_numbers = set(ctx.rules_found)
    # A gap is only a problem if it causes the total count to diverge from the manifest.
    # Intentional gaps (e.g. rule 6 omitted) are allowed as long as rule_count matches.
    duplicates = sorted(n for n in set(ctx.index_rules)
                        if ctx.index_rules.count(n) > 1)
    if duplicates:
        ctx.errors.append('Duplicate rule numbers in AGENTS.md: ' + str(duplicates))
        print('  FAIL duplicate rule numbers: ' + str(duplicates))
    else:
        print('  OK  no duplicate rule numbers')

    # 7. config.json hooks references valid scripts
    print()


def c7(ctx):
    ctx.config = json.load(open('config.json', encoding='utf-8-sig'))
    ctx.hooks = json.load(open('hooks.v1.json', encoding='utf-8-sig'))
    if not ctx.hooks:
        ctx.errors.append('hooks.v1.json is empty')
        print('  FAIL hooks.v1.json empty')
    ctx.scripts_referenced = set()
    for event in ctx.hooks:
        for entry in ctx.hooks[event]:
            for h in entry.get('hooks', []):
                cmd = h.get('command', '')
                # Match scripts/<name>.py with either slash direction
                m = re.search(r'scripts[/\\]([a-z-]+\.py)', cmd)
                if m:
                    ctx.scripts_referenced.add(m.group(1))
                # Warn if command uses %APPDATA% (not expanded by hook shell)
                if '%APPDATA%' in cmd:
                    ctx.warnings.append('Hook command uses %APPDATA% (not expanded): ' + cmd[:80])
                    print('  WARN %APPDATA% in command (use {{APPDATA}} or absolute path)')
    # Follow one level of indirection: consolidated guards reference check modules
    # in their internal lists (executed in-process via _hookrun).
    for ctx.s in list(ctx.scripts_referenced):
        sp = os.path.join('scripts', ctx.s)
        if os.path.exists(sp):
            src = open(sp, encoding='utf-8').read()
            for m in re.finditer(r"['\"]([a-z-]+\.py)['\"]", src):
                ctx.scripts_referenced.add(m.group(1))
    for ctx.s in sorted(ctx.scripts_referenced):
        path = os.path.join('scripts', ctx.s)
        if os.path.exists(path):
            print('  OK  ' + ctx.s + ' exists')
        else:
            ctx.errors.append('Hook references ' + ctx.s + ' but file missing')
            print('  FAIL ' + ctx.s + ' missing')

    # 7b. config.json + hooks.v1.json schema validation
    print()


def c7b(ctx):
    HOOK_EVENTS = ['PreToolUse', 'PostToolUse', 'PreCompact', 'PostCompact', 'PostCompaction', 'UserPromptSubmit', 'SessionStart', 'SessionEnd', 'Stop', 'PermissionRequest']
    config_errors = []
    if not isinstance(ctx.config.get('version'), int):
        config_errors.append('version must be an integer')
    for key in ['devin', 'agent', 'read_config_from', 'shell', 'hooks']:
        if not isinstance(ctx.config.get(key), dict):
            config_errors.append('missing or invalid top-level key: ' + key)
    if 'attribution' not in ctx.config or not isinstance(ctx.config['attribution'], bool):
        config_errors.append('attribution must be a boolean')
    for event in ctx.hooks:
        if event not in HOOK_EVENTS:
            config_errors.append('unknown hook event: ' + event)
        if not isinstance(ctx.hooks[event], list):
            config_errors.append('hooks[' + event + '] must be a list')
        else:
            for entry in ctx.hooks[event]:
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
            ctx.errors.append('config.json schema: ' + e)
            print('  FAIL ' + e)
    else:
        print('  OK  config.json schema valid')

    # 8. All scripts in scripts/ dir
    print()


