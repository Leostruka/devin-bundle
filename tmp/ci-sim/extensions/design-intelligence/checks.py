#!/usr/bin/env python3
"""checks.py - pure static checks for the design_lint subset.

Each check takes (html_text, css_text, relpath) and yields finding dicts
{rule, file, line, evidence}. Browser-scoped rules are never run here.
Heuristics follow impeccable's rule intent, adapted to a static pass.
"""
import re
from html.parser import HTMLParser

# ---------- helpers ----------

_FONT_OVERUSED = ("inter", "roboto", "geist", "fraunces", "poppins",
                  "open sans", "montserrat", "lato")
_BUZZWORDS = ("delve", "leverage", "unlock", "elevate", "seamless",
              "cutting-edge", "revolutionary", "empower", "supercharge",
              "unleash", "game-changer", "next-level", "reimagine")
_THEATER = ("step into", "welcome to the future", "a new era",
            "redefining", "where .* meets", "elevate your",
            "the future of", "reimagined")
_CREAM = ("beige", "cream", "ivory", "linen", "faf7f2", "f5f0e8",
          "fdf6e3", "fffbf5", "faf3e0", "f9f5ef", "f4ecd8")
_PURPLE = ("purple", "violet", "8b5cf6", "a855f7", "7c3aed", "9333ea",
           "6366f1", "indigo")
_CYANBLUE = ("cyan", "blue", "06b6d4", "3b82f6", "0ea5e9", "60a5fa",
             "sky", "22d3ee")
_PLACEHOLDER_HOSTS = ("placehold.co", "via.placeholder", "dummyimage",
                      "picsum.photos", "loremflickr", "lorem ipsum")
_GRAY_TEXT = re.compile(r"text-(gray|slate|zinc|neutral)-\d+")
_COLOR_BG = re.compile(r"bg-(?!gray|slate|zinc|neutral|white|black)"
                       r"[a-z]+-(?:[4-9]\d{2})")


def _finding(rule, path, line, evidence):
    return {"rule": rule, "file": path, "line": line,
            "evidence": evidence[:120]}


def _css_rules(css):
    """Yield (selector, body) for each CSS rule, incl. <style> content."""
    for m in re.finditer(r"([^{}]+)\{([^{}]*)\}", css or "", re.S):
        yield m.group(1).strip(), m.group(2)


def _num(px):
    try:
        return float(px)
    except (TypeError, ValueError):
        return 0.0


# ---------- HTML structure collector ----------

