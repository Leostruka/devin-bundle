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

  var ARCHETYPE = {
    Knight: "martial", Marshal: "martial", Squire: "martial",
    Commander: "commander",
    Ranger: "ranger", Scout: "ranger", Cartographer: "ranger",
    Cleric: "cleric", Inquisitor: "cleric", Steward: "cleric",
    Archmage: "caster", "Far Seer": "caster", Enchanter: "caster",
    Spellbreaker: "caster", Chronicler: "caster",
    Runesmith: "smith", Inspector: "smith",
    Bard: "bard", Herald: "bard",
    Shadowblade: "rogue",
    Worker: "worker", Minion: "minion"
  };

  // unit glyphs: first letter of the class, distinct hue + WC3 archetype
  function unitTable(glyphFg) {
    var t = {}, hues = [210, 115, 48, 275, 185, 230, 22, 340, 195, 295, 320,
      0, 260, 95, 205, 160, 245, 35, 145, 270, 42, 45];
    CLASSES.forEach(function (c, i) {
      var h = hues[i % hues.length];
      t[c] = {
        cls: c,
        arch: ARCHETYPE[c] || "martial",
        glyph: c === "Minion" ? "s" : c === "Worker" ? "w" : c[0],
        fg: glyphFg,
        bg: "hsl(" + h + ",64%,44%)",
        trim: "hsl(" + h + ",78%,68%)",
        dark: "hsl(" + h + ",55%,24%)",
        shape: c === "Minion" ? "tri" : "disc"
      };
    });
    t.Worker.bg = "#9e7b42"; t.Worker.trim = "#e3c567"; t.Worker.dark = "#523d1e";
    t.Minion.bg = "#6f52b8"; t.Minion.trim = "#b59df0"; t.Minion.dark = "#382666";
    t.Commander = {
      cls: "Commander", arch: "commander", glyph: "C", fg: glyphFg,
      bg: "#d4a72c", trim: "#fff099", dark: "#6e500f", shape: "disc"
    };
    return t;
  }

  function bldTable(base, roof) {
    var t = {}, glyphs = { "town-hall": "H", "barracks": "B", "tavern": "T",
      "library": "L", "watchtower": "W", "runeforge": "R", "vault": "V",
      "portal": "P", "marketplace": "M", "altar": "A", "trophy-hall": "!" };
    BLD.forEach(function (b) {
      t[b] = { bid: b, glyph: glyphs[b], fg: "#f0f6fc", bg: base, roof: roof,
        shape: "keep" };
    });
    t["town-hall"].roof = "#254e8a";
    t["barracks"].roof = "#7d2922";
    t["tavern"].roof = "#7c5127";
    t["library"].roof = "#235c78";
    t["watchtower"].bg = "#525848"; t["watchtower"].roof = "#32496b";
    t["runeforge"].bg = "#3d3834"; t["runeforge"].roof = "#5c2c1d";
    t["vault"].roof = "#8c6d23";
    t["portal"].fg = "#d8b4fe"; t["portal"].bg = "#2a1f3d";
    t["portal"].roof = "#553285";
    t["marketplace"].roof = "#9c2f2f";
    t["altar"].bg = "#474254"; t["altar"].roof = "#6b5428";
    t["trophy-hall"].roof = "#967424";
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
      var SP = 96;                      // high-res 3D raster box (#163)
      if (!entry._spr) {
        var c = document.createElement("canvas");
        c.width = SP; c.height = SP;
        entry._spr = c;
        var g2 = c.getContext("2d");
        Theme._paint(g2, entry, 10, 16, 76, 76);
      }
      ctx.drawImage(entry._spr, 0, 0, SP, SP,
        x - w * 10 / 76, y - h * 16 / 76, w * SP / 76, h * SP / 76);
    },

    // #163 3D PBR-inspired volumetric gradient helpers (Lambertian +
    // Blinn-Phong specular hotspot + terminator shadow + Fresnel rim)
    _cylGrad: function (ctx, x, w, hi, mid, dark, rim) {
      var g = ctx.createLinearGradient(x, 0, x + w, 0);
      g.addColorStop(0.0, mid);
      g.addColorStop(0.22, hi);
      g.addColorStop(0.55, mid);
      g.addColorStop(0.85, dark);
      g.addColorStop(1.0, rim || mid);
      return g;
    },
    _sphereGrad: function (ctx, cx, cy, r, hi, mid, dark) {
      var g = ctx.createRadialGradient(
        cx - r * 0.35, cy - r * 0.35, r * 0.08, cx, cy, r);
      g.addColorStop(0.0, hi);
      g.addColorStop(0.45, mid);
      g.addColorStop(1.0, dark);
      return g;
    },
    _roof3D: function (ctx, x0, yBase, cx, yPeak, x1, colW, colE, trim) {
      // Sunlit West roof slope
      ctx.fillStyle = colW;
      ctx.beginPath();
      ctx.moveTo(x0, yBase); ctx.lineTo(cx, yPeak);
      ctx.lineTo(cx, yBase + 2); ctx.closePath(); ctx.fill();
      // Shadowed East roof slope
      ctx.fillStyle = colE;
      ctx.beginPath();
      ctx.moveTo(cx, yPeak); ctx.lineTo(x1, yBase);
      ctx.lineTo(cx, yBase + 2); ctx.closePath(); ctx.fill();
      // Shingle course lines + golden ridge beam
      ctx.strokeStyle = "rgba(0,0,0,0.25)";
      ctx.lineWidth = 1;
      for (var s = 0.35; s < 0.9; s += 0.28) {
        var sy = yPeak + (yBase - yPeak) * s;
        var hw = (x1 - x0) * 0.5 * s;
        ctx.beginPath();
        ctx.moveTo(cx - hw, sy); ctx.lineTo(cx + hw, sy);
        ctx.stroke();
      }
      ctx.strokeStyle = trim || "#d4a72c";
      ctx.lineWidth = 1.5;
      ctx.beginPath();
      ctx.moveTo(x0, yBase); ctx.lineTo(cx, yPeak); ctx.lineTo(x1, yBase);
      ctx.stroke();
      ctx.lineWidth = 1;
    },

    // procedural painter: draws 3D-lit WC3/AoE3 architectural buildings &
    // heroic unit silhouettes into ctx at the given box (#158/#163)
    _paint: function (ctx, entry, x, y, w, h) {
      if (entry.shape === "keep") {
        Theme._paintBuilding(ctx, entry, x, y, w, h);
      } else {
        Theme._paintUnit(ctx, entry, x, y, w, h);
      }
    },

    _paintBuilding: function (ctx, entry, x, y, w, h) {
      var cx = x + w / 2, cy = y + h / 2, bid = entry.bid || "vault";
      // 1. Deep Ambient Occlusion (AO) radial contact shadow + 3D stone plinth
      var ao = ctx.createRadialGradient(
        cx + 3, y + h - 4, w * 0.1, cx + 3, y + h - 4, w * 0.56);
      ao.addColorStop(0, "rgba(0,0,0,0.62)");
      ao.addColorStop(0.7, "rgba(0,0,0,0.28)");
      ao.addColorStop(1, "rgba(0,0,0,0)");
      ctx.fillStyle = ao;
      ctx.beginPath();
      ctx.ellipse(cx + 3, y + h - 3, w * 0.55, h * 0.25, 0, 0, 7);
      ctx.fill();
      // Beveled stone foundation (lit front + shadowed right side)
      ctx.fillStyle = Theme._cylGrad(ctx, x + 2, w - 4,
                                     "#8c8576", "#666052", "#3d3930", "#595448");
      ctx.fillRect(x + 2, y + h - 13, w - 4, 10);
      ctx.strokeStyle = "#26231d";
      ctx.lineWidth = 1.4;
      ctx.strokeRect(x + 2, y + h - 13, w - 4, 10);

      if (bid === "town-hall") {
        // 3D Keep / Town Center: cylindrical twin towers + axonometric central hall
        ctx.fillStyle = Theme._cylGrad(ctx, x + 2, 16,
                                       "#b0b7c2", "#7d8490", "#454a52", "#686e78");
        ctx.fillRect(x + 2, y + 14, 16, h - 23);
        ctx.fillStyle = Theme._cylGrad(ctx, x + w - 18, 16,
                                       "#9ca3ae", "#6c737e", "#3b3f47", "#585e68");
        ctx.fillRect(x + w - 18, y + 14, 16, h - 23);
        // Central hall (lit South face + shadowed East wing)
        ctx.fillStyle = "#949aa6";
        ctx.fillRect(x + 14, y + 18, (w - 28) * 0.65, h - 27);
        ctx.fillStyle = "#626873";
        ctx.fillRect(x + 14 + (w - 28) * 0.65, y + 18,
                     (w - 28) * 0.35, h - 27);
        // Timber cross-beams
        ctx.strokeStyle = "#4d351e"; ctx.lineWidth = 1.6;
        ctx.strokeRect(x + 14, y + 18, w - 28, h - 27);
        // 3D Conical tower roofs + main royal blue/gold pitched roof
        Theme._roof3D(ctx, x, y + 15, x + 10, y - 1, x + 20,
                      "#3b6ebf", "#1d3d70", "#ffd54a");
        Theme._roof3D(ctx, x + w - 20, y + 15, x + w - 10, y - 1, x + w,
                      "#3362ad", "#17325c", "#ffd54a");
        Theme._roof3D(ctx, x + 10, y + 20, cx, y - 6, x + w - 10,
                      "#386ec2", "#1c3b6e", "#ffd54a");
        // Recessed arched oak double-gate + iron bands + gold crest
        ctx.fillStyle = "#24160b";
        ctx.beginPath();
        ctx.arc(cx, y + h - 14, 9.5, Math.PI, 0);
        ctx.lineTo(cx + 9.5, y + h - 4); ctx.lineTo(cx - 9.5, y + h - 4);
        ctx.closePath(); ctx.fill();
        ctx.fillStyle = "#4f3319";
        ctx.beginPath();
        ctx.arc(cx, y + h - 14, 7.5, Math.PI, 0);
        ctx.lineTo(cx + 7.5, y + h - 4); ctx.lineTo(cx - 7.5, y + h - 4);
        ctx.closePath(); ctx.fill();
        ctx.strokeStyle = "#ffd54a"; ctx.lineWidth = 1.4; ctx.stroke();
      } else if (bid === "barracks") {
        // 3D Human Barracks: axonometric stone walls + battlements + portcullis
        ctx.fillStyle = "#8a9099";
        ctx.fillRect(x + 5, y + 16, (w - 10) * 0.68, h - 25);
        ctx.fillStyle = "#565b63";
        ctx.fillRect(x + 5 + (w - 10) * 0.68, y + 16,
                     (w - 10) * 0.32, h - 25);
        for (var bx = 0; bx < 4; bx++) {
          ctx.fillStyle = bx < 2 ? "#9aa0aa" : "#646972";
          ctx.fillRect(x + 5 + bx * 16, y + 10, 10, 6);
        }
        Theme._roof3D(ctx, x + 2, y + 18, cx, y + 1, x + w - 2,
                      "#a8382f", "#661e18", "#d4a72c");
        // Portcullis sally port + iron grille
        ctx.fillStyle = "#1c140d";
        ctx.fillRect(cx - 8, y + h - 22, 16, 18);
        ctx.strokeStyle = "#7d8590"; ctx.lineWidth = 1;
        for (var pg = -5; pg <= 5; pg += 5) {
          ctx.beginPath();
          ctx.moveTo(cx + pg, y + h - 22); ctx.lineTo(cx + pg, y + h - 4);
          ctx.stroke();
        }
        // Crossed golden halberds
        ctx.strokeStyle = "#ffd54a"; ctx.lineWidth = 2;
        ctx.beginPath();
        ctx.moveTo(cx - 12, y + 27); ctx.lineTo(cx + 12, y + 13);
        ctx.moveTo(cx + 12, y + 27); ctx.lineTo(cx - 12, y + 13);
        ctx.stroke();
      } else if (bid === "tavern") {
        // 3D Half-timbered Inn + stone chimney + 3D oak barrels
        ctx.fillStyle = "#dec79e";
        ctx.fillRect(x + 6, y + 18, (w - 12) * 0.66, h - 27);
        ctx.fillStyle = "#a38d68";
        ctx.fillRect(x + 6 + (w - 12) * 0.66, y + 18,
                     (w - 12) * 0.34, h - 27);
        ctx.strokeStyle = "#4a2f16"; ctx.lineWidth = 2;
        ctx.strokeRect(x + 6, y + 18, w - 12, h - 27);
        // 3D Stone chimney
        ctx.fillStyle = Theme._cylGrad(ctx, x + w - 18, 9,
                                       "#8a7968", "#5c4d3e", "#362c23", "#5c4d3e");
        ctx.fillRect(x + w - 18, y + 1, 9, 18);
        Theme._roof3D(ctx, x + 2, y + 20, cx, y + 1, x + w - 2,
                      "#9e6832", "#593818", "#d4a72c");
        // Warm glowing paned windows + 3D oak barrel
        ctx.fillStyle = "#ffdf78";
        ctx.fillRect(x + 12, y + 24, 10, 8);
        ctx.fillRect(x + w - 24, y + 24, 10, 8);
        ctx.fillStyle = Theme._sphereGrad(ctx, x + 13, y + h - 9, 6,
                                          "#a67038", "#6e4720", "#38220d");
        ctx.beginPath(); ctx.arc(x + 13, y + h - 9, 6, 0, 7); ctx.fill();
      } else if (bid === "library") {
        // 3D Arcane Sanctum: cylindrical marble tower + specular azure dome
        ctx.fillStyle = Theme._cylGrad(ctx, x + 9, w - 18,
                                       "#8d9bb5", "#5e6a82", "#353d4d", "#525d73");
        ctx.fillRect(x + 9, y + 17, w - 18, h - 26);
        ctx.fillStyle = Theme._sphereGrad(ctx, cx, y + 16, (w - 14) / 2,
                                          "#5ec2f7", "#235c78", "#0f2c3d");
        ctx.beginPath();
        ctx.arc(cx, y + 18, (w - 14) / 2, Math.PI, 0);
        ctx.closePath(); ctx.fill();
        ctx.strokeStyle = "#ffd54a"; ctx.lineWidth = 1.6; ctx.stroke();
        // Glowing stained-glass lancet windows
        ctx.fillStyle = "#7dd3fc";
        ctx.fillRect(cx - 3.5, y + 22, 7, 16);
        ctx.fillRect(x + 14, y + 24, 4.5, 13);
        ctx.fillRect(x + w - 18.5, y + 24, 4.5, 13);
      } else if (bid === "watchtower") {
        // 3D Cylindrical Guard/Cannon Tower + machicolations + spire
        ctx.fillStyle = Theme._cylGrad(ctx, cx - 14, 28,
                                       "#a3ab9c", "#6c7366", "#393d35", "#5a6155");
        ctx.beginPath();
        ctx.moveTo(cx - 14, y + h - 8); ctx.lineTo(cx - 10, y + 11);
        ctx.lineTo(cx + 10, y + 11); ctx.lineTo(cx + 14, y + h - 8);
        ctx.closePath(); ctx.fill();
        ctx.fillStyle = "#4d3822";
        ctx.fillRect(cx - 15, y + 9, 30, 5);
        Theme._roof3D(ctx, cx - 16, y + 10, cx, y - 7, cx + 16,
                      "#486999", "#21334d", "#ffd54a");
      } else if (bid === "runeforge") {
        // 3D Blacksmith Foundry: dark stone + volumetric furnace glow + steel anvil
        ctx.fillStyle = Theme._cylGrad(ctx, x + 5, w - 10,
                                       "#6e6763", "#4a4542", "#292523", "#423d3a");
        ctx.fillRect(x + 5, y + 18, w - 10, h - 27);
        ctx.fillStyle = Theme._cylGrad(ctx, x + 9, 11,
                                       "#594842", "#382d29", "#1f1816", "#382d29");
        ctx.fillRect(x + 9, y + 1, 11, 19);
        Theme._roof3D(ctx, x + 3, y + 20, cx, y + 5, x + w - 3,
                      "#803d28", "#421d12", "#c99a49");
        // Volumetric furnace hearth glow
        var fg = ctx.createRadialGradient(
          cx - 4, y + h - 12, 1, cx - 4, y + h - 12, 11);
        fg.addColorStop(0, "#fff7cc");
        fg.addColorStop(0.45, "#ff9900");
        fg.addColorStop(1, "rgba(255,50,0,0)");
        ctx.fillStyle = fg;
        ctx.beginPath();
        ctx.arc(cx - 4, y + h - 12, 11, Math.PI, 0); ctx.fill();
        // 3D Steel Anvil
        ctx.fillStyle = Theme._cylGrad(ctx, x + w - 20, 12,
                                       "#d0d7de", "#8b949e", "#484f58", "#8b949e");
        ctx.fillRect(x + w - 20, y + h - 16, 12, 6);
      } else if (bid === "portal") {
        // 3D Dark Portal: carved runic obelisks + multi-ring dimensional vortex
        ctx.fillStyle = Theme._cylGrad(ctx, x + 7, 11,
                                       "#7a6599", "#463859", "#241b30", "#5a4873");
        ctx.fillRect(x + 7, y + 7, 11, h - 14);
        ctx.fillStyle = Theme._cylGrad(ctx, x + w - 18, 11,
                                       "#6c5887", "#3d304f", "#1e1629", "#4e3e63");
        ctx.fillRect(x + w - 18, y + 7, 11, h - 14);
        ctx.fillRect(x + 4, y + 3, w - 8, 8);
        var pg2 = ctx.createRadialGradient(cx, cy + 2, 2, cx, cy + 2, 18);
        pg2.addColorStop(0, "#ffffff");
        pg2.addColorStop(0.35, "#e879f9");
        pg2.addColorStop(0.75, "#6d28d9");
        pg2.addColorStop(1, "rgba(30,27,75,0)");
        ctx.fillStyle = pg2;
        ctx.beginPath();
        ctx.ellipse(cx, cy + 2, 15, 20, 0, 0, 7); ctx.fill();
      } else if (bid === "marketplace") {
        // 3D Market Pavilion with shaded cloth awnings + gold crates
        ctx.fillStyle = "#7a5734";
        ctx.fillRect(x + 5, y + 22, w - 10, h - 31);
        for (var st = 0; st < 6; st++) {
          ctx.fillStyle = (st % 2 === 0) ? "#cf3636" : "#f5ebd6";
          ctx.fillRect(x + 3 + st * 11, y + 9, 11, 14);
          ctx.fillStyle = "rgba(0,0,0,0.22)";
          ctx.fillRect(x + 3 + st * 11, y + 19, 11, 4);
        }
        ctx.fillStyle = "#d4a72c";
        ctx.fillRect(x + 9, y + h - 15, 11, 9);
        ctx.fillRect(x + w - 22, y + h - 15, 11, 9);
      } else if (bid === "altar") {
        // 3D Stepped Marble Altar of Kings + golden winged statue
        ctx.fillStyle = Theme._cylGrad(ctx, x + 5, w - 10,
                                       "#b8b2c4", "#7a7585", "#494552", "#6c6778");
        ctx.fillRect(x + 5, y + h - 19, w - 10, 12);
        ctx.fillRect(x + 11, y + h - 26, w - 22, 8);
        ctx.fillStyle = Theme._sphereGrad(ctx, cx, y + 16, 14,
                                          "#fff3b0", "#d4a72c", "#7a5c0c");
        ctx.beginPath();
        ctx.arc(cx, y + 15, 6.5, 0, 7);
        ctx.moveTo(cx - 16, y + 12); ctx.lineTo(cx, y + 23);
        ctx.lineTo(cx + 16, y + 12);
        ctx.fill();
        ctx.fillRect(cx - 4.5, y + 20, 9, 16);
      } else {
        // 3D Vault & Trophy Hall: Cylindrical marble columns + golden pediment
        ctx.fillStyle = "#5c6169";
        ctx.fillRect(x + 7, y + 18, w - 14, h - 27);
        for (var col = 0; col < 4; col++) {
          var colX = x + 9 + col * 15;
          ctx.fillStyle = Theme._cylGrad(ctx, colX, 6,
                                         "#e6ebf2", "#9ca3af", "#4b5563", "#9ca3af");
          ctx.fillRect(colX, y + 18, 6, h - 27);
        }
        Theme._roof3D(ctx, x + 3, y + 18, cx, y + 2, x + w - 3,
                      "#c49a33", "#735816", "#ffe07d");
      }
      // Corner heraldic crest badge with structure glyph for instant ID
      ctx.fillStyle = "rgba(12,18,14,0.92)";
      ctx.beginPath();
      ctx.arc(x + w - 11, y + h - 11, 10, 0, 7);
      ctx.fill();
      ctx.strokeStyle = "#ffd54a"; ctx.lineWidth = 1.6; ctx.stroke();
      if (entry.glyph) {
        ctx.fillStyle = entry.fg || "#fff";
        ctx.font = "bold 11px monospace";
        ctx.textAlign = "center"; ctx.textBaseline = "middle";
        ctx.fillText(entry.glyph, x + w - 11, y + h - 11);
      }
    },

    _paintUnit: function (ctx, entry, x, y, w, h) {
      var cx = x + w / 2, cy = y + h / 2, r = Math.min(w, h) / 2;
      var arch = entry.arch || "martial";
      // 1. Deep AO ground contact shadow
      var uao = ctx.createRadialGradient(
        cx, y + h - 4, r * 0.1, cx, y + h - 4, r * 0.78);
      uao.addColorStop(0, "rgba(0,0,0,0.55)");
      uao.addColorStop(1, "rgba(0,0,0,0)");
      ctx.fillStyle = uao;
      ctx.beginPath();
      ctx.ellipse(cx, y + h - 4, r * 0.76, r * 0.34, 0, 0, 7);
      ctx.fill();

      // 2. 3D-Shaded Torso Cuirass & Exaggerated WC3 Pauldrons (Shoulders)
      ctx.fillStyle = entry.dark || "#222";
      ctx.beginPath();
      ctx.ellipse(cx, cy + 6, r * 0.66, r * 0.56, 0, 0, 7);
      ctx.fill();
      // Left & right spherical-shaded pauldrons with metallic rim
      ctx.fillStyle = Theme._sphereGrad(
        ctx, cx - r * 0.56, cy + 1, r * 0.38,
        entry.trim || "#ffd54a", entry.bg || "#444", entry.dark || "#111");
      ctx.beginPath();
      ctx.ellipse(cx - r * 0.56, cy + 2, r * 0.36, r * 0.30, -0.3, 0, 7);
      ctx.fill();
      ctx.strokeStyle = entry.trim || "#ffd54a";
      ctx.lineWidth = 1.6;
      ctx.stroke();

      ctx.fillStyle = Theme._sphereGrad(
        ctx, cx + r * 0.56, cy + 1, r * 0.38,
        entry.trim || "#ffd54a", entry.bg || "#444", entry.dark || "#111");
      ctx.beginPath();
      ctx.ellipse(cx + r * 0.56, cy + 2, r * 0.36, r * 0.30, 0.3, 0, 7);
      ctx.fill();
      ctx.stroke();

      // 3D Cylindrical/Spherical Breastplate + Belt
      ctx.fillStyle = Theme._sphereGrad(
        ctx, cx, cy + 3, r * 0.52,
        entry.trim || "#fff", entry.bg || "#444", entry.dark || "#111");
      ctx.beginPath();
      ctx.arc(cx, cy + 4, r * 0.49, 0, 7);
      ctx.fill();
      // Golden belt buckle
      ctx.fillStyle = "#d4a72c";
      ctx.fillRect(cx - r * 0.32, cy + r * 0.34, r * 0.64, 3);

      // 3. 3D-Lit Head, Visor & Class Headgear / Weapons
      ctx.fillStyle = Theme._sphereGrad(
        ctx, cx, cy - r * 0.24, r * 0.32, "#ffe4bd", "#e8be8a", "#9c6f3e");
      ctx.beginPath();
      ctx.arc(cx, cy - r * 0.22, r * 0.31, 0, 7);
      ctx.fill();
      // Glowing RTS eyes
      ctx.fillStyle = arch === "caster" ? "#7dd3fc" : "#fff";
      ctx.fillRect(cx - r * 0.14, cy - r * 0.26, 2.5, 2);
      ctx.fillRect(cx + r * 0.06, cy - r * 0.26, 2.5, 2);

      if (arch === "commander" || arch === "martial") {
        // 3D Greathelm crest + curved heraldic kite shield + specular broadsword
        ctx.fillStyle = Theme._cylGrad(
          ctx, cx - r * 0.32, r * 0.64,
          "#fff3b0", entry.trim || "#ffd54a", "#8a6508", "#ffd54a");
        ctx.beginPath();
        ctx.moveTo(cx - r * 0.34, cy - r * 0.28);
        ctx.lineTo(cx, cy - r * 0.82);
        ctx.lineTo(cx + r * 0.34, cy - r * 0.28);
        ctx.closePath(); ctx.fill();
        // Kite Shield with golden cross
        ctx.fillStyle = Theme._cylGrad(
          ctx, cx - r * 0.88, r * 0.44,
          entry.trim || "#fff", entry.bg, entry.dark, entry.bg);
        ctx.beginPath();
        ctx.moveTo(cx - r * 0.88, cy - 3);
        ctx.lineTo(cx - r * 0.44, cy - 3);
        ctx.lineTo(cx - r * 0.44, cy + r * 0.46);
        ctx.lineTo(cx - r * 0.66, cy + r * 0.76);
        ctx.lineTo(cx - r * 0.88, cy + r * 0.46);
        ctx.closePath(); ctx.fill();
        ctx.strokeStyle = "#ffd54a"; ctx.lineWidth = 1.5; ctx.stroke();
        // Broadsword with crossguard & fuller highlight
        ctx.strokeStyle = "#f0f6fc"; ctx.lineWidth = 3.2;
        ctx.beginPath();
        ctx.moveTo(cx + r * 0.66, cy + r * 0.32);
        ctx.lineTo(cx + r * 0.90, cy - r * 0.70);
        ctx.stroke();
        ctx.strokeStyle = "#ffd54a"; ctx.lineWidth = 2;
        ctx.beginPath();
        ctx.moveTo(cx + r * 0.54, cy + r * 0.12);
        ctx.lineTo(cx + r * 0.82, cy + r * 0.22);
        ctx.stroke();
      } else if (arch === "caster") {
        // Pointed wizard hat / arcane hood + glowing crystal staff
        ctx.fillStyle = Theme._cylGrad(
          ctx, cx - r * 0.44, r * 0.88,
          entry.bg, entry.dark || "#2a1f3d", "#120b1d", entry.trim);
        ctx.beginPath();
        ctx.moveTo(cx - r * 0.44, cy - r * 0.22);
        ctx.lineTo(cx, cy - r * 0.88);
        ctx.lineTo(cx + r * 0.44, cy - r * 0.22);
        ctx.closePath(); ctx.fill();
        ctx.strokeStyle = "#a855f7"; ctx.lineWidth = 2.5;
        ctx.beginPath();
        ctx.moveTo(cx + r * 0.74, cy + r * 0.68);
        ctx.lineTo(cx + r * 0.74, cy - r * 0.65);
        ctx.stroke();
        ctx.fillStyle = Theme._sphereGrad(
          ctx, cx + r * 0.74, cy - r * 0.72, r * 0.22,
          "#ffffff", "#38bdf8", "#1d4ed8");
        ctx.beginPath();
        ctx.arc(cx + r * 0.74, cy - r * 0.72, r * 0.22, 0, 7);
        ctx.fill();
      } else if (arch === "ranger") {
        // 3D Forest hood + recurve bow + taut bowstring
        ctx.fillStyle = entry.dark || "#1b4332";
        ctx.beginPath();
        ctx.arc(cx, cy - r * 0.28, r * 0.36, Math.PI, 0);
        ctx.fill();
        ctx.strokeStyle = "#d97706"; ctx.lineWidth = 2.6;
        ctx.beginPath();
        ctx.arc(cx + r * 0.56, cy, r * 0.54, -1.15, 1.15);
        ctx.stroke();
        ctx.strokeStyle = "#e2e8f0"; ctx.lineWidth = 1;
        ctx.beginPath();
        ctx.moveTo(cx + r * 0.56 + Math.cos(-1.15) * r * 0.54,
                   cy + Math.sin(-1.15) * r * 0.54);
        ctx.lineTo(cx + r * 0.56 + Math.cos(1.15) * r * 0.54,
                   cy + Math.sin(1.15) * r * 0.54);
        ctx.stroke();
      } else {
        // Dwarven Warhammer / Pickaxe / Twin Daggers
        ctx.strokeStyle = "#cbd5e1"; ctx.lineWidth = 2.6;
        ctx.beginPath();
        ctx.moveTo(cx + r * 0.64, cy + r * 0.42);
        ctx.lineTo(cx + r * 0.78, cy - r * 0.52);
        ctx.stroke();
        ctx.fillStyle = "#94a3b8";
        ctx.fillRect(cx + r * 0.64, cy - r * 0.58, r * 0.28, r * 0.18);
      }
      // Subtle class initial on breastplate
      if (entry.glyph) {
        ctx.fillStyle = entry.fg || "#fff";
        ctx.font = "bold " + Math.round(r * 0.58) + "px monospace";
        ctx.textAlign = "center"; ctx.textBaseline = "middle";
        ctx.fillText(entry.glyph, cx, cy + 5);
      }
    },

    /* #159 animated 3D-style portrait renderer for the bottom console */
    drawPortrait: function (ctx, item, w, h, now) {
      ctx.clearRect(0, 0, w, h);
      var grad = ctx.createRadialGradient(w / 2, h / 2, 4, w / 2, h / 2, w * 0.7);
      grad.addColorStop(0, "#243428");
      grad.addColorStop(1, "#0b110d");
      ctx.fillStyle = grad;
      ctx.fillRect(0, 0, w, h);
      var bob = Math.sin((now || 0) / 380) * 2.2;
      var talk = Math.abs(Math.sin((now || 0) / 150)) * 2.5;
      if (item && item.bid) {
        var be = current.buildings[item.bid] || current.buildings["town-hall"];
        Theme._paintBuilding(ctx, be, 8, 8 + bob * 0.5, w - 16, h - 16);
      } else if (item) {
        var ue = current.units[item.cls] || current.units.Knight;
        // Aura backdrop
        ctx.strokeStyle = ue.trim || "#ffd54a";
        ctx.globalAlpha = 0.35;
        ctx.beginPath();
        ctx.arc(w / 2, h / 2, w * 0.38 + bob, 0, 7);
        ctx.stroke();
        ctx.globalAlpha = 1;
        Theme._paintUnit(ctx, ue, 6, 6 + bob, w - 12, h - 12);
        // Animated glowing eyes + talking visor movement
        ctx.fillStyle = "#58a6ff";
        ctx.fillRect(w / 2 - 5, h * 0.36 + bob, 3, 2);
        ctx.fillRect(w / 2 + 2, h * 0.36 + bob, 3, 2);
        if (item.status_live === "running" || item.bark) {
          ctx.fillStyle = "#ffd54a";
          ctx.fillRect(w / 2 - 3, h * 0.43 + bob, 6, 1 + talk * 0.6);
        }
      }
      ctx.strokeStyle = "#c9a227";
      ctx.lineWidth = 2;
      ctx.strokeRect(1, 1, w - 2, h - 2);
    }
  };
})(window);
