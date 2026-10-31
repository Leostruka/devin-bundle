"""ui_dsl — strict line-based UI DSL (v1) for streamed HUDs and forms.

Local capability: parses a versioned one-element-per-line grammar into an
AST, emits it back canonically (roundtrip), feeds it incrementally for
streaming, and renders it to a self-contained HTML fragment with native
form controls. No network, no JS, no external app claims — the craft
bridge continues to dispatch only real app CLI commands.

Grammar:

    # comment
    hud title="Quest Tracker" anchor=top-right
    row label="Kills" value=12 of=20
    bar value=0.6 color=green
    end
    form id=grill-3 title="Confirm scope"
    q choice id=q1 text="Delete cache?" options=yes|no|skip
    q multi id=q2 text="Targets" options=docs|code|tests
    btn action=submit label="Go"
    end

Rules:
  * one element per line; `end` closes the nearest open block (no nesting)
  * attrs are `key=value`; values bare tokens or double-quoted with
    \\\\ and \\" escapes only
  * `kind` is a reserved qualifier for q, not a settable attribute
  * `id` values must match [A-Za-z][A-Za-z0-9_-]* and be unique
    document-wide; options may not repeat within a question
  * blocks must contain at least one child; children restricted per parent
  * unknown types/attrs, duplicates, malformed quoting -> ParseError

CLI:
    python ui_dsl.py parse --input in.dsl [--output out.dsl] [--force]
    python ui_dsl.py render --input in.dsl --output out.html [--force]
    python ui_dsl.py benchmark --fixture in.dsl [--tokenizer PATH_OR_ID]
        [--output res.json]
"""
from __future__ import annotations

import argparse
import codecs
import copy
import hashlib
import html
import json
import os
import re
import sys
import tempfile

DSL_VERSION = 1

MAX_LINES = 2000
MAX_BYTES = 128 * 1024
MAX_LINE_LEN = 1024
MAX_ELEMENTS = 500
MAX_VALUE_LEN = 512
MAX_OPTIONS = 64

TOKENIZER_ID = "Xenova/gpt-4"
TOKENIZER_FALLBACK = "Xenova/cl100k_base"

BARE_VALUE = re.compile(r"[A-Za-z0-9_.,:|#%@+=/~^-]+")
IDENT = re.compile(r"[A-Za-z][A-Za-z0-9_-]*")
ACTION_TOKEN = re.compile(r"[a-z][a-z0-9_-]*")

ATTRS = {
    "hud": {"title", "anchor"},
    "row": {"label", "value", "of"},
    "bar": {"value", "color"},
    "form": {"id", "title"},
    "q": {"id", "text", "options"},
    "btn": {"action", "label"},
}
REQUIRED = {
    "row": {"label", "value"},
    "bar": {"value"},
    "form": {"id"},
    "q": {"id", "text", "options"},
    "btn": {"action"},
}
BLOCKS = {"hud", "form"}
LEAVES = {"row", "bar", "q", "btn"}
CHILDREN = {
    "hud": {"row", "bar"},
    "form": {"q", "btn"},
}
Q_KINDS = {"choice", "multi"}
BAR_COLORS = re.compile(r"([a-z]+|#[0-9a-fA-F]{3,8})")


class ParseError(ValueError):
    """Strict grammar, encoding, or bounds violation."""


class Element:
    __slots__ = ("type", "attrs", "children")

    def __init__(self, type_, attrs=None):
        self.type = type_
        self.attrs = attrs or {}
        self.children = []


class Document:
    __slots__ = ("blocks",)

    def __init__(self):
        self.blocks = []


def _err(msg, line_no=None):
    if line_no is not None:
        raise ParseError(f"line {line_no}: {msg}")
    raise ParseError(msg)


