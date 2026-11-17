import os, re, json, hashlib, sys, py_compile, subprocess, glob
import ast as _ast
import ast as _ast37
from ._ctx import Ctx, text_hash_matches, _scan_py_files


def c37(ctx):
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
            ctx.warnings.append('subprocess text=True without encoding=: '
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


def c38(ctx):
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
            ctx.warnings.append('text file I/O without encoding=: '
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


def c39(ctx):
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
            ctx.warnings.append('text-mode sys.stdin without utf-8 pin: '
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


def c40(ctx):
    try:
        import time as _time40
        _stale_days = 180
        _now40 = _time40.time()
        _stale = []
        _missing = []
        for _sk in sorted(os.listdir(ctx.skills_dir)):
            _sp = os.path.join(ctx.skills_dir, _sk)
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
            ctx.warnings.append('skill dir lacks SKILL.md: ' + _sk)
            print('  WARN ' + _sk + ': no SKILL.md')
        if _stale:
            ctx.warnings.append('stale SKILL.md (>' + str(_stale_days) + 'd): '
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


def c41(ctx):
    try:
        _ident = json.load(open('data/bundle-identity.json', encoding='utf-8-sig'))
        _v = _ident.get('validated_cli_version')
        _doc = '.devin/docs/DEVIN-CLI-COMPATIBILITY.md'
        if not _v:
            ctx.warnings.append('bundle-identity.json lacks validated_cli_version')
            print('  WARN no validated_cli_version declared')
        elif not os.path.isfile(_doc):
            ctx.errors.append(_doc + ' missing')
            print('  FAIL ' + _doc + ' missing')
        elif _v not in open(_doc, encoding='utf-8').read():
            ctx.warnings.append(_doc + ' does not name validated_cli_version ' + _v)
            print('  WARN ' + _doc + ' missing version ' + _v)
        else:
            print('  OK  compat doc names validated_cli_version ' + _v)
    except Exception as _e41:
        print('  SKIP compat-doc check failed: ' + str(_e41))

    # 42. stdout utf-8 pin: files that print ensure_ascii=False JSON must
    # pin sys.stdout - on Windows the console is cp1252 and `>` redirects
    # write mojibake (issue #573: PT transcripts lost accents).
    print()


def c42(ctx):
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
            ctx.errors.append('JSON emitters without sys.stdout utf-8 pin: '
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


def c43(ctx):
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
            ctx.errors.append('stdlib names used without import: '
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


def c44(ctx):
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
            ctx.errors.append('stdlib API newer than the 3.11 floor: '
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


def c45(ctx):
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
            ctx.warnings.append('--out declared without overwrite-refusal: '
                            + ', '.join(_bad45[:10]))
            print('  WARN ' + str(len(_bad45)) + ' file(s): '
                  + ', '.join(_bad45[:5]))
        else:
            print('  OK  all --out emitters refuse to overwrite')
    except Exception as _e45:
        print('  SKIP out-refusal check failed: ' + str(_e45))



