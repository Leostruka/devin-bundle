#!/usr/bin/env python3
"""checks_p4.py - P4 additions to the design_lint static rule set.

Two groups (see rules_registry.py for citations/severities):

  * unslop-ui copy tells (source: felipebasurto/unslop-ui, MIT) - the
    statically checkable subset of U1-U16/U21-U24: eyebrow labels,
    decorative numbering, repeated subtitles, self-explaining captions,
    dead status chips.
  * CSS craft checks - dynamic viewport units, palette size, gradient
    interpolation hints, concentric border-radius, carousel edge fades.

Each check takes (html_text, css_text, relpath) and yields finding dicts
{rule, file, line, evidence}, same contract as checks.py. Merged into
checks.CHECKS at import time; keep this module self-contained (no import
of checks.py - it is the other way around).
"""
import re
from html import unescape as _unescape_html


def _finding(rule, path, line, evidence):
    return {"rule": rule, "file": path, "line": line,
            "evidence": evidence[:120]}


def _num(px):
    try:
        return float(px)
    except (TypeError, ValueError):
        return 0.0


# ---------- P4: unslop-ui copy tells (source: felipebasurto/unslop-ui, MIT)
# Static subset of U1-U16/U21-U24. Heuristics only flag review candidates;
# the real-state test (bound data vs fixed literal) cannot be proven
# statically, so severity stays info/warn per registry.

_LABEL_TAGS = (r"span|div|p|small|label|em|strong|a|li|td|th|figcaption|"
               r"legend")
_LABEL_THEN_HEADING = re.compile(
    r"<(" + _LABEL_TAGS + r")((?:\s[^<>]*)?)>\s*([^<]{1,80}?)\s*</\1\s*>"
    r"\s*<h([1-6])[\s>]", re.S)
_EYEBROW_HINT_CLASS = re.compile(
    r"(?:eyebrow|kicker|overline)", re.I)
_CLASSIC_KICKER_CLASS = re.compile(
    r"uppercase|tracking-(?:wide|widest)", re.I)

_CAPTION_TAGS = r"figcaption|small|p|div|span|td|th|li"
_CAPTION_CLASS = re.compile(
    r"(?:class|className)\s*=\s*[\"'][^\"']*"
    r"(?:caption|footnote|helper|hint|fine[-_ ]?print|description|"
    r"disclaimer|tooltip|note)[^\"']*[\"']", re.I)
_CAPTION_EL = re.compile(
    r"<(" + _CAPTION_TAGS + r")((?:\s[^<>]*)?)>\s*([^<]{10,240}?)\s*</\1\s*>",
    re.S)
_BOTCAPTION = re.compile(
    r"\b(?:click|tap|press|hover|select|choose|enter|fill|type|use|scroll)"
    r"\b[^.!?]{0,100}?\b(?:to|for|and then|in order to|below|above|here|now)"
    r"\b"
    r"|\bthis\s+(?:button|chart|graph|form|section|page|field|input|icon|"
    r"image|table|card|modal|dialog|link|tab|video|map|slider|menu)\b"
    r"[^.!?]{0,100}?\b(?:shows?|lets?|allows?|helps?|is used|works|"
    r"displays?|represents?|confirms?|submits?)\b"
    r"|\b(?:each|every)\s+(?:bar|slice|point|segment|row|item|step|column|"
    r"block)\s+(?:represents?|shows?|is|corresponds|equals?)\b"
    r"|\bhover\s+(?:over|for|to)\b"
    r"|\bno credit card\b|\bcancel anytime\b|\bno spam\b"
    r"|\bunsubscribe anytime\b", re.I)

_BADGE_CLASS = re.compile(
    r"(?:class|className)\s*=\s*[\"'][^\"']*"
    r"(?:badge|chip|pill|tag|status|live|dot|indicator|pulse)[^\"']*[\"']",
    re.I)