def _unescape(raw, line_no):
    out = []
    i = 0
    while i < len(raw):
        c = raw[i]
        if c == "\\":
            i += 1
            if i >= len(raw) or raw[i] not in "\\\"":
                _err("invalid escape in quoted value", line_no)
            out.append(raw[i])
        else:
            out.append(c)
        i += 1
    return "".join(out)


def _parse_attrs(text, line_no):
    """Parse `key=value` pairs; returns dict. Strict: single-space
    separators, bare token or double-quoted value, no duplicates."""
    attrs = {}
    i, n = 0, len(text)
    while i < n:
        m = IDENT.match(text, i)
        if not m:
            _err(f"expected attribute name at {text[i:]!r}", line_no)
        key = m.group(0)
        i = m.end()
        if i >= n or text[i] != "=":
            _err(f"expected '=' after attribute {key!r}", line_no)
        i += 1
        if i < n and text[i] == '"':
            j = i + 1
            while True:
                if j >= n:
                    _err("unterminated quoted value", line_no)
                if text[j] == "\\":
                    j += 2
                    continue
                if text[j] == '"':
                    break
                j += 1
            value = _unescape(text[i + 1:j], line_no)
            i = j + 1
        else:
            m = BARE_VALUE.match(text, i)
            if not m:
                _err(f"invalid bare value for {key!r}", line_no)
            value = m.group(0)
            i = m.end()
        if key in attrs:
            _err(f"duplicate attribute {key!r}", line_no)
        if len(value) > MAX_VALUE_LEN:
            _err(f"value for {key!r} exceeds {MAX_VALUE_LEN} chars", line_no)
        attrs[key] = value
        if i < n:
            if text[i] != " ":
                _err("expected single space between attributes", line_no)
            i += 1
            if i < n and text[i] == " ":
                _err("expected single space between attributes", line_no)
    return attrs


def _check_attrs(type_, attrs, line_no):
    allowed = ATTRS[type_]
    for k in attrs:
        if k not in allowed:
            _err(f"unknown attribute {k!r} for {type_!r}", line_no)
    missing = REQUIRED.get(type_, set()) - attrs.keys()
    if missing:
        _err(f"{type_!r} missing required: {sorted(missing)}", line_no)


def _parse_element(head, rest, line_no):
    """Leaf/opening line -> Element. `q` takes a leading kind qualifier;
    `kind` is reserved and rejected as a normal attribute."""
    if head == "q":
        parts = rest.split(" ", 1)
        if len(parts) < 1 or parts[0] not in Q_KINDS:
            _err("q requires kind 'choice' or 'multi'", line_no)
        attrs = _parse_attrs(parts[1], line_no) if len(parts) > 1 else {}
        _check_attrs(head, attrs, line_no)
        attrs = {"kind": parts[0], **attrs}
    else:
        attrs = _parse_attrs(rest, line_no)
        _check_attrs(head, attrs, line_no)
    return Element(head, attrs)


def _validate_element(el, line_no):
    a = el.attrs
    if "id" in a and not IDENT.fullmatch(a["id"]):
        _err(f"invalid id {a['id']!r}", line_no)
    if el.type == "row" and "of" in a:
        for k in ("value", "of"):
            if not re.fullmatch(r"-?\d+(\.\d+)?", a[k]):
                _err(f"row {k!r} must be numeric", line_no)
    if el.type == "bar":
        try:
            v = float(a["value"])
        except ValueError:
            _err("bar value must be numeric", line_no)
        if not 0.0 <= v <= 1.0:
            _err("bar value must be within [0,1]", line_no)
        if "color" in a and not BAR_COLORS.fullmatch(a["color"]):
            _err(f"invalid bar color {a['color']!r}", line_no)
    if el.type == "q":
        opts = a["options"].split("|")
        if not all(opts) or len(opts) > MAX_OPTIONS:
            _err("q options must be non-empty | separated tokens", line_no)
        if len(set(opts)) != len(opts):
            _err("q options must not repeat", line_no)
        a["options"] = opts
    if el.type == "btn" and not ACTION_TOKEN.fullmatch(a["action"]):
        _err("btn action must be a lowercase token", line_no)


