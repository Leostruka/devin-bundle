#!/usr/bin/env python3
'''devin-manager — deterministic evidence-first `.devin/` audit and planning.

Conceptually inspired by DeepPaperNote's one-source-at-a-time, evidence-first
note workflow. No external code, no PDF dependencies, no network calls.
See `skills/devin-manager/SKILL.md` for source/license attribution.

Usage:
    python devin-manager.py scan [PROJECT]
    python devin-manager.py explain [PROJECT] ARTIFACT
    python devin-manager.py diff [PROJECT_A] [PROJECT_B]
    python devin-manager.py doctor [PROJECT]
    python devin-manager.py plan [PROJECT] [--write] [--approve]
'''
import argparse, hashlib, json, os, re, sys
from pathlib import Path

# Devin CLI lifecycle events (from Devin docs)
DEVIN_EVENTS = {
    'PreToolUse', 'PostToolUse', 'PermissionRequest', 'UserPromptSubmit',
    'Stop', 'PostCompaction', 'SessionStart', 'SessionEnd',
}

NOTE_SUBDIR = Path('notes/devin-manager')

# Reference kind strength (lower is stronger; used for source+target dedup)
KIND_STRENGTH = {
    'source': 0,
    'markdown_link': 1,
    'wikilink': 2,
    'command': 3,
    'mention': 4,
}

# Reference extraction regexes
LINK_RE = re.compile(r'!?\[[^\]]*\]\(([^)\s`]+)(?:\s+[^)]*)?\)')
WIKI_RE = re.compile(r'\[\[([^\]|]+)(?:\|[^\]]+)?\]\]')
SOURCE_RE = re.compile(r'^(?:[-*]\s+)?source:\s*([^\s\n:,]+)', re.MULTILINE)
MENTION_RE = re.compile(
    r'(?<![\w./])(skills|rules|scripts|hooks|memory|ledgers|mcp_config)(?:\.json)?[/\\]([^\s)\]"\',;:`]+)'
)
TOP_RE = re.compile(r'\b(global_rules\.md|config\.json|hooks\.v1\.json|mcp_config\.json)\b')

INTERNAL_PREFIXES = ('skills/', 'rules/', 'scripts/', 'hooks/', 'memory/', 'ledgers/')
TOP_FILES = ('global_rules.md', 'config.json', 'hooks.v1.json', 'mcp_config.json')


def err(msg):
    '''Write a diagnostic line to stderr.'''
    sys.stderr.write(msg + '\n')


def emit_json(data):
    '''Write deterministic JSON to stdout.'''
    text = json.dumps(data, sort_keys=True, indent=2, ensure_ascii=False)
    sys.stdout.buffer.write((text + '\n').encode('utf-8'))


def emit_text(text):
    '''Write plain text (LF) to stdout.'''
    sys.stdout.buffer.write((text + '\n').encode('utf-8'))


def locate_devin(project):
    '''Return (project_root, devin_dir) for a project or .devin path.'''
    p = Path(project).expanduser()
    if p.name == '.devin' and p.is_dir():
        return p.parent.resolve(), p.resolve()
    candidate = p / '.devin'
    if candidate.is_dir():
        return p.resolve(), candidate.resolve()
    raise FileNotFoundError(f'no .devin directory in {project}')


def relpath(base, abs_path):
    '''Relative path from base to abs_path, forward slashes, sorted basis.'''
    return os.path.relpath(abs_path, base).replace(os.sep, '/')


def project_label(project):
    '''Return a relative, deterministic label for a project path.'''
    try:
        rel = Path(os.path.relpath(project.resolve(), Path.cwd())).as_posix()
        if rel.startswith('..') or rel.startswith('..\\'):
            return project.name
        return rel
    except ValueError:
        return project.name


