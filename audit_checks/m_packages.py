import os, re, json
from ._ctx import Ctx

# c46: slop-squatting guard. Skills, agent profiles, and scripts instruct
# agents to run installers; an unpinned or unvetted package name is the
# vector hallucinated-dependency attacks use (agent skills telling agents
# to `npx <package-that-does-not-exist>`). Offline we cannot verify
# registry existence, so the contract is: unpinned refs must appear in
# data/allowed-packages.json; anything else is a warning for human review.

_SCAN = [
    ('skills', re.compile(r'SKILL\.md$')),
    ('agents', re.compile(r'\.md$')),
    ('scripts', re.compile(r'\.py$')),
]

_PKG = r'([a-z0-9@][^\s`"\'|<>()]*)'
_NPX_RE = re.compile(r'npx\s+(?:-{1,2}[a-zA-Z][\w-]*\s+)*' + _PKG)
_NPM_RE = re.compile(r'npm\s+(?:i|install|add)\s+([^\n`"|]+)')
_PIP_RE = re.compile(r'(?:python3?\s+-m\s+)?pip3?\s+install\s+([^\n`"|]+)')
_UV_RE = re.compile(r'uv(?:x|\s+tool\s+(?:run|install))\s+' + _PKG)
_PIPX_RE = re.compile(r'pipx\s+(?:run|install)\s+' + _PKG)
_CARGO_RE = re.compile(r'cargo\s+install\s+' + _PKG)
_FLAG_RE = re.compile(r'^-')
_FLAG_TAKES_VALUE = {'-r', '--requirement', '-c', '--constraint',
                     '-e', '--editable', '-t', '--target', '-g', '--global',
                     '--git', '--branch', '--tag', '--rev',
                     '--index-url', '--extra-index-url', '--find-links',
                     '-i', '--registry', '--python', '--features',
                     '--bin', '--root', '--path',
                     '--package'}
# matched against the tag after the last '@' (rpartition strips the '@')
_FLOATING_RE = re.compile(r'^(latest|next|beta|canary|dev|nightly)$')
_REQFILE_RE = re.compile(r'\.(txt|in)$')
_CUT_CHARS = ';|&<>'


def _npm_pkgs(seg):
    """All package tokens in one install/exec segment. Every non-flag,
    non-requirements token is a package - collecting only the first let an
    unpinned name hide behind a pinned sibling."""
    pkgs = []
    skip_next = False
    for tok in seg.split():
        tok = tok.lstrip(_CUT_CHARS)
        if not tok:
            break  # ; | && < > all end the command segment
        if any(c in tok for c in _CUT_CHARS):
            tok = tok[:min(tok.index(c) for c in _CUT_CHARS if c in tok)]
            end_of_cmd = True
        else:
            end_of_cmd = False
        if not tok:
            break
        if skip_next:
            skip_next = False
            if end_of_cmd:
                break
            continue
        if _FLAG_RE.match(tok):
            if tok in _FLAG_TAKES_VALUE:
                skip_next = True
            if end_of_cmd:
                break
            continue
        if _REQFILE_RE.search(tok):
            if end_of_cmd:
                break
            continue
        if not re.match(r'^[a-z0-9@]', tok):
            break  # prose, not a package token
        pkgs.append(tok)
        if end_of_cmd:
            break
    return pkgs


def _pin_state(eco, ref):
    """Return (name, pinned, floating)."""
    name = ref.strip().rstrip('.,;:)')
    if eco in ('pip', 'uv', 'pipx', 'cargo'):
        for sep in ('==', '~=', '>=', '<=', '>', '!='):
            if sep in name:
                return name.split(sep)[0].strip(), True, False
        if '[' in name and ']' in name and '@' in name:
            return name, True, False
        return name, False, False
    # npm-style: name@version; @scope/name[@version]
    core = name.lstrip('@')
    if '@' in core:
        base, _, tag = name.rpartition('@')
        if _FLOATING_RE.match(tag):
            return base, False, True
        return base, True, False
    return name, False, False


def _refs_in(text):
    for m in _NPX_RE.finditer(text):
        yield 'npx', m.group(1)
    for m in _NPM_RE.finditer(text):
        for tok in _npm_pkgs(m.group(1)):
            yield 'npm', tok
    for m in _PIP_RE.finditer(text):
        for tok in _npm_pkgs(m.group(1)):
            yield 'pip', tok
    for m in _UV_RE.finditer(text):
        yield 'uv', m.group(1)
    for m in _PIPX_RE.finditer(text):
        yield 'pipx', m.group(1)
    for m in _CARGO_RE.finditer(text):
        yield 'cargo', m.group(1)


def _files():
    for root, pat in _SCAN:
        if not os.path.isdir(root):
            continue
        for dirpath, dirnames, filenames in os.walk(root):
            dirnames[:] = sorted(d for d in dirnames
                                 if d not in ('__pycache__', '.venv',
                                              'node_modules'))
            for fn in sorted(filenames):
                if pat.search(fn):
                    yield os.path.join(dirpath, fn)


def c46(ctx):
    allow_path = os.path.join('data', 'allowed-packages.json')
    allowed = {}
    if os.path.isfile(allow_path):
        try:
            data = json.load(open(allow_path, encoding='utf-8-sig'))
            pk = data.get('packages') if isinstance(data, dict) else None
            if isinstance(pk, dict):
                for eco, names in pk.items():
                    if isinstance(names, (list, set)):
                        allowed[eco] = set(names)
        except (ValueError, OSError):
            ctx.warnings.append('data/allowed-packages.json unreadable')
    flagged = []
    for path in _files():
        try:
            text = open(path, encoding='utf-8', errors='replace').read()
        except OSError:
            continue
        for eco, ref in _refs_in(text):
            name, pinned, floating = _pin_state(eco, ref)
            if not name or name.startswith('<'):
                continue
            if name in allowed.get(eco, set()):
                continue
            if pinned and not floating:
                continue
            kind = 'floating tag' if floating else 'unpinned + unvetted'
            flagged.append(f'{path}: {eco} {name} ({kind})')
    for f in sorted(set(flagged)):
        ctx.warnings.append('package-ref ' + f)
        print('  WARN ' + f)
    if not flagged:
        print('  OK  all package install/exec refs are pinned or allowlisted')
    print()