class _Machine:
    """Feeds complete lines into an open/close state machine and tracks
    document-wide id uniqueness."""

    def __init__(self):
        self.doc = Document()
        self.open = None
        self.line_no = 0
        self.elements = 0
        self.ids = set()

    def _adopt(self, el, line_no):
        _validate_element(el, line_no)
        emitted = []
        eid = el.attrs.get("id")
        if eid is not None:
            emitted.append(eid)
            if el.type == "form" and "title" in el.attrs:
                emitted.append(f"{eid}-title")
            if el.type == "q":
                emitted.extend(f"{eid}-opt{i}"
                               for i in range(len(el.attrs["options"])))
        for e in emitted:
            if e in self.ids:
                _err(f"duplicate id {e!r}", line_no)
        self.ids.update(emitted)

    def line(self, raw):
        self.line_no += 1
        if len(raw) > MAX_LINE_LEN:
            _err(f"line exceeds {MAX_LINE_LEN} chars", self.line_no)
        text = raw.rstrip("\r")
        if not text.strip() or text.lstrip().startswith("#"):
            return
        head, _, rest = text.partition(" ")
        if head == "end":
            if rest.strip():
                _err("'end' takes no attributes", self.line_no)
            if self.open is None:
                _err("'end' with no open block", self.line_no)
            if not self.open.children:
                _err(f"{self.open.type!r} block must contain a child",
                     self.line_no)
            self.doc.blocks.append(self.open)
            self.open = None
            return
        if head in BLOCKS:
            if self.open is not None:
                _err(f"cannot nest {head!r} inside {self.open.type!r}",
                     self.line_no)
            el = _parse_element(head, rest, self.line_no)
            self._adopt(el, self.line_no)
            self.open = el
        elif head in LEAVES:
            if self.open is None:
                _err(f"{head!r} outside any block", self.line_no)
            if head not in CHILDREN[self.open.type]:
                _err(f"{head!r} not allowed inside {self.open.type!r}",
                     self.line_no)
            el = _parse_element(head, rest, self.line_no)
            self._adopt(el, self.line_no)
            self.open.children.append(el)
        else:
            _err(f"unknown element type {head!r}", self.line_no)
        self.elements += 1
        if self.elements > MAX_ELEMENTS:
            _err(f"element count exceeds {MAX_ELEMENTS}", self.line_no)

    def finish(self):
        if self.open is not None:
            _err(f"unclosed {self.open.type!r} block at EOF", self.line_no)
        return self.doc


def parse(text):
    """Strict whole-string parse -> Document. Raises ParseError."""
    if isinstance(text, bytes):
        try:
            text = text.decode("utf-8")
        except UnicodeDecodeError as e:
            _err(f"invalid UTF-8: {e}")
    try:
        nbytes = len(text.encode("utf-8"))
    except UnicodeEncodeError as e:
        _err(f"invalid str input: {e}")
    if nbytes > MAX_BYTES:
        _err(f"input exceeds {MAX_BYTES} bytes")
    m = _Machine()
    lines = text.split("\n")
    if lines and lines[-1] == "":
        lines.pop()
    if len(lines) > MAX_LINES:
        _err(f"input exceeds {MAX_LINES} lines")
    for raw in lines:
        m.line(raw)
    return m.finish()