def _rel_and_provenance(abs_path, devin, project):
    '''Return (rel, provenance, category) for a file anywhere under project.'''
    try:
        rel = abs_path.relative_to(devin).as_posix()
        return rel, f'.devin/{rel}', category(rel, in_devin=True)
    except ValueError:
        pass
    try:
        rel = 'agents/' + abs_path.relative_to(project / 'agents').as_posix()
        return rel, rel, 'agents'
    except ValueError:
        pass
    if abs_path == project / 'mcp_config.json':
        return 'mcp_config.json', 'mcp_config.json', 'mcp'
    # fallback: relative to devin (will contain ..)
    rel = relpath(devin, abs_path)
    return rel, rel, category(rel, in_devin=False)


def category(rel, in_devin=True):
    if rel == 'global_rules.md' or rel.startswith('rules/') or rel == '.devin/global_rules.md':
        return 'rules'
    if rel.startswith('skills/') or rel.startswith('.devin/skills/'):
        return 'skills'
    if rel == 'hooks.v1.json' or rel == '.devin/hooks.v1.json':
        return 'hooks'
    if rel == 'config.json' or rel == '.devin/config.json':
        return 'config'
    if rel == 'mcp_config.json' or rel == '.devin/mcp_config.json':
        return 'mcp'
    if rel.startswith('agents/'):
        return 'agents'
    if rel.startswith('memory/') or rel.startswith('.devin/memory/'):
        return 'memory'
    if rel.startswith('ledgers/') or rel.startswith('.devin/ledgers/'):
        return 'ledgers'
    return 'other'


