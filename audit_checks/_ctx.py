import os, re, json, hashlib, sys, py_compile, subprocess, glob


def text_hash_matches(path, expected):
    with open(path, 'rb') as source:
        raw = source.read()
    lf = raw.replace(b'\r\n', b'\n')
    variants = (raw, lf, lf.replace(b'\n', b'\r\n'))
    return expected.upper() in {hashlib.sha256(data).hexdigest().upper() for data in variants}


class Ctx:
    """Shared audit state: result lists + cross-check carriers."""
    def __init__(self):
        self.errors = []
        self.warnings = []


def _scan_py_files():
    for _root in ('extensions', 'scripts', 'skills'):
        for _dirpath, _dirnames, _filenames in os.walk(_root):
            _dirnames[:] = [d for d in _dirnames
                            if d not in ('.venv', '__pycache__', 'tests')]
            for _fn in _filenames:
                if _fn.endswith('.py'):
                    yield os.path.join(_dirpath, _fn)