class _Doc(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.imgs = []
        self.headings = []          # (level, line)
        self.text = []
        self.classes = []           # (classstr, tag, line)
        self.stack = []

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        line = self.getpos()[0]
        if tag == "img":
            self.imgs.append((a, line))
        if re.fullmatch(r"h[1-6]", tag):
            self.headings.append((int(tag[1]), line))
        cls = a.get("class", "")
        if cls:
            self.classes.append((cls, tag, line))
        self.stack.append((tag, a, line))

    def handle_endtag(self, tag):
        for i in range(len(self.stack) - 1, -1, -1):
            if self.stack[i][0] == tag:
                del self.stack[i:]
                break

    def handle_data(self, data):
        self.text.append(data)


def collect(html):
    d = _Doc()
    try:
        d.feed(html or "")
    except Exception:
        pass  # fail-soft: cleanup; preserve primary error
    return d


# ---------- checks ----------

def check_side_tab(html, css, path):
    hits = []
    for m in re.finditer(
            r"border-(?:left|right)\s*:\s*(\d+)px\s+solid\s+([^;}]+)",
            css or ""):
        if _num(m.group(1)) >= 4 and not re.search(
                r"gray|slate|zinc|neutral|#(?:e|d|f)\w{2,5}\b|rgba?\(2\d\d",
                m.group(2), re.I):
            ln = css[:m.start()].count("\n") + 1
            hits.append(_finding("side-tab", path, ln, m.group(0)))
    return hits


def check_border_accent_rounded(html, css, path):
    hits = []
    for sel, body in _css_rules(css):
        rad = re.search(r"border-radius\s*:\s*(\d+)", body)
        bor = re.search(r"border(?:-color)?\s*:[^;}]*"
                        r"(blue|purple|cyan|violet|indigo|#[0-9a-fA-F]{3,8}"
                        r"|hsl|rgb)", body, re.I)
        if rad and _num(rad.group(1)) >= 8 and bor:
            ln = css[:css.find(body)].count("\n") + 1
            hits.append(_finding("border-accent-on-rounded", path, ln,
                                 sel.strip()[:60]))
    return hits


def check_overused_font(html, css, path):
    hits = []
    for m in re.finditer(r"font-family\s*:([^;}]+)", css or "", re.I):
        fams = m.group(1).lower()
        for f in _FONT_OVERUSED:
            if f in fams:
                ln = css[:m.start()].count("\n") + 1
                hits.append(_finding("overused-font", path, ln,
                                     m.group(0)[:80]))
                break
    return hits


def check_gradient_text(html, css, path):
    hits = []
    for sel, body in _css_rules(css):
        if re.search(r"(linear|conic|radial)-gradient", body) and re.search(
                r"text-fill-color\s*:\s*transparent|color\s*:\s*transparent",
                body):
            hits.append(_finding("gradient-text", path, 1,
                                 sel.strip()[:60]))
    return hits


def check_ai_color_palette(html, css, path):
    hits = []
    low = (css or "").lower()
    has_p = any(c in low for c in _PURPLE)
    has_b = any(c in low for c in _CYANBLUE)
    if has_p and has_b and "gradient" in low:
        ln = next((i + 1 for i, l in enumerate(low.split("\n"))
                   if "gradient" in l and any(c in l for c in _PURPLE)), 1)
        hits.append(_finding("ai-color-palette", path, ln,
                             "purple/violet + blue/cyan gradient"))
    return hits


def check_cream_palette(html, css, path):
    low = (css or "").lower()
    for c in _CREAM:
        for m in re.finditer(r"background[^;}]*" + re.escape(c), low):
            return [_finding("cream-palette", path,
                             low[:m.start()].count("\n") + 1,
                             f"background uses {c}")]
    return []


def check_nested_cards(html, css, path):
    hits = []
    doc = collect(html)
    cardish = re.compile(r"(?=.*rounded)(?=.*(shadow|border))")
    depth = []
    for cls, tag, line in doc.classes:
        while depth and depth[-1][2] != tag and len(depth) > 3:
            depth.pop()
        if cardish.search(cls):
            depth.append((cls, line, tag))
            if len([1 for c, _, _ in depth if cardish.search(c)]) >= 2:
                hits.append(_finding("nested-cards", path, line,
                                     cls[:80]))
                depth.clear()
        elif len(depth) > 8:
            depth.clear()
    return hits[:3]


def check_bounce_easing(html, css, path):
    hits = []
    for m in re.finditer(r"cubic-bezier\(([^)]+)\)", css or ""):
        nums = [x.strip() for x in m.group(1).split(",")]
        if len(nums) == 4 and (_num(nums[1]) > 1 or _num(nums[3]) > 1
                               or _num(nums[1]) < 0 or _num(nums[3]) < 0):
            hits.append(_finding("bounce-easing", path,
                                 css[:m.start()].count("\n") + 1,
                                 m.group(0)))
    for m in re.finditer(r"transition[^;}]*\b(bounce|elastic|spring)\b",
                         css or "", re.I):
        hits.append(_finding("bounce-easing", path,
                             css[:m.start()].count("\n") + 1,
                             m.group(0)[:80]))
    return hits


def check_pulsing_dot(html, css, path):
    hits = []
    for cls, tag, line in collect(html).classes:
        if re.search(r"animate-(ping|pulse)", cls) and re.search(
                r"rounded-full|h-\d\s+w-\d|w-\d\s+h-\d|dot", cls):
            hits.append(_finding("pulsing-dot", path, line, cls[:80]))
    for m in re.finditer(r"@keyframes\s+(ping|pulse)[\s{]", css or ""):
        hits.append(_finding("pulsing-dot", path,
                             css[:m.start()].count("\n") + 1,
                             m.group(0)))
    return hits


def check_blinking_cursor(html, css, path):
    hits = []
    for m in re.finditer(r"content\s*:\s*['\"|]+['\"]", css or ""):
        if re.search(r"(blink|caret|cursor)", css[m.start():m.start() + 300],
                     re.I):
            hits.append(_finding("blinking-cursor", path,
                                 css[:m.start()].count("\n") + 1,
                                 m.group(0)))
    for m in re.finditer(r"animation[^;}]*\bblink", css or "", re.I):
        hits.append(_finding("blinking-cursor", path,
                             css[:m.start()].count("\n") + 1,
                             m.group(0)[:80]))
    return hits


def check_hard_offset_shadow(html, css, path):
    hits = []
    for m in re.finditer(
            r"box-shadow\s*:\s*(\d+)px\s+(\d+)px\s+0(?:px)?\b[^;}]*",
            css or ""):
        if _num(m.group(1)) >= 3 or _num(m.group(2)) >= 3:
            hits.append(_finding("hard-offset-shadow", path,
                                 css[:m.start()].count("\n") + 1,
                                 m.group(0)[:80]))
    return hits


def check_dark_glow(html, css, path):
    hits = []
    for m in re.finditer(
            r"box-shadow\s*:[^;}]*(?:rgba?\([^)]*\)|(?:cyan|violet|purple|"
            r"fuchsia|magenta|blue)[^;}]*)", css or "", re.I):
        seg = m.group(0)
        blur = re.search(r"\d+px\s+(\d+)px", seg)
        if (blur and _num(blur.group(1)) >= 16) or re.search(
                r"(cyan|violet|purple|fuchsia|magenta)", seg, re.I):
            hits.append(_finding("dark-glow", path,
                                 css[:m.start()].count("\n") + 1,
                                 seg[:80]))
    return hits


def check_radial_halo(html, css, path):
    return [_finding("radial-halo", path,
                     css[:m.start()].count("\n") + 1, m.group(0)[:80])
            for m in re.finditer(
                r"background[^;}]*radial-gradient", css or "")]


def check_radial_spotlight(html, css, path):
    hits = []
    for sel, body in _css_rules(css):
        if "radial-gradient" in body and re.search(
                r"(absolute|fixed|pointer-events|z-index|inset)", body):
            hits.append(_finding("radial-spotlight-glow", path, 1,
                                 sel.strip()[:60]))
    return hits


def check_repeating_stripes(html, css, path):
    return [_finding("repeating-stripes-gradient", path,
                     css[:m.start()].count("\n") + 1, m.group(0)[:80])
            for m in re.finditer(r"repeating-(linear|conic)-gradient",
                                 css or "")]


def check_codex_grid(html, css, path):
    hits = []
    for sel, body in _css_rules(css):
        if "linear-gradient" in body and re.search(
                r"background-(size|image)[^;}]*(\d{1,3}px)", body):
            hits.append(_finding("codex-grid-background", path, 1,
                                 sel.strip()[:60]))
    return hits


def check_thin_border_wide_shadow(html, css, path):
    hits = []
    for sel, body in _css_rules(css):
        thin = re.search(r"border\s*:\s*1px", body)
        wide = re.search(r"box-shadow[^;}]*\s(\d{2,})px", body)
        if thin and wide and _num(wide.group(1)) >= 24:
            hits.append(_finding("gpt-thin-border-wide-shadow", path, 1,
                                 sel.strip()[:60]))
    return hits


def check_marquee(html, css, path):
    hits = []
    for m in re.finditer(r"<marquee|animate-marquee|animation[^;}]*marquee",
                         html + "\n" + (css or ""), re.I):
        src = html + "\n" + (css or "")
        hits.append(_finding("marquee", path,
                             src[:m.start()].count("\n") + 1,
                             m.group(0)[:80]))
    for m in re.finditer(r"@keyframes\s+\w*marquee", css or "", re.I):
        hits.append(_finding("marquee", path,
                             css[:m.start()].count("\n") + 1,
                             m.group(0)))
    return hits


def check_em_dash_overuse(html, css, path):
    text = re.sub(r"<[^>]+>", " ", html or "")
    count = text.count("\u2014")
    if count > 3:
        return [_finding("em-dash-overuse", path, 1,
                         f"{count} em-dashes in visible copy")]
    return []


def check_marketing_buzzword(html, css, path):
    hits = []
    text = re.sub(r"<[^>]+>", " ", html or "").lower()
    for w in _BUZZWORDS:
        if re.search(r"\b" + re.escape(w) + r"\b", text):
            hits.append(_finding("marketing-buzzword", path, 1, w))
    return hits[:4]


def check_aphoristic_cadence(html, css, path):
    text = re.sub(r"<[^>]+>", " ", html or "")
    if re.search(r"\b(No|Not)\s+[\w']+\.\s*(No|Not|Just)\b", text):
        return [_finding("aphoristic-cadence", path, 1,
                         "No X. Just Y. cadence")]
    return []


def check_theater_slop(html, css, path):
    text = re.sub(r"<[^>]+>", " ", html or "").lower()
    hits = []
    for p in _THEATER:
        if re.search(p, text):
            hits.append(_finding("theater-slop-phrase", path, 1, p))
    return hits[:3]


def check_oversized_h1(html, css, path):
    hits = []
    for sel, body in _css_rules(css):
        if re.search(r"\bh1\b", sel, re.I):
            m = re.search(r"font-size\s*:\s*([\d.]+)(rem|px)", body)
            if m:
                px = _num(m.group(1)) * (16 if m.group(2) == "rem" else 1)
                if px >= 64:
                    hits.append(_finding("oversized-h1", path, 1,
                                         f"h1 {px}px"))
    for cls, tag, line in collect(html).classes:
        if tag == "h1" and re.search(
                r"text-(6|7|8|9)xl|text-\[\d{3,}", cls):
            hits.append(_finding("oversized-h1", path, line, cls[:60]))
    return hits


def check_extreme_tracking(html, css, path):
    hits = []
    for m in re.finditer(r"letter-spacing\s*:\s*-?([\d.]+)(em|px)",
                         css or ""):
        v = _num(m.group(1))
        vpx = v * 16 if m.group(2) == "em" else v
        if "-" in m.group(0) and vpx > 0.5:
            hits.append(_finding("extreme-negative-tracking", path,
                                 css[:m.start()].count("\n") + 1,
                                 m.group(0)))
    return hits


def check_italic_serif(html, css, path):
    hits = []
    for sel, body in _css_rules(css):
        if re.search(r"\bh[12]\b", sel, re.I) \
                and "italic" in body \
                and re.search(r"serif", body):
            hits.append(_finding("italic-serif-display", path, 1,
                                 sel.strip()[:60]))
    return hits


def check_hero_eyebrow_chip(html, css, path):
    hits = []
    for m in re.finditer(
            r"class=\"[^\"]*(rounded-full|pill|badge|chip)[^\"]*\"[^>]*>"
            r"[^<]{1,80}</[a-z]+>\s*<h1", html or "", re.I):
        hits.append(_finding("hero-eyebrow-chip", path,
                             html[:m.start()].count("\n") + 1,
                             m.group(0)[:80]))
    return hits


def check_kicker_above_heading(html, css, path):
    hits = []
    for m in re.finditer(
            r"class=\"[^\"]*(uppercase|tracking-(wide|widest))[^\"]*\"[^>]*>"
            r"[^<]{1,80}</[a-z]+>\s*<h[12]", html or "", re.I):
        hits.append(_finding("kicker-above-heading", path,
                             html[:m.start()].count("\n") + 1,
                             m.group(0)[:80]))
    return hits


def check_numbered_labels(html, css, path):
    hits = []
    for m in re.finditer(r">\s*0[1-9]\s*[\./—-]", html or ""):
        hits.append(_finding("numbered-section-labels", path,
                             html[:m.start()].count("\n") + 1,
                             m.group(0)[:40]))
    return hits[:3]


def check_icon_tile_stack(html, css, path):
    hits = []
    for m in re.finditer(
            r"<div[^>]*rounded[^>]*>\s*<(svg|img|i)[^>]*>.*?</div>\s*"
            r"<h[1-3]", html or "", re.S):
        hits.append(_finding("icon-tile-stack", path,
                             html[:m.start()].count("\n") + 1,
                             m.group(0)[:60]))
    return hits[:3]


def check_gray_on_color(html, css, path):
    hits = []
    for m in re.finditer(r"class=\"([^\"]+)\"", html or ""):
        cls = m.group(1)
        if _GRAY_TEXT.search(cls) and _COLOR_BG.search(cls):
            hits.append(_finding("gray-on-color", path,
                                 html[:m.start()].count("\n") + 1,
                                 cls[:80]))
    return hits[:4]


def _lum(hexc):
    hexc = hexc.lstrip("#")
    if len(hexc) == 3:
        hexc = "".join(c * 2 for c in hexc)
    if len(hexc) != 6:
        return None
    rgb = [int(hexc[i:i + 2], 16) / 255 for i in (0, 2, 4)]
    rgb = [c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4
           for c in rgb]
    return 0.2126 * rgb[0] + 0.7152 * rgb[1] + 0.0722 * rgb[2]


def check_low_contrast(html, css, path):
    hits = []
    for sel, body in _css_rules(css):
        fg = re.search(r"(?<![-\w])color\s*:\s*(#[0-9a-fA-F]{3,6})", body)
        bg = re.search(r"background(?:-color)?\s*:\s*(#[0-9a-fA-F]{3,6})",
                       body)
        if fg and bg:
            lf, lb = _lum(fg.group(1)), _lum(bg.group(1))
            if lf is not None and lb is not None:
                hi, lo = max(lf, lb), min(lf, lb)
                ratio = (hi + 0.05) / (lo + 0.05)
                if ratio < 4.5:
                    hits.append(_finding("low-contrast", path, 1,
                                         f"{sel.strip()[:40]} ratio "
                                         f"{ratio:.2f}"))
    return hits


def check_line_length(html, css, path):
    hits = []
    for m in re.finditer(r"max-width\s*:\s*(\d+)(ch|px)", css or ""):
        v = _num(m.group(1))
        if (m.group(2) == "ch" and v > 75) or \
                (m.group(2) == "px" and v > 1100):
            hits.append(_finding("line-length", path,
                                 css[:m.start()].count("\n") + 1,
                                 m.group(0)))
    return hits


def check_cramped_padding(html, css, path):
    hits = []
    for sel, body in _css_rules(css):
        if re.search(r"(card|panel|tile|shadow|rounded)", sel):
            m = re.search(r"padding\s*:\s*(\d+)px", body)
            if m and _num(m.group(1)) < 8:
                hits.append(_finding("cramped-padding", path, 1,
                                     sel.strip()[:50]))
    return hits


def check_tight_leading(html, css, path):
    hits = []
    for m in re.finditer(r"line-height\s*:\s*([\d.]+)", css or ""):
        v = _num(m.group(1))
        if 0 < v < 1.2:
            hits.append(_finding("tight-leading", path,
                                 css[:m.start()].count("\n") + 1,
                                 m.group(0)))
    return hits


def check_skipped_heading(html, css, path):
    hits = []
    prev = None
    for lvl, line in collect(html).headings:
        if prev is not None and lvl - prev > 1:
            hits.append(_finding("skipped-heading", path, line,
                                 f"h{prev} -> h{lvl}"))
        prev = lvl
    return hits


def check_justified_text(html, css, path):
    return [_finding("justified-text", path,
                     css[:m.start()].count("\n") + 1, m.group(0))
            for m in re.finditer(r"text-align\s*:\s*justify",
                                 css or "")]


def check_tiny_text(html, css, path):
    hits = []
    for sel, body in _css_rules(css):
        m = re.search(r"font-size\s*:\s*([\d.]+)px", body)
        if m and _num(m.group(1)) < 12 and not re.search(
                r"icon|badge|chip|label|caption|sr-only", sel):
            hits.append(_finding("tiny-text", path, 1,
                                 f"{sel.strip()[:40]} {m.group(1)}px"))
    return hits


def check_undersized_ui_text(html, css, path):
    hits = []
    for sel, body in _css_rules(css):
        if re.search(r"(button|input|nav|label|menu|tab)", sel, re.I):
            m = re.search(r"font-size\s*:\s*([\d.]+)px", body)
            if m and _num(m.group(1)) < 10:
                hits.append(_finding("undersized-ui-text", path, 1,
                                     f"{sel.strip()[:40]} {m.group(1)}px"))
    return hits


def check_all_caps_body(html, css, path):
    hits = []
    for sel, body in _css_rules(css):
        if re.search(r"(^|\s|\.)(p|body|span|div)\b", sel) \
                and "text-transform" in body and "uppercase" in body:
            hits.append(_finding("all-caps-body", path, 1,
                                 sel.strip()[:40]))
    return hits


def check_wide_tracking(html, css, path):
    hits = []
    for sel, body in _css_rules(css):
        m = re.search(r"letter-spacing\s*:\s*([\d.]+)(em|px)", body)
        if m and re.search(r"(p|body|span|li)\b", sel):
            v = _num(m.group(1)) * (1 if m.group(2) == "em" else 0.0625)
            if v > 0.1:
                hits.append(_finding("wide-tracking", path, 1,
                                     sel.strip()[:40]))
    return hits


def check_broken_image(html, css, path):
    hits = []
    for attrs, line in collect(html).imgs:
        src = (attrs.get("src") or "").strip().lower()
        if not src or any(h in src for h in _PLACEHOLDER_HOSTS):
            hits.append(_finding("broken-image", path, line,
                                 src[:60] or "empty src"))
    return hits


def check_content_hidden(html, css, path):
    hits = []
    for m in re.finditer(r"<main[^>]*class=\"[^\"]*(opacity-0|hidden)",
                         html or ""):
        hits.append(_finding("content-hidden-at-rest", path,
                             html[:m.start()].count("\n") + 1,
                             m.group(0)[:60]))
    return hits


def check_monotonous_spacing(html, css, path):
    vals = re.findall(r"(?:gap|margin|padding)[^;}]*:\s*(\d+)px",
                      css or "")
    from collections import Counter
    for v, n in Counter(vals).most_common(1):
        if n >= 6:
            return [_finding("monotonous-spacing", path, 1,
                             f"{v}px repeated {n}x")]
    return []


def check_repeated_container_text(html, css, path):
    doc = collect(html)
    from collections import Counter
    texts = Counter(t.strip() for t in doc.text
                    if len(t.strip()) > 12)
    for t, n in texts.most_common(3):
        if n >= 3:
            return [_finding("repeated-container-text", path, 1,
                             f"'{t[:40]}' x{n}")]
    return []


def check_flat_type(html, css, path):
    sizes = {}
    for sel, body in _css_rules(css):
        m = re.match(r"^\s*(h[1-6])\s*$", sel, re.I)
        f = re.search(r"font-size\s*:\s*([\d.]+)(rem|px)", body)
        if m and f:
            sizes[m.group(1).lower()] = _num(f.group(1)) * (
                16 if f.group(2) == "rem" else 1)
    vals = set(sizes.values())
    if len(sizes) >= 3 and len(vals) <= 1:
        return [_finding("flat-type-hierarchy", path, 1,
                         f"{len(sizes)} headings same size")]
    return []


def check_shape_assembled(html, css, path):
    hits = []
    for m in re.finditer(
            r"class=\"[^\"]*(rounded-(full|\[50)|aspect-square)[^\"]*"
            r"(absolute|overflow)[^\"]*\"", html or ""):
        hits.append(_finding("shape-assembled-illustration", path,
                             html[:m.start()].count("\n") + 1,
                             m.group(0)[:60]))
    return hits[:2]


CHECKS = {
    "side-tab": check_side_tab,
    "border-accent-on-rounded": check_border_accent_rounded,
    "overused-font": check_overused_font,
    "gradient-text": check_gradient_text,
    "ai-color-palette": check_ai_color_palette,
    "cream-palette": check_cream_palette,
    "nested-cards": check_nested_cards,
    "bounce-easing": check_bounce_easing,
    "pulsing-dot": check_pulsing_dot,
    "blinking-cursor": check_blinking_cursor,
    "hard-offset-shadow": check_hard_offset_shadow,
    "dark-glow": check_dark_glow,
    "radial-halo": check_radial_halo,
    "radial-spotlight-glow": check_radial_spotlight,
    "repeating-stripes-gradient": check_repeating_stripes,
    "codex-grid-background": check_codex_grid,
    "gpt-thin-border-wide-shadow": check_thin_border_wide_shadow,
    "marquee": check_marquee,
    "em-dash-overuse": check_em_dash_overuse,
    "marketing-buzzword": check_marketing_buzzword,
    "aphoristic-cadence": check_aphoristic_cadence,
    "theater-slop-phrase": check_theater_slop,
    "oversized-h1": check_oversized_h1,
    "extreme-negative-tracking": check_extreme_tracking,
    "italic-serif-display": check_italic_serif,
    "hero-eyebrow-chip": check_hero_eyebrow_chip,
    "kicker-above-heading": check_kicker_above_heading,
    "numbered-section-labels": check_numbered_labels,
    "icon-tile-stack": check_icon_tile_stack,
    "gray-on-color": check_gray_on_color,
    "low-contrast": check_low_contrast,
    "line-length": check_line_length,
    "cramped-padding": check_cramped_padding,
    "tight-leading": check_tight_leading,
    "skipped-heading": check_skipped_heading,
    "justified-text": check_justified_text,
    "tiny-text": check_tiny_text,
    "undersized-ui-text": check_undersized_ui_text,
    "all-caps-body": check_all_caps_body,
    "wide-tracking": check_wide_tracking,
    "broken-image": check_broken_image,
    "content-hidden-at-rest": check_content_hidden,
    "monotonous-spacing": check_monotonous_spacing,
    "repeated-container-text": check_repeated_container_text,
    "flat-type-hierarchy": check_flat_type,
    "shape-assembled-illustration": check_shape_assembled,
}
