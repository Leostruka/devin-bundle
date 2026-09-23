#!/usr/bin/env python3
"""Host-side import shim for guest/worker.py — the worker file lives in
guest/ (it ships inside the image), this module exists so tests and the
supervisor can load its pure functions via the standard extension path.
"""
import importlib.util
import sys
from pathlib import Path

_w = Path(__file__).resolve().parent / "guest" / "worker.py"
_spec = importlib.util.spec_from_file_location("guest_worker", _w)
_mod = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_mod)

PROTOCOL_VERSION = _mod.PROTOCOL_VERSION
METHODS = _mod.METHODS
build_handshake = _mod.build_handshake
handle_request = _mod.handle_request
serve = _mod.serve