class StreamParser:
    """Incremental feeder: incrementally decodes UTF-8, buffers partial
    lines, validates each completed line immediately. snapshot() is
    deterministic — a partial last line is never treated as complete."""

    def __init__(self):
        self._m = _Machine()
        self._dec = codecs.getincrementaldecoder("utf-8")()
        self._buf = ""
        self._bytes = 0
        self._done = False

    def feed(self, data):
        """data: str or bytes. Byte chunks may split multibyte characters."""
        if self._done:
            raise ParseError("feed() after finish()")
        if isinstance(data, (bytes, bytearray)):
            self._bytes += len(data)
            try:
                data = self._dec.decode(bytes(data), final=False)
            except UnicodeDecodeError as e:
                _err(f"invalid UTF-8: {e}", self._m.line_no + 1)
        else:
            try:
                self._bytes += len(data.encode("utf-8"))
            except UnicodeEncodeError as e:
                self._done = True
                _err(f"invalid str input: {e}", self._m.line_no + 1)
        if self._bytes > MAX_BYTES:
            _err(f"stream exceeds {MAX_BYTES} bytes", self._m.line_no + 1)
        self._buf += data
        while "\n" in self._buf:
            raw, self._buf = self._buf.split("\n", 1)
            if self._m.line_no + 1 > MAX_LINES:
                _err(f"stream exceeds {MAX_LINES} lines", self._m.line_no + 1)
            self._m.line(raw)
        if len(self._buf) > MAX_LINE_LEN:
            _err(f"partial line exceeds {MAX_LINE_LEN} chars",
                 self._m.line_no + 1)

    def finish(self):
        """Signal end of input. Raises on truncated UTF-8, a dangling
        partial line, or an unclosed block."""
        try:
            tail = self._dec.decode(b"", final=True)
        except UnicodeDecodeError as e:
            _err(f"truncated UTF-8 at EOF: {e}", self._m.line_no + 1)
        self._buf += tail
        if self._buf.strip():
            _err("unterminated final line", self._m.line_no + 1)
        self._buf = ""
        self._done = True
        return self._m.finish()

    def snapshot(self):
        """Current document including an open block's parsed children;
        never includes a partial un-parsed line."""
        if self._m.open is None:
            return copy.deepcopy(self._m.doc)
        doc = Document()
        doc.blocks = list(self._m.doc.blocks) + [self._m.open]
        return copy.deepcopy(doc)


def _emit_value(v):
    if isinstance(v, list):
        v = "|".join(v)
    if BARE_VALUE.fullmatch(v):
        return v
    esc = v.replace("\\", "\\\\").replace('"', '\\"')
    return f'"{esc}"'


def emit(doc):
    """Canonical serialization; emit(parse(src)) == src for canonical src."""
    out = []
    for block in doc.blocks:
        head = block.type + (" " if block.attrs else "") + \
            " ".join(f"{k}={_emit_value(v)}" for k, v in block.attrs.items())
        out.append(head)
        for c in block.children:
            if c.type == "q":
                kind = c.attrs["kind"]
                rest = " ".join(
                    f"{k}={_emit_value(v)}"
                    for k, v in c.attrs.items() if k != "kind")
                out.append(f"q {kind} {rest}".rstrip())
            else:
                line = c.type + " " + " ".join(
                    f"{k}={_emit_value(v)}" for k, v in c.attrs.items())
                out.append(line.rstrip())
        out.append("end")
    return "\n".join(out) + "\n"


def to_jsonable(doc):
    """Semantic-equivalent JSON payload (used for tokenizer comparison)."""
    def el(e):
        return {"type": e.type, "attrs": dict(e.attrs)}
    return {"version": DSL_VERSION,
            "blocks": [{**el(b),
                        "children": [el(c) for c in b.children]}
                       for b in doc.blocks]}


def _e(s):
    return html.escape(str(s), quote=True)