_BADGE_EL = re.compile(
    r"<(span|div|a|em|strong|small|li|td|th|button)\b((?:\s[^<>]*)?)>"
    r"\s*([^<>{}\n]{1,60}?)\s*</\1\s*>", re.S)
_STATUS_WORDS = frozenset({
    "live", "new", "beta", "pro", "ai", "hot", "updated", "synced",
    "online", "offline", "status", "preview", "soon", "deprecated",
    "legacy", "free", "plus"})
_VERSION_TOKEN = re.compile(r"v?\d+(?:\.\d+)*")

_NUM_ONLY = re.compile(
    r"^\s*(?:(?:§|//+|[./·:;—–-])\s*)*(?:0[1-9]|[1-9])"
    r"(?:(?:§|//+|[./·:;—–-])\s*)*$")
_HEAD_NUM = re.compile(
    r"<h([1-6])\b[^>]*>\s*(?:(?:<(?:span|em|strong|b|i)\b[^>]*>\s*)*)"
    r"§?\s*(?:0[1-9]|[1-9])(?:\s*//+|\s*[./·:;—–-]+)?\s*(?=[\s<])")

_HEADING_EL = re.compile(r"<h([1-6])\b[^>]*>(.*?)</h\1\s*>", re.S)
_SUBJECT_EL = re.compile(
    r"<(p|div|span|a|small|li|td|th|blockquote|figcaption|section)\b"
    r"((?:\s[^<>]*)?)>\s*([^<]{3,240}?)\s*</\1\s*>")
_GAP_ONLY = re.compile(r"(?:\s|<!--[\s\S]*?-->)*")

_STOPWORDS = frozenset({
    "the", "a", "an", "and", "or", "of", "to", "in", "for", "on", "with",
    "your", "you", "our", "we", "how", "what", "why", "is", "are", "at",
    "by", "it", "its", "that", "this", "new", "get", "all", "more", "us",
    "my", "me", "be", "as", "from", "into", "about", "over", "under",
    "per", "vs", "not", "no", "do", "does", "can", "will", "would", "so",
    "if", "then", "than", "but", "have", "has", "had", "were", "was",
    "each", "every", "any", "some", "one", "two", "out", "up", "down"})


def _strip_tags(s):
    return _unescape_html(re.sub(r"<[^>]+>", " ", s or ""))


def _norm_text(s):
    return " ".join(re.findall(r"[a-z0-9]+", _strip_tags(s).lower()))


def _content_tokens(s):
    return [t for t in re.findall(r"[a-z0-9]+", _strip_tags(s).lower())
            if len(t) >= 3 and t not in _STOPWORDS]


def _eyebrow_text(t):
    """True when t reads as an uppercase eyebrow/kicker label."""
    t = re.sub(r"\s+", " ", t).strip()
    if not (2 <= len(t) <= 48) or "{" in t or "}" in t:
        return False
    cased = [c for c in t if c.isalpha()]
    if len(cased) < 2:
        return False
    return sum(1 for c in cased if c.isupper()) / len(cased) >= 0.8