def hash_file(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read_text(path):
    try:
        text = path.read_text(encoding='utf-8', newline='')
        text = text.replace('\r\n', '\n').replace('\r', '\n')
        return True, text
    except UnicodeDecodeError:
        return False, ''


def parse_frontmatter(text):
    m = re.match(r'^---\s*\n(.*?)\n---\s*\n', text, re.DOTALL)
    if not m:
        return None, text
    fm = {}
    for line in m.group(1).split('\n'):
        if not line.strip():
            continue
        if ':' in line and not line[0].isspace():
            k, _, v = line.partition(':')
            fm[k.strip()] = v.strip()
    return fm, text[m.end():]


def headings(text):
    return re.findall(r'^#{1,6}\s+(.+)$', text, re.MULTILINE)


def iter_json_strings(obj):
    if isinstance(obj, dict):
        for v in obj.values():
            yield from iter_json_strings(v)
    elif isinstance(obj, list):
        for v in obj:
            yield from iter_json_strings(v)
    elif isinstance(obj, str):
        yield obj


def _clean_target(target):
    target = target.strip()
    target = target.split('#')[0].split('?')[0]
    target = target.rstrip('/')
    return target


def extract_refs(rel, content, is_json):
    by_pair = {}

    def add(kind, target):
        target = _clean_target(target)
        if not target:
            return
        if re.match(r'^[a-z][a-z0-9+.-]*:', target, re.IGNORECASE):
            return
        if target.startswith('#') or target.startswith('//'):
            return
        if '%APPDATA%' in target or '~/.config' in target or target.startswith('%') or target.startswith('~'):
            return
        if target.startswith('\\') or re.match(r'^[A-Za-z]:', target):
            return
        if target.startswith('/') and not target.startswith('.devin/'):
            return
        key = (rel, target)
        existing = by_pair.get(key)
        if existing is None or KIND_STRENGTH[kind] < KIND_STRENGTH[existing['kind']]:
            by_pair[key] = {'kind': kind, 'target': target, 'source': rel}

    if is_json:
        try:
            data = json.loads(content)
            strings = list(iter_json_strings(data))
        except Exception:
            strings = [content]
        for s in strings:
            if '%APPDATA%' in s or '~/.config' in s or '://' in s or s.startswith('%'):
                continue
            for m in re.finditer(r'\bscripts/([a-z0-9_-]+\.py)', s):
                add('command', 'scripts/' + m.group(1))
            for m in MENTION_RE.finditer(s):
                add('mention', m.group(1) + '/' + m.group(2).rstrip('/.,;)'))
            for m in TOP_RE.finditer(s):
                add('mention', m.group(1))
    else:
        for m in LINK_RE.finditer(content):
            add('markdown_link', m.group(1))
        for m in WIKI_RE.finditer(content):
            target = m.group(1).strip()
            if not target.endswith(('.md', '.json', '.py')):
                target += '.md'
            add('wikilink', target)
        for m in SOURCE_RE.finditer(content):
            add('source', m.group(1).rstrip('.,;'))
        for m in MENTION_RE.finditer(content):
            add('mention', m.group(1) + '/' + m.group(2).rstrip('/.,;)'))
        for m in TOP_RE.finditer(content):
            add('mention', m.group(1))
    return sorted(by_pair.values(), key=lambda x: (x['source'], x['target'], x['kind']))


def resolve_reference(target, source, devin, kind):
    if not target:
        return None
    target = target.strip()
    if re.match(r'^[a-z][a-z0-9+.-]*:', target, re.IGNORECASE):
        return None
    if target.startswith('#') or target.startswith('//'):
        return None
    if '%APPDATA%' in target or '~/.config' in target or target.startswith('%') or target.startswith('~'):
        return None
    if target.startswith('\\') or re.match(r'^[A-Za-z]:', target):
        return None
    if target.startswith('/') and not target.startswith('.devin/'):
        return None

    devin = devin.resolve()

    if target.startswith('.devin/') or target.startswith('.devin\\'):
        target = target.replace('\\', '/')
        if target.startswith('.devin/'):
            target = target[7:]
        bases = [devin]
    elif target.startswith(INTERNAL_PREFIXES) or target in TOP_FILES:
        bases = [devin]
    else:
        source_dir = (devin / source).parent
        bases = [source_dir, devin]

    if kind == 'source':
        bases.insert(0, devin)
    if kind == 'wikilink' and source.startswith('memory/'):
        bases.insert(0, devin / 'memory')

    for base in bases:
        candidate_unresolved = base / target
        if candidate_unresolved.is_symlink():
            continue
        try:
            candidate = candidate_unresolved.resolve()
            candidate.relative_to(devin)
            if candidate.is_file() or candidate.is_dir():
                return candidate
        except (ValueError, OSError):
            continue
    return None


def scan_artifact(devin, project, abs_path):
    if abs_path.is_symlink():
        return None
    rel, provenance, cat = _rel_and_provenance(abs_path, devin, project)
    is_text, content = read_text(abs_path)
    frontmatter = None
    hd = []
    refs = []
    json_keys = []
    json_error = None
    mcp_servers = []
    if is_text:
        if rel.endswith('.md'):
            frontmatter, body = parse_frontmatter(content)
            hd = headings(body)
            refs = extract_refs(rel, content, is_json=False)
        elif rel.endswith('.json'):
            try:
                data = json.loads(content)
                json_keys = sorted(data.keys())
                refs = extract_refs(rel, content, is_json=True)
                if rel == 'mcp_config.json' or provenance == '.devin/mcp_config.json':
                    mcp_servers = sorted(data.get('mcpServers', {}).keys())
            except json.JSONDecodeError as e:
                json_error = str(e)
                json_keys = []
                refs = []
    return {
        'category': cat,
        'frontmatter': frontmatter,
        'headings': hd,
        'json_keys': json_keys,
        'json_error': json_error,
        'mcp_servers': mcp_servers,
        'path': rel,
        'provenance': provenance,
        'references': refs,
        'sha256': hash_file(abs_path),
        'size': abs_path.stat().st_size,
    }


def scan_artifacts(devin, project):
    arts = []
    for abs_path in sorted(devin.rglob('*')):
        if '__pycache__' in abs_path.parts:
            continue
        if abs_path.is_file() and not abs_path.is_symlink():
            a = scan_artifact(devin, project, abs_path)
            if a is not None:
                arts.append(a)
    agents_dir = project / 'agents'
    if agents_dir.is_dir():
        for abs_path in sorted(agents_dir.rglob('*')):
            if '__pycache__' in abs_path.parts:
                continue
            if abs_path.is_file() and not abs_path.is_symlink():
                a = scan_artifact(devin, project, abs_path)
                if a is not None:
                    arts.append(a)
    mcp_path = project / 'mcp_config.json'
    if mcp_path.is_file() and not mcp_path.is_symlink():
        a = scan_artifact(devin, project, mcp_path)
        if a is not None:
            arts.append(a)
    arts.sort(key=lambda a: a['provenance'])
    return arts


def scan(devin, project, project_str):
    arts = scan_artifacts(devin, project)
    summary = {}
    for a in arts:
        summary[a['category']] = summary.get(a['category'], 0) + 1
    emit_json({
        'command': 'scan',
        'project': project_str,
        'summary': dict(sorted(summary.items())),
        'artifacts': arts,
    })


def explain(devin, project, project_str, artifact):
    target = devin / artifact
    if not target.is_file():
        raise FileNotFoundError(f'artifact not found: {artifact}')
    a = scan_artifact(devin, project, target)
    if a is None:
        raise FileNotFoundError(f'artifact is a symlink or outside .devin: {artifact}')
    emit_json({'command': 'explain', 'project': project_str, 'artifact': a})


def diff(left_devin, left_project, left_str, right_devin, right_project, right_str):
    left = {a['provenance']: a for a in scan_artifacts(left_devin, left_project)}
    right = {a['provenance']: a for a in scan_artifacts(right_devin, right_project)}
    added = sorted(set(right) - set(left))
    removed = sorted(set(left) - set(right))
    changed = [p for p in sorted(set(left) & set(right)) if left[p]['sha256'] != right[p]['sha256']]
    identical = [p for p in sorted(set(left) & set(right)) if left[p]['sha256'] == right[p]['sha256']]
    emit_json({
        'command': 'diff',
        'left': left_str,
        'right': right_str,
        'added': added,
        'removed': removed,
        'changed': changed,
        'identical': identical,
    })


def diagnose(devin, project):
    arts = scan_artifacts(devin, project)
    broken = []
    for a in arts:
        for ref in a['references']:
            resolved = resolve_reference(ref['target'], ref['source'], devin, ref['kind'])
            if resolved is None:
                broken.append(ref)
    broken = sorted(broken, key=lambda x: (x['source'], x['target'], x['kind']))

    by_hash = {}
    by_name = {}
    for a in arts:
        by_hash.setdefault(a['sha256'], []).append(a['path'])
        if a.get('frontmatter') and a['frontmatter'].get('name'):
            by_name.setdefault(a['frontmatter']['name'], []).append(a['path'])

    duplicates = []
    for sha, paths in by_hash.items():
        if len(paths) > 1:
            duplicates.append({'kind': 'content', 'sha256': sha, 'paths': sorted(paths)})
    for name, paths in by_name.items():
        if len(paths) > 1:
            duplicates.append({'kind': 'skill_name', 'name': name, 'paths': sorted(paths)})

    divergences = []

    # Malformed JSON files (provenance-bearing)
    for a in arts:
        if a.get('json_error'):
            divergences.append({'kind': 'malformed_json', 'source': a['provenance'], 'error': a['json_error']})

    # Config/hook events
    cfg_path = devin / 'config.json'
    hk_path = devin / 'hooks.v1.json'
    cfg = None
    hk = None
    if cfg_path.is_file():
        try:
            cfg = json.loads(cfg_path.read_text(encoding='utf-8-sig'))
        except json.JSONDecodeError:
            cfg = None
    if hk_path.is_file():
        try:
            hk = json.loads(hk_path.read_text(encoding='utf-8-sig'))
        except json.JSONDecodeError:
            hk = None
    if cfg is not None and hk is not None:
        cfg_events = set(cfg.get('hooks', {}).keys()) if isinstance(cfg.get('hooks'), dict) else set()
        hk_events = set(hk.keys()) if isinstance(hk, dict) else set()
        for events, src in [(cfg_events, 'config.json'), (hk_events, 'hooks.v1.json')]:
            missing = sorted(DEVIN_EVENTS - events)
            extra = sorted(events - DEVIN_EVENTS)
            if missing:
                divergences.append({'kind': 'missing_devin_events', 'source': src, 'missing': missing})
            if extra:
                divergences.append({'kind': 'extra_devin_events', 'source': src, 'extra': extra})
        only_cfg = sorted(cfg_events - hk_events)
        only_hk = sorted(hk_events - cfg_events)
        if only_cfg or only_hk:
            divergences.append({
                'kind': 'hooks_config_mismatch',
                'source': 'config.json vs hooks.v1.json',
                'only_in_config': only_cfg,
                'only_in_hooks_v1': only_hk,
            })

    # Manifest skill count
    manifest_path = devin / 'manifest.json'
    if manifest_path.is_file():
        try:
            m = json.loads(manifest_path.read_text(encoding='utf-8-sig'))
            declared = m.get('skill_count')
            actual = len([a for a in arts if a['category'] == 'skills' and a['path'].endswith('/SKILL.md')])
            if declared is not None and declared != actual:
                divergences.append({
                    'kind': 'manifest_skill_count',
                    'source': 'manifest.json',
                    'declared': declared,
                    'actual': actual,
                })
        except json.JSONDecodeError:
            # malformed manifest already reported via scan_artifact json_error
            pass

    return {
        'status': 'ok' if not (broken or duplicates or divergences) else 'issues',
        'broken_references': broken,
        'duplicates': duplicates,
        'divergences': divergences,
    }


def doctor(devin, project, project_str):
    data = diagnose(devin, project)
    data['command'] = 'doctor'
    data['project'] = project_str
    emit_json(data)


def render_plan(doctor_data, project_str):
    lines = [
        '# devin-manager plan',
        '',
        'Project: `' + project_str + '`',
        '',
        'Status: ' + doctor_data['status'],
        '',
        '## Findings',
        '',
    ]
    if not doctor_data['broken_references']:
        lines.append('- No broken references found.')
    else:
        lines.append('### Broken references')
        for ref in doctor_data['broken_references']:
            lines.append('- `' + ref['target'] + '` referenced from `' + ref['source'] + '` (kind: ' + ref['kind'] + ')')
    lines.append('')
    if not doctor_data['duplicates']:
        lines.append('- No duplicates found.')
    else:
        lines.append('### Duplicates')
        for dup in doctor_data['duplicates']:
            paths = ', '.join('`' + p + '`' for p in dup['paths'])
            if dup['kind'] == 'content':
                lines.append('- Content sha `' + dup['sha256'][:16] + '...` appears in ' + paths)
            else:
                lines.append('- Skill name `' + dup['name'] + '` appears in ' + paths)
    lines.append('')
    if not doctor_data['divergences']:
        lines.append('- No divergences found.')
    else:
        lines.append('### Divergences')
        for div in doctor_data['divergences']:
            if div['kind'] == 'malformed_json':
                lines.append('- `' + div['source'] + '` is malformed JSON: ' + str(div['error']))
            elif div['kind'] == 'missing_devin_events':
                events = ', '.join('`' + e + '`' for e in div['missing'])
                lines.append('- `' + div['source'] + '` is missing Devin CLI events: ' + events)
            elif div['kind'] == 'extra_devin_events':
                events = ', '.join('`' + e + '`' for e in div['extra'])
                lines.append('- `' + div['source'] + '` has extra events: ' + events)
            elif div['kind'] == 'hooks_config_mismatch':
                lines.append('- `' + div['source'] + '` mismatch: only in config=' + str(div['only_in_config']) + ', only in hooks.v1.json=' + str(div['only_in_hooks_v1']))
            elif div['kind'] == 'manifest_skill_count':
                lines.append('- `' + div['source'] + '` declares skill_count=' + str(div['declared']) + ' but disk has ' + str(div['actual']))
            else:
                lines.append('- ' + str(div))
    lines.extend([
        '',
        '## Proposed actions',
        '',
        '1. Review broken references and update source files or create missing targets under `.devin/`.',
        '2. Resolve duplicate skill names or content before writing to memory.',
        '3. Reconcile configuration divergences (malformed JSON, config.json vs hooks.v1.json, manifest counts).',
        '4. Re-run `devin-manager doctor` after fixes to verify convergence.',
        '',
        '## Source and license attribution',
        '',
        'This plan was produced by `devin-manager`.',
        'The `devin-manager` skill is conceptually inspired by DeepPaperNote\'s evidence-first workflow.',
        '- DeepPaperNote: https://github.com/917Dhj/DeepPaperNote',
        '- License: https://github.com/917Dhj/DeepPaperNote/blob/main/LICENSE (MIT)',
    ])
    return '\n'.join(lines)


def plan(devin, project, project_str, write, approve):
    if write and not approve:
        err('plan --write requires --approve to persist notes under .devin/')
        return 2
    data = diagnose(devin, project)
    note = render_plan(data, project_str)
    if write and approve:
        note_path = devin / NOTE_SUBDIR / 'plan.md'
        note_path.parent.mkdir(parents=True, exist_ok=True)
        note_path.write_text(note, encoding='utf-8', newline='\n')
        emit_json({
            'command': 'plan',
            'project': project_str,
            'status': 'ok',
            'written': str(note_path.relative_to(project).as_posix()),
        })
    else:
        emit_text(note)
    return 0


def main(argv=None):
    parser = argparse.ArgumentParser(description='Deterministic .devin audit and planning')
    sub = parser.add_subparsers(dest='command', required=True)

    p_scan = sub.add_parser('scan', help='deterministic inventory')
    p_scan.add_argument('project', nargs='?', default='.')

    p_explain = sub.add_parser('explain', help='explain one artifact')
    p_explain.add_argument('explain_args', nargs='+', help='[PROJECT] ARTIFACT')

    p_diff = sub.add_parser('diff', help='compare two .devin directories')
    p_diff.add_argument('left')
    p_diff.add_argument('right')

    p_doctor = sub.add_parser('doctor', help='diagnose references, duplicates, divergences')
    p_doctor.add_argument('project', nargs='?', default='.')

    p_plan = sub.add_parser('plan', help='generate plan note (read-only by default)')
    p_plan.add_argument('project', nargs='?', default='.')
    p_plan.add_argument('--write', '-w', action='store_true')
    p_plan.add_argument('--approve', '-a', action='store_true')

    args = parser.parse_args(argv)

    try:
        if args.command == 'scan':
            project, devin = locate_devin(args.project)
            scan(devin, project, project_label(project))
        elif args.command == 'explain':
            if len(args.explain_args) == 1:
                project_path, artifact = '.', args.explain_args[0]
            elif len(args.explain_args) == 2:
                project_path, artifact = args.explain_args[0], args.explain_args[1]
            else:
                err('explain requires one or two arguments: [PROJECT] ARTIFACT')
                return 2
            project, devin = locate_devin(project_path)
            explain(devin, project, project_label(project), artifact)
        elif args.command == 'diff':
            left_project, left_devin = locate_devin(args.left)
            right_project, right_devin = locate_devin(args.right)
            left_str = project_label(left_project)
            right_str = project_label(right_project)
            diff(left_devin, left_project, left_str, right_devin, right_project, right_str)
        elif args.command == 'doctor':
            project, devin = locate_devin(args.project)
            doctor(devin, project, project_label(project))
        elif args.command == 'plan':
            project, devin = locate_devin(args.project)
            return plan(devin, project, project_label(project), args.write, args.approve)
    except Exception as e:
        err(f'{args.command} failed: {e}')
        return 1
    return 0


if __name__ == '__main__':
    sys.exit(main())