def _render_el(el, out, autofocus=False):
    a = el.attrs
    if el.type == "row":
        extra = (f'<span class="ui-of">/{_e(a["of"])}</span>'
                 if "of" in a else "")
        out.append(
            f'<div class="ui-row"><span class="ui-label">{_e(a["label"])}'
            f'</span><span class="ui-value">{_e(a["value"])}{extra}</span>'
            f"</div>")
    elif el.type == "bar":
        pct = int(round(float(a["value"]) * 100))
        color = _e(a.get("color", ""))
        cls = f" ui-bar-{color}" if color else ""
        out.append(
            f'<div class="ui-bar{cls}" role="progressbar" '
            f'aria-valuemin="0" aria-valuemax="100" aria-valuenow="{pct}"'
            f' aria-label="progress">'
            f'<progress class="ui-bar-fill" value="{_e(a["value"])}" '
            f'max="1">{pct}%</progress></div>')
    elif el.type == "q":
        kind = "radio" if a["kind"] == "choice" else "checkbox"
        out.append(
            f'<fieldset class="ui-q" id="{_e(a["id"])}">'
            f"<legend>{_e(a['text'])}</legend>")
        for i, opt in enumerate(a["options"]):
            oid = f'{a["id"]}-opt{i}'
            focus = " autofocus" if autofocus and i == 0 else ""
            out.append(
                f'<label for="{_e(oid)}">'
                f'<input type="{kind}" name="{_e(a["id"])}" '
                f'id="{_e(oid)}" value="{_e(opt)}"{focus}>{_e(opt)}</label>')
        out.append("</fieldset>")
    elif el.type == "btn":
        btype = "submit" if a["action"] == "submit" else "button"
        out.append(
            f'<button type="{btype}" data-action="{_e(a["action"])}" '
            f'class="ui-btn">{_e(a.get("label", a["action"]))}</button>')


def render_html(doc):
    """Render a Document to a self-contained HTML fragment. All dynamic
    text is HTML-escaped; emits no scripts, inline handlers, URLs, or
    remote references. Each form is wrapped in a non-modal `<dialog open>`
    (kept in flow via `position:static` so multiple forms never overlap)
    with `method="dialog"` — native submit closes the dialog in-page with
    no navigation, no endpoint, and no JS."""
    out = ['<div class="ui-dsl" data-dsl-version="%d">' % DSL_VERSION,
           "<style>.ui-dsl dialog{position:static}</style>"]
    for block in doc.blocks:
        a = block.attrs
        if block.type == "hud":
            label = _e(a.get("title", "hud"))
            anchor = _e(a.get("anchor", ""))
            out.append(
                f'<section class="ui-hud" aria-label="{label}"'
                + (f' data-anchor="{anchor}"' if anchor else "") + ">")
            if "title" in a:
                out.append(f'<h2 class="ui-title">{_e(a["title"])}</h2>')
        elif block.type == "form":
            fid = _e(a["id"])
            title_id = f"{fid}-title"
            named = f'aria-labelledby="{title_id}"' if "title" in a \
                else f'aria-label="{_e(a["id"])}"'
            out.append(
                f'<dialog class="ui-form-dialog" open {named}>'
                f'<form class="ui-form" id="{fid}" method="dialog" {named}>')
            if "title" in a:
                out.append(
                    f'<h2 class="ui-title" id="{title_id}">'
                    f'{_e(a["title"])}</h2>')
        for i, c in enumerate(block.children):
            first_q = (block.type == "form" and c.type == "q"
                       and not any(p.type == "q"
                                   for p in block.children[:i]))
            _render_el(c, out, autofocus=first_q)
        out.append("</section>" if block.type == "hud"
                   else "</form></dialog>")
    out.append("</div>")
    return "\n".join(out) + "\n"


def load_tokenizer(spec=None):
    """Pinned real BPE tokenizer. `spec` may be a local tokenizer.json
    artifact path (recorded with sha256 for reproducibility) or a hub id.
    Never falls back to a byte heuristic."""
    from tokenizers import Tokenizer
    if spec and os.path.exists(spec):
        return Tokenizer.from_file(spec), {"tokenizer": spec}
    if spec:
        return Tokenizer.from_pretrained(spec), {"tokenizer": spec}
    try:
        return Tokenizer.from_pretrained(TOKENIZER_ID), \
            {"tokenizer": TOKENIZER_ID}
    except Exception:
        return Tokenizer.from_pretrained(TOKENIZER_FALLBACK), \
            {"tokenizer": TOKENIZER_FALLBACK}