def _subtitle_repeats(htext, stext):
    """Heuristic: subtitle restates the adjacent heading (U3)."""
    if len(stext.split()) > 30:
        return False
    hn = _norm_text(htext)
    sn = _norm_text(stext)
    if len(hn) >= 6 and re.search(
            r"(?<![a-z0-9])" + re.escape(hn) + r"(?![a-z0-9])", sn):
        return True
    ht = set(_content_tokens(htext))
    st = set(_content_tokens(stext))
    if len(ht) >= 2:
        need = max(2, (len(ht) * 4 + 4) // 5)  # 80% of heading tokens
        return len(ht & st) >= need
    return False


def _jsx_unbound(prefix):
    """Cheap JSX guard: an unclosed '{' before the element means the
    literal sits inside an expression (bound) - do not flag it."""
    return prefix.count("{") <= prefix.count("}")


def check_unslop_eyebrow(html, css, path):
    hits = []
    for m in _LABEL_THEN_HEADING.finditer(html or ""):
        tag, attrs, text, lvl = m.groups()
        t = re.sub(r"\s+", " ", text).strip()
        if not t or "{" in t or "}" in t:
            continue
        hinted = bool(_EYEBROW_HINT_CLASS.search(attrs or ""))
        classic = bool(_CLASSIC_KICKER_CLASS.search(attrs or ""))
        # class=uppercase/tracking kickers are owned by
        # kicker-above-heading; this rule adds text-driven + h1-h6 reach.
        if (hinted and 2 <= len(t) <= 60) or \
                (_eyebrow_text(t) and not classic):
            hits.append(_finding(
                "unslop-eyebrow-label", path,
                html[:m.start()].count("\n") + 1,
                f"'{t[:40]}' above h{lvl}"))
        if len(hits) >= 5:
            break
    return hits


def check_unslop_numbering(html, css, path):
    hits = []
    for m in _LABEL_THEN_HEADING.finditer(html or ""):
        tag, attrs, text, lvl = m.groups()
        if len(text) <= 12 and _NUM_ONLY.fullmatch(text) \
                and any(c.isdigit() for c in text):
            hits.append(_finding(
                "unslop-decorative-numbering", path,
                html[:m.start()].count("\n") + 1,
                f"'{text.strip()[:20]}' before h{lvl}"))
        if len(hits) >= 4:
            break
    for m in _HEAD_NUM.finditer(html or ""):
        hits.append(_finding(
            "unslop-decorative-numbering", path,
            html[:m.start()].count("\n") + 1,
            f"numbered heading h{m.group(1)}"))
        if len(hits) >= 6:
            break
    return hits[:6]


def check_unslop_subtitle_repeat(html, css, path):
    hits = []
    for m in _HEADING_EL.finditer(html or ""):
        htext = _strip_tags(m.group(2)).strip()
        if len(_norm_text(htext)) < 6:
            continue
        rest = html[m.end():m.end() + 900]
        gap = _GAP_ONLY.match(rest)
        sm = _SUBJECT_EL.match(rest, gap.end())
        if not sm:
            continue
        stext = sm.group(3).strip()
        if _subtitle_repeats(htext, stext):
            hits.append(_finding(
                "unslop-subtitle-repeat", path,
                html[:m.start()].count("\n") + 1,
                f"'{htext[:30]}' ~ '{stext[:50]}'"))
        if len(hits) >= 4:
            break
    return hits


def check_unslop_caption(html, css, path):
    hits = []
    for m in _CAPTION_EL.finditer(html or ""):
        tag, attrs, text = m.groups()
        t = re.sub(r"\s+", " ", text).strip()
        caption_ctx = tag in ("figcaption", "small") or \
            bool(_CAPTION_CLASS.search(attrs or ""))
        if caption_ctx and _BOTCAPTION.search(t):
            hits.append(_finding(
                "unslop-self-explaining-caption", path,
                html[:m.start()].count("\n") + 1,
                f"'{t[:60]}'"))
        if len(hits) >= 5:
            break
    return hits


def check_unslop_dead_status(html, css, path):
    hits = []
    for m in _BADGE_EL.finditer(html or ""):
        tag, attrs, text = m.groups()
        if not _BADGE_CLASS.search(attrs or ""):
            continue
        if "{" in attrs or not _jsx_unbound(html[max(0, m.start() - 160):
                                                m.start()]):
            continue
        toks = re.findall(r"[a-z0-9.]+", text.lower())
        if not toks:
            continue
        ok = all(t in _STATUS_WORDS or _VERSION_TOKEN.fullmatch(t)
                 for t in toks)
        if ok:
            hits.append(_finding(
                "unslop-dead-status-chip", path,
                html[:m.start()].count("\n") + 1,
                f"'{text.strip()[:40]}' status literal"))
        if len(hits) >= 5:
            break
    return hits


# ---------- P4: CSS craft checks ----------

_VIEWPORT_PROPS = {"height", "min-height", "max-height",
                   "width", "min-width", "max-width"}
_COLOR_LITERAL = re.compile(
    r"#[0-9a-fA-F]{3,8}\b|(?:hsla?|rgba?|hwb|lab|lch|oklab|oklch|color)"
    r"\([^)]*\)", re.I)
_PALETTE_SEL = re.compile(
    r"(:root|html|body|\[data-theme|\.theme|\.dark|\.light|:host)", re.I)
_GRADIENT_RE = re.compile(r"(?:repeating-)?linear-gradient\s*\(")
_INTERP_RE = re.compile(
    r"\bin\s+(?:oklch|oklab|hsl|hwb|lab|lch|srgb)\b", re.I)
_CAROUSEL_SEL = re.compile(
    r"carousel|slider|scroll|track|gallery|swiper|marquee|filmstrip|strip",
    re.I)
_MASK_RE = re.compile(r"mask-image|mask\s*:|-webkit-mask", re.I)


def _decls(css):
    """Best-effort (prop, value, pos) for flat CSS declarations."""
    for m in re.finditer(r"([a-zA-Z-]+)\s*:\s*([^;{}]+)", css or ""):
        yield m.group(1).strip().lower(), m.group(2).strip(), m.start()


def _css_finditer(css):
    """_css_rules with match positions, for line numbers."""
    for m in re.finditer(r"([^{}]+)\{([^{}]*)\}", css or "", re.S):
        yield m.group(1).strip(), m.group(2), m.start()


def _norm_sel(sel):
    s = re.sub(r"\s*([>+~])\s*", r"\1", sel.strip())
    return re.sub(r"\s+", " ", s)


def _paren_end(text, open_idx):
    depth = 0
    for i in range(open_idx, len(text)):
        if text[i] == "(":
            depth += 1
        elif text[i] == ")":
            depth -= 1
            if depth == 0:
                return i
    return len(text)


def _desktop_media_spans(css):
    """Char spans of @media blocks gated to >=1024px min-width (desktop
    only - mobile viewport units are correct there)."""
    spans = []
    for m in re.finditer(r"@media\b[^{}]*\{", css or ""):
        mw = re.search(r"min-width\s*:\s*(\d+(?:\.\d+)?)px", m.group(0))
        if not mw or _num(mw.group(1)) < 1024:
            continue
        depth = 0
        for j in range(m.end() - 1, len(css)):
            if css[j] == "{":
                depth += 1
            elif css[j] == "}":
                depth -= 1
                if depth == 0:
                    spans.append((m.start(), j))
                    break
    return spans


def check_static_viewport_units(html, css, path):
    hits = []
    desktop = _desktop_media_spans(css)
    for prop, val, pos in _decls(css):
        if prop not in _VIEWPORT_PROPS:
            continue
        if not re.search(r"\b100(?:vh|vw)\b", val):
            continue
        if any(s <= pos < e for s, e in desktop):
            continue
        ln = css[:pos].count("\n") + 1
        hits.append(_finding(
            "static-viewport-units", path, ln,
            f"{prop}: {val[:50]} -> prefer dvh/svh"))
        if len(hits) >= 5:
            break
    return hits


def check_palette_sprawl(html, css, path):
    seen = {}
    first = None
    for m in re.finditer(r"--[a-zA-Z0-9_-]+\s*:\s*([^;}]+)", css or ""):
        for cm in _COLOR_LITERAL.finditer(m.group(1)):
            lit = re.sub(r"\s+", "", cm.group(0)).lower()
            if lit not in seen:
                seen[lit] = css[:m.start()].count("\n") + 1
            if first is None:
                first = m.start()
    for sel, body, pos in _css_finditer(css):
        if not _PALETTE_SEL.search(sel):
            continue
        for cm in _COLOR_LITERAL.finditer(body):
            lit = re.sub(r"\s+", "", cm.group(0)).lower()
            if lit not in seen:
                seen[lit] = css[:pos].count("\n") + 1
            if first is None or pos < first:
                first = pos
    if len(seen) > 4:
        ln = css[:first].count("\n") + 1 if first is not None else 1
        return [_finding("palette-color-sprawl", path, ln,
                         f"{len(seen)} palette colors - consider oklch")]
    return []


def check_gradient_oklch(html, css, path):
    hits = []
    for m in _GRADIENT_RE.finditer(css or ""):
        end = _paren_end(css, m.end() - 1)
        if not _INTERP_RE.search(css[m.end():end]):
            hits.append(_finding(
                "gradient-missing-oklch", path,
                css[:m.start()].count("\n") + 1,
                "linear-gradient without 'in oklch' hint"))
        if len(hits) >= 5:
            break
    return hits


def _first_px(body, prop):
    m = re.search(prop + r"\s*:\s*(\d+(?:\.\d+)?)px", body)
    return _num(m.group(1)) if m else None


def check_concentric_radius(html, css, path):
    rules = []
    for sel, body, pos in _css_finditer(css):
        radius = _first_px(body, r"border-radius")
        padding = _first_px(body, r"(?<![a-z-])padding")
        for part in sel.split(","):
            s = _norm_sel(part)
            if s:
                rules.append((s, radius, padding, pos))
    hits = []
    for i, (sel, rad, _pad, pos) in enumerate(rules):
        if rad is None:
            continue
        outer = None
        for j, (osel, orad, opad, _opos) in enumerate(rules):
            if i == j or orad is None or opad is None:
                continue
            if sel != osel and sel.startswith(osel) and \
                    sel[len(osel)] in " >+~":
                if outer is None or len(osel) > len(outer[0]):
                    outer = (osel, orad, opad)
        if not outer:
            continue
        _os, orad, opad = outer
        expected = max(0.0, orad - opad)
        if abs(rad - expected) > 1.0:
            hits.append(_finding(
                "non-concentric-radius", path,
                css[:pos].count("\n") + 1,
                f"{sel[:48]}: inner {rad:g}px != outer {orad:g}px "
                f"- pad {opad:g}px = {expected:g}px"))
        if len(hits) >= 5:
            break
    return hits


def check_unmasked_scroll(html, css, path):
    hits = []
    for sel, body, pos in _css_finditer(css):
        ox = re.search(r"overflow-x\s*:\s*(?:scroll|auto)\b", body, re.I)
        if not ox:
            om = re.search(r"(?<![a-z-])overflow\s*:\s*([^;}]+)", body, re.I)
            if om:
                toks = om.group(1).split()
                if toks and toks[0].lower() in ("scroll", "auto"):
                    ox = True
        if not ox:
            continue
        if not (_CAROUSEL_SEL.search(sel) or "scroll-snap" in body):
            continue
        if _MASK_RE.search(body):
            continue
        hits.append(_finding(
            "unmasked-horizontal-scroll", path,
            css[:pos].count("\n") + 1,
            f"{sel[:48]} overflow-x scroller, no mask-image fade"))
        if len(hits) >= 4:
            break
    return hits



CHECKS = {
    "unslop-eyebrow-label": check_unslop_eyebrow,
    "unslop-decorative-numbering": check_unslop_numbering,
    "unslop-subtitle-repeat": check_unslop_subtitle_repeat,
    "unslop-self-explaining-caption": check_unslop_caption,
    "unslop-dead-status-chip": check_unslop_dead_status,
    "static-viewport-units": check_static_viewport_units,
    "palette-color-sprawl": check_palette_sprawl,
    "gradient-missing-oklch": check_gradient_oklch,
    "non-concentric-radius": check_concentric_radius,
    "unmasked-horizontal-scroll": check_unmasked_scroll,
}
