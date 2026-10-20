/* theme.js - rtsd v2 theme registry (GDD §3.3).
   A theme = { name, palette, tiles, units, buildings, ui }. A sprite entry
   is programmer-art first: {glyph, fg, bg, shape} rendered procedurally;
   when real art exists the entry becomes {sheet:<url>, sx,sy,sw,sh} and
   Theme.sprite() blits from the sheet instead - no call-site changes.
   Both themes ship inline; nothing is fetched from a CDN. */
(function (g) {
  "use strict";

  var _sheets = {}; // url -> Image|null (async load, glyph until ready)

  function sheet(url) {
    if (!(url in _sheets)) {
      _sheets[url] = null;
      var img = new Image();
      img.onload = function () { _sheets[url] = img; };
      img.src = url;
    }
    return _sheets[url];
  }

  var CLASSES = ["Knight", "Ranger", "Cleric", "Spellbreaker", "Far Seer",
    "Archmage", "Runesmith", "Herald", "Marshal", "Enchanter", "Bard",
    "Inquisitor", "Shadowblade", "Scout", "Squire", "Cartographer",
    "Chronicler", "Inspector", "Steward", "Minion", "Worker", "Commander"];

  var BLD = ["town-hall", "barracks", "tavern", "library", "watchtower",
    "runeforge", "vault", "portal", "marketplace", "altar", "trophy-hall"];

  // unit glyphs: first letter of the class, distinct hue per class
  function unitTable(glyphFg) {
    var t = {}, hues = [0, 25, 50, 90, 140, 170, 200, 230, 260, 290, 320,
      15, 40, 65, 105, 185, 250, 275, 305, 335, 210, 60];
    CLASSES.forEach(function (c, i) {
      t[c] = { glyph: c === "Minion" ? "s" : c === "Worker" ? "w" : c[0],
        fg: glyphFg, bg: "hsl(" + hues[i % hues.length] + ",60%,42%)",
        shape: c === "Minion" ? "tri" : "disc" };
    });
    t.Worker.bg = "#8b7d4a"; t.Minion.bg = "#7a5cc0";
    t.Commander = { glyph: "C", fg: glyphFg, bg: "#c9a227", shape: "disc" };
    return t;
  }

  function bldTable(base, roof) {
    var t = {}, glyphs = { "town-hall": "H", "barracks": "B", "tavern": "T",
      "library": "L", "watchtower": "W", "runeforge": "R", "vault": "V",
      "portal": "P", "marketplace": "M", "altar": "A", "trophy-hall": "!" };
    BLD.forEach(function (b) {
      t[b] = { glyph: glyphs[b], fg: "#e6edf3", bg: base, roof: roof,
        shape: "keep" };
    });
    t.portal.fg = "#b57edc"; t.portal.bg = "#2a1f3d";
    t.watchtower.bg = "#4a4f3a"; t.altar.bg = "#3d2a2a";
    return t;
  }

  var THEMES = {
    battlefield: {
      name: "battlefield",
      palette: { bg: "#0d1710", grid: "#243825", shroud: "#090f0b",
        dim: "#121f14", text: "#f0f6ec", sel: "#ffd54a", err: "#f85149",
        ok: "#3fb950", panel: "#151c16", border: "#3b5038" },
      tiles: { 0: "#264b25", 1: "#2b5429", 2: "#315d2e", 3: "#386633",
        4: "#29502b", 5: "#234422", 6: "#356130", 7: "#284d28",
        8: "#2f582c", 9: "#3b6932", water: "#184668", waterDeep: "#113450",
        road: "#6b5840", plaza: "#786954", plot: "#5c5546",
        contested: "#5e2525" },
      units: unitTable("#f0f6ec"),
      buildings: bldTable("#3b4a3b", "#6b442a"),
      ui: { minimapBg: "#0d160f", font: "11px monospace", ping: "#ffd54a" }
    },
    office: {
      name: "office",
      iso: true,   // #134: isometric projection (engine render + picking)
      palette: { bg: "#14161c", grid: "#232733", shroud: "#0b0d12",
        dim: "#101219", text: "#e8ecf4", sel: "#ffd54a", err: "#f85149",
        ok: "#3fb950", panel: "#1b1e28", border: "#333a4d" },
      tiles: { 0: "#2b2f3c", 1: "#313647", 2: "#2e3342", 3: "#353b4e",
        4: "#292e3d", 5: "#252a38", 6: "#383f52", 7: "#2d3243",
        8: "#333a4c", 9: "#3a4157", water: "#1d3b58", waterDeep: "#152b42",
        road: "#4a4e5c", plaza: "#565b6b", plot: "#4a4a42",
        contested: "#4d2626" },
      units: unitTable("#e8ecf4"),
      buildings: bldTable("#39415a", "#5a4632"),
      ui: { minimapBg: "#10131b", font: "11px monospace", ping: "#ffd54a" }
    }
  };
  // office reskin (GDD 3.2): every battlefield id maps to an interior
  // counterpart - same data, different skin. `label` is shown in the
  // tooltip/inspector flavor; `glyph` is the map marker.
  var OFFICE_BLD = {
    "town-hall":   { glyph: "M", label: "meeting room" },
    "barracks":    { glyph: "H", label: "onboarding desk" },
    "tavern":      { glyph: "C", label: "break room" },
    "library":     { glyph: "B", label: "bookshelf" },
    "watchtower":  { glyph: "S", label: "server rack" },
    "runeforge":   { glyph: "P", label: "printer" },
    "vault":       { glyph: "W", label: "whiteboard" },
    "portal":      { glyph: "T", label: "phone booth" },
    "marketplace": { glyph: "$", label: "supply cabinet" },
    "altar":       { glyph: "~", label: "water cooler" },
    "trophy-hall": { glyph: "!", label: "kanban wall" }
  };
  BLD.forEach(function (b) {
    var o = OFFICE_BLD[b], e = THEMES.office.buildings[b];
    e.glyph = o.glyph; e.label = o.label;
    e.bg = "#39415a"; e.roof = "#59627e";
  });
  THEMES.office.buildings["portal"].fg = "#b57edc";
  THEMES.office.buildings["portal"].bg = "#2a1f3d";
  THEMES.office.buildings["altar"].bg = "#26414a";

  // theme choice persists across sessions (#134); localStorage may be
  // unavailable under file:// so every access is guarded
  var THEME_KEY = "rtsd.theme";
  function savedTheme() {
    try { return localStorage.getItem(THEME_KEY); } catch (e) {
      return null; }
  }
  function persist() {
    try { localStorage.setItem(THEME_KEY, current.name); } catch (e) {}
  }

  var current = THEMES[savedTheme()] || THEMES.battlefield;

  g.Theme = {
    all: THEMES,
    get: function () { return current; },
    set: function (name) { if (THEMES[name]) { current = THEMES[name];
      persist(); } },
    toggle: function () {
      current = current === THEMES.battlefield ? THEMES.office
        : THEMES.battlefield;
      persist();
      return current;
    },
    /* Draw one sprite. entry={glyph,fg,bg,shape} or {sheet,sx,sy,sw,sh}.
       #136 perf pass: procedural entries are rasterized once into an
       offscreen canvas (keyed on the entry object) and then blitted with
       drawImage - one draw call per entity instead of path+text every
       frame. */
    sprite: function (ctx, entry, x, y, w, h) {
      if (!entry) return;
      if (entry.sheet) {
        var img = sheet(entry.sheet);
        if (img) {
          ctx.drawImage(img, entry.sx, entry.sy, entry.sw, entry.sh,
            x, y, w, h);
          return;
        }
      }
      var SP = 80;                      // raster box (margin for roofs)
      if (!entry._spr) {
        var c = document.createElement("canvas");
        c.width = SP; c.height = SP;
        entry._spr = c;
        var g2 = c.getContext("2d");
        Theme._paint(g2, entry, 8, 14, 64, 64);
      }
      ctx.drawImage(entry._spr, 0, 0, SP, SP,
        x - w * 8 / 64, y - h * 14 / 64, w * SP / 64, h * SP / 64);
    },
    // procedural painter: draws one entry into ctx at the given box
    _paint: function (ctx, entry, x, y, w, h) {
      var r = Math.min(w, h) / 2, cx = x + w / 2, cy = y + h / 2;
      ctx.fillStyle = entry.bg || "#444";
      if (entry.shape === "tri") {
        ctx.beginPath();
        ctx.moveTo(cx, cy - r); ctx.lineTo(cx + r, cy + r);
        ctx.lineTo(cx - r, cy + r); ctx.closePath(); ctx.fill();
      } else if (entry.shape === "keep") {
        ctx.fillRect(x + 1, y + 1, w - 2, h - 2);
        ctx.fillStyle = entry.roof || "#222";
        ctx.beginPath();
        ctx.moveTo(x, y + 1); ctx.lineTo(cx, y - 4); ctx.lineTo(x + w, y + 1);
        ctx.closePath(); ctx.fill();
      } else {
        ctx.beginPath(); ctx.arc(cx, cy, r, 0, 7); ctx.fill();
      }
      if (entry.glyph) {
        ctx.fillStyle = entry.fg || "#fff";
        ctx.font = "bold " + Math.round(r) + "px monospace";
        ctx.textAlign = "center"; ctx.textBaseline = "middle";
        ctx.fillText(entry.glyph, cx, cy);
      }
    }
  };
})(window);