def benchmark(dsl_src, tokenizer=None, fixture_name=None):
    """Token-count the DSL source vs its minified semantic-equivalent JSON
    payload with a real tokenizer. Results carry the canonical-input and
    serialized-tokenizer digests so they are reproducible; they are
    fixture- and tokenizer-specific — not a universal savings claim."""
    tok, meta = load_tokenizer(tokenizer)
    doc = parse(dsl_src)
    canon = emit(doc)
    json_src = json.dumps(to_jsonable(doc), ensure_ascii=False,
                          separators=(",", ":"))
    dsl_toks = len(tok.encode(canon).ids)
    json_toks = len(tok.encode(json_src).ids)
    return {**meta,
            "tokenizer_sha256": hashlib.sha256(
                tok.to_str().encode("utf-8")).hexdigest(),
            "json_form": "minified",
            "fixture": fixture_name,
            "input_sha256": hashlib.sha256(
                canon.encode("utf-8")).hexdigest(),
            "fixture_bytes_dsl": len(canon.encode("utf-8")),
            "fixture_bytes_json": len(json_src.encode("utf-8")),
            "dsl_tokens": dsl_toks,
            "json_tokens": json_toks,
            "ratio": round(dsl_toks / json_toks, 4) if json_toks else None}


def _read_input(path):
    """Read at most MAX_BYTES+1 bytes, then fail — no unbounded read."""
    def bounded(f):
        data = f.read(MAX_BYTES + 1)
        if len(data) > MAX_BYTES:
            _err(f"input exceeds {MAX_BYTES} bytes")
        return data
    if path in (None, "-"):
        return bounded(sys.stdin)
    with open(path, "r", encoding="utf-8") as f:
        return bounded(f)


def _write_output(path, text, force):
    """stdout when no path. Without --force: atomic exclusive create —
    never clobbers an existing file. With --force: atomic replace via
    temp file + os.replace."""
    if path in (None, "-"):
        sys.stdout.write(text)
        return
    data = text.encode("utf-8")
    if not force:
        try:
            fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL)
        except FileExistsError:
            raise ParseError(f"output exists (use --force): {path}")
        with os.fdopen(fd, "wb") as f:
            f.write(data)
        return
    d = os.path.dirname(os.path.abspath(path))
    fd, tmp = tempfile.mkstemp(dir=d, suffix=".tmp")
    try:
        with os.fdopen(fd, "wb") as f:
            f.write(data)
        os.replace(tmp, path)
    except BaseException:
        try:
            os.unlink(tmp)
        except OSError:
            pass
        raise


def main(argv=None):
    ap = argparse.ArgumentParser(description="ui_dsl — line UI DSL v%d" %
                                 DSL_VERSION)
    sub = ap.add_subparsers(dest="cmd", required=True)
    for name in ("parse", "render"):
        p = sub.add_parser(name)
        p.add_argument("--input", default="-")
        p.add_argument("--output", default="-")
        p.add_argument("--force", action="store_true")
    pb = sub.add_parser("benchmark")
    pb.add_argument("--fixture", required=True)
    pb.add_argument("--tokenizer", default=None)
    pb.add_argument("--output", default="-")
    pb.add_argument("--force", action="store_true")
    args = ap.parse_args(argv)
    try:
        if args.cmd == "parse":
            _write_output(args.output, emit(parse(_read_input(args.input))),
                          args.force)
        elif args.cmd == "render":
            _write_output(args.output,
                          render_html(parse(_read_input(args.input))),
                          args.force)
        elif args.cmd == "benchmark":
            res = benchmark(_read_input(args.fixture), args.tokenizer,
                            fixture_name=args.fixture)
            _write_output(args.output,
                          json.dumps(res, indent=2) + "\n", args.force)
    except ParseError as e:
        print(f"ui_dsl: {e}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
