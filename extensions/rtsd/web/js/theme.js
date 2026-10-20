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
    // procedural painter: draws WC3/AoE3 architectural buildings & heroic
    // unit silhouettes into ctx at the given box (#158)
    _paint: function (ctx, entry, x, y, w, h) {
      if (entry.shape === "keep") {
        Theme._paintBuilding(ctx, entry, x, y, w, h);
      } else {
        Theme._paintUnit(ctx, entry, x, y, w, h);
      }
    },

    _paintBuilding: function (ctx, entry, x, y, w, h) {
      var cx = x + w / 2, cy = y + h / 2, bid = entry.bid || "vault";
      // Ground shadow + stone foundation plinth
      ctx.fillStyle = "rgba(0,0,0,0.42)";
      ctx.beginPath();
      ctx.ellipse(cx + 2, y + h - 2, w * 0.48, h * 0.22, 0, 0, 7);
      ctx.fill();
      ctx.fillStyle = "#595449";
      ctx.fillRect(x + 2, y + h - 12, w - 4, 10);
      ctx.strokeStyle = "#2b2822";
      ctx.lineWidth = 1.5;
      ctx.strokeRect(x + 2, y + h - 12, w - 4, 10);

      if (bid === "town-hall") {
        // Keep / Town Center: twin crenellated side towers + central hall + blue/gold roof
        ctx.fillStyle = "#6e737b";
        ctx.fillRect(x + 3, y + 14, 14, h - 22);
        ctx.fillRect(x + w - 17, y + 14, 14, h - 22);
        ctx.fillStyle = "#858a94";
        ctx.fillRect(x + 12, y + 18, w - 24, h - 26);
        // Timber framing
        ctx.strokeStyle = "#4a3520";
        ctx.strokeRect(x + 12, y + 18, w - 24, h - 26);
        // Conical tower roofs + main pitched royal roof
        ctx.fillStyle = entry.roof || "#254e8a";
        ctx.beginPath();
        ctx.moveTo(x + 1, y + 15); ctx.lineTo(x + 10, y + 2);
        ctx.lineTo(x + 19, y + 15);
        ctx.moveTo(x + w - 19, y + 15); ctx.lineTo(x + w - 10, y + 2);
        ctx.lineTo(x + w - 1, y + 15);
        ctx.moveTo(x + 9, y + 20); ctx.lineTo(cx, y - 4);
        ctx.lineTo(x + w - 9, y + 20);
        ctx.closePath(); ctx.fill();
        ctx.strokeStyle = "#d4a72c"; ctx.stroke();
        // Arched oak gate
        ctx.fillStyle = "#3d2714";
        ctx.beginPath();
        ctx.arc(cx, y + h - 14, 8, Math.PI, 0);
        ctx.lineTo(cx + 8, y + h - 4); ctx.lineTo(cx - 8, y + h - 4);
        ctx.closePath(); ctx.fill();
      } else if (bid === "barracks") {
        // Human Barracks: fortified garrison, red roof, battlements, weapon rack
        ctx.fillStyle = "#686c73";
        ctx.fillRect(x + 5, y + 16, w - 10, h - 24);
        for (var bx = 0; bx < 4; bx++) {
          ctx.fillRect(x + 5 + bx * 14, y + 10, 8, 6);
        }
        ctx.fillStyle = entry.roof || "#7d2922";
        ctx.beginPath();
        ctx.moveTo(x + 3, y + 18); ctx.lineTo(cx, y + 3);
        ctx.lineTo(x + w - 3, y + 18); ctx.closePath(); ctx.fill();
        ctx.fillStyle = "#2b1d12";
        ctx.fillRect(cx - 7, y + h - 20, 14, 16);
        // Crossed spears on facade
        ctx.strokeStyle = "#d4a72c"; ctx.lineWidth = 2;
        ctx.beginPath();
        ctx.moveTo(cx - 10, y + 26); ctx.lineTo(cx + 10, y + 14);
        ctx.moveTo(cx + 10, y + 26); ctx.lineTo(cx - 10, y + 14);
        ctx.stroke();
      } else if (bid === "tavern") {
        // Half-timbered Inn + chimney + ale barrels
        ctx.fillStyle = "#c9b38c";
        ctx.fillRect(x + 7, y + 18, w - 14, h - 26);
        ctx.strokeStyle = "#4d3319"; ctx.lineWidth = 2;
        ctx.strokeRect(x + 7, y + 18, w - 14, h - 26);
        // Chimney
        ctx.fillStyle = "#5c4938";
        ctx.fillRect(x + w - 16, y + 2, 7, 16);
        // Warm gable roof
        ctx.fillStyle = entry.roof || "#7c5127";
        ctx.beginPath();
        ctx.moveTo(x + 3, y + 20); ctx.lineTo(cx, y + 2);
        ctx.lineTo(x + w - 3, y + 20); ctx.closePath(); ctx.fill();
        // Glowing tavern windows + ale barrel
        ctx.fillStyle = "#ffcf5c";
        ctx.fillRect(x + 13, y + 24, 8, 7);
        ctx.fillRect(x + w - 21, y + 24, 8, 7);
        ctx.fillStyle = "#6e4720";
        ctx.beginPath(); ctx.arc(x + 12, y + h - 8, 5, 0, 7); ctx.fill();
      } else if (bid === "library") {
        // Arcane Sanctum: octagonal tower + azure dome + glowing lancet windows
        ctx.fillStyle = "#5e6a82";
        ctx.fillRect(x + 10, y + 16, w - 20, h - 24);
        ctx.fillStyle = entry.roof || "#235c78";
        ctx.beginPath();
        ctx.arc(cx, y + 18, (w - 16) / 2, Math.PI, 0);
        ctx.closePath(); ctx.fill();
        ctx.strokeStyle = "#ffd54a"; ctx.lineWidth = 1.5; ctx.stroke();
        ctx.fillStyle = "#58a6ff";
        ctx.fillRect(cx - 3, y + 22, 6, 14);
        ctx.fillRect(x + 15, y + 24, 4, 11);
        ctx.fillRect(x + w - 19, y + 24, 4, 11);
      } else if (bid === "watchtower") {
        // Guard/Cannon Tower: tall tapered stone spire + machicolations
        ctx.fillStyle = "#6c7366";
        ctx.beginPath();
        ctx.moveTo(cx - 12, y + h - 8); ctx.lineTo(cx - 9, y + 12);
        ctx.lineTo(cx + 9, y + 12); ctx.lineTo(cx + 12, y + h - 8);
        ctx.closePath(); ctx.fill();
        ctx.fillStyle = "#4d3822";
        ctx.fillRect(cx - 13, y + 10, 26, 5);
        ctx.fillStyle = entry.roof || "#32496b";
        ctx.beginPath();
        ctx.moveTo(cx - 14, y + 10); ctx.lineTo(cx, y - 6);
        ctx.lineTo(cx + 14, y + 10); ctx.closePath(); ctx.fill();
      } else if (bid === "runeforge") {
        // Blacksmith Foundry: stone hall + glowing furnace hearth + anvil
        ctx.fillStyle = "#4a4542";
        ctx.fillRect(x + 6, y + 18, w - 12, h - 26);
        ctx.fillStyle = "#332926";
        ctx.fillRect(x + 10, y + 2, 9, 18); // forge chimney
        ctx.fillStyle = entry.roof || "#5c2c1d";
        ctx.beginPath();
        ctx.moveTo(x + 4, y + 20); ctx.lineTo(cx, y + 6);
        ctx.lineTo(x + w - 4, y + 20); ctx.closePath(); ctx.fill();
        // Glowing orange furnace mouth
        ctx.fillStyle = "#ff6a00";
        ctx.beginPath();
        ctx.arc(cx - 4, y + h - 12, 8, Math.PI, 0); ctx.fill();
        ctx.fillStyle = "#ffd54a";
        ctx.beginPath();
        ctx.arc(cx - 4, y + h - 12, 4.5, Math.PI, 0); ctx.fill();
        // Anvil on right
        ctx.fillStyle = "#8b949e";
        ctx.fillRect(x + w - 18, y + h - 15, 10, 5);
      } else if (bid === "portal") {
        // Dark Portal / Waygate: twin runic obelisks + swirling void vortex
        ctx.fillStyle = "#463859";
        ctx.fillRect(x + 8, y + 8, 9, h - 14);
        ctx.fillRect(x + w - 17, y + 8, 9, h - 14);
        ctx.fillRect(x + 5, y + 4, w - 10, 7);
        ctx.fillStyle = "#7c3aed";
        ctx.beginPath();
        ctx.ellipse(cx, cy + 2, 13, 18, 0, 0, 7); ctx.fill();
        ctx.fillStyle = "#c084fc";
        ctx.beginPath();
        ctx.ellipse(cx, cy + 2, 7, 11, 0, 0, 7); ctx.fill();
      } else if (bid === "marketplace") {
        // Trading Post / Market stalls with striped awnings
        ctx.fillStyle = "#6e4e2e";
        ctx.fillRect(x + 6, y + 22, w - 12, h - 30);
        for (var st = 0; st < 6; st++) {
          ctx.fillStyle = (st % 2 === 0) ? "#b82c2c" : "#f0e6d2";
          ctx.fillRect(x + 4 + st * 9, y + 10, 9, 13);
        }
        ctx.fillStyle = "#c99a49";
        ctx.fillRect(x + 10, y + h - 14, 10, 8);
        ctx.fillRect(x + w - 22, y + h - 14, 10, 8);
      } else if (bid === "altar") {
        // Altar of Kings: stepped marble dais + winged golden statue + braziers
        ctx.fillStyle = "#7a7585";
        ctx.fillRect(x + 6, y + h - 18, w - 12, 12);
        ctx.fillRect(x + 12, y + h - 24, w - 24, 8);
        ctx.fillStyle = "#d4a72c";
        ctx.beginPath();
        ctx.arc(cx, y + 16, 6, 0, 7);
        ctx.moveTo(cx - 14, y + 14); ctx.lineTo(cx, y + 22);
        ctx.lineTo(cx + 14, y + 14);
        ctx.fill();
        ctx.fillRect(cx - 4, y + 20, 8, 16);
      } else {
        // Vault & Trophy Hall: Classical colonnade + golden pediment
        ctx.fillStyle = "#757a82";
        ctx.fillRect(x + 8, y + 18, w - 16, h - 26);
        ctx.fillStyle = "#aeb4bd";
        for (var col = 0; col < 4; col++) {
          ctx.fillRect(x + 10 + col * 13, y + 18, 4, h - 26);
        }
        ctx.fillStyle = entry.roof || "#967424";
        ctx.beginPath();
        ctx.moveTo(x + 4, y + 18); ctx.lineTo(cx, y + 3);
        ctx.lineTo(x + w - 4, y + 18); ctx.closePath(); ctx.fill();
      }
      // Corner heraldic crest badge with structure glyph for instant ID
      ctx.fillStyle = "rgba(15,20,25,0.88)";
      ctx.beginPath();
      ctx.arc(x + w - 10, y + h - 10, 9, 0, 7);
      ctx.fill();
      ctx.strokeStyle = "#ffd54a"; ctx.lineWidth = 1.5; ctx.stroke();
      if (entry.glyph) {
        ctx.fillStyle = entry.fg || "#fff";
        ctx.font = "bold 11px monospace";
        ctx.textAlign = "center"; ctx.textBaseline = "middle";
        ctx.fillText(entry.glyph, x + w - 10, y + h - 10);
      }
    },

    _paintUnit: function (ctx, entry, x, y, w, h) {
      var cx = x + w / 2, cy = y + h / 2, r = Math.min(w, h) / 2;
      var arch = entry.arch || "martial";
      // Ground shadow
      ctx.fillStyle = "rgba(0,0,0,0.38)";
      ctx.beginPath();
      ctx.ellipse(cx, y + h - 4, r * 0.72, r * 0.32, 0, 0, 7);
      ctx.fill();

      // Torso & Exaggerated WC3 Pauldrons (Shoulders)
      ctx.fillStyle = entry.dark || "#222";
      ctx.beginPath();
      ctx.ellipse(cx, cy + 5, r * 0.65, r * 0.55, 0, 0, 7);
      ctx.fill();
      ctx.fillStyle = entry.bg || "#444";
      // Left & right big pauldrons
      ctx.beginPath();
      ctx.ellipse(cx - r * 0.56, cy + 2, r * 0.34, r * 0.28, -0.3, 0, 7);
      ctx.ellipse(cx + r * 0.56, cy + 2, r * 0.34, r * 0.28, 0.3, 0, 7);
      ctx.fill();
      ctx.strokeStyle = entry.trim || "#ffd54a";
      ctx.lineWidth = 1.8;
      ctx.stroke();
      // Chest breastplate / tunic
      ctx.fillStyle = entry.bg || "#444";
      ctx.beginPath();
      ctx.arc(cx, cy + 4, r * 0.48, 0, 7);
      ctx.fill();

      // Head & Class Headgear
      ctx.fillStyle = "#f2cfa0"; // face/visor
      ctx.beginPath();
      ctx.arc(cx, cy - r * 0.22, r * 0.30, 0, 7);
      ctx.fill();
      if (arch === "commander" || arch === "martial") {
        // Greathelm + golden crest/plume + kite shield + broadsword
        ctx.fillStyle = entry.trim || "#ffd54a";
        ctx.beginPath();
        ctx.moveTo(cx - r * 0.32, cy - r * 0.28);
        ctx.lineTo(cx, cy - r * 0.78);
        ctx.lineTo(cx + r * 0.32, cy - r * 0.28);
        ctx.closePath(); ctx.fill();
        // Shield on left arm
        ctx.fillStyle = entry.bg;
        ctx.beginPath();
        ctx.moveTo(cx - r * 0.85, cy - 2);
        ctx.lineTo(cx - r * 0.45, cy - 2);
        ctx.lineTo(cx - r * 0.45, cy + r * 0.45);
        ctx.lineTo(cx - r * 0.65, cy + r * 0.72);
        ctx.lineTo(cx - r * 0.85, cy + r * 0.45);
        ctx.closePath(); ctx.fill();
        ctx.strokeStyle = "#ffd54a"; ctx.stroke();
        // Sword blade on right
        ctx.strokeStyle = "#e6edf3"; ctx.lineWidth = 3;
        ctx.beginPath();
        ctx.moveTo(cx + r * 0.68, cy + r * 0.3);
        ctx.lineTo(cx + r * 0.88, cy - r * 0.65);
        ctx.stroke();
      } else if (arch === "caster") {
        // Pointed wizard hat / arcane hood + glowing crystal staff
        ctx.fillStyle = entry.dark || "#2a1f3d";
        ctx.beginPath();
        ctx.moveTo(cx - r * 0.42, cy - r * 0.22);
        ctx.lineTo(cx, cy - r * 0.85);
        ctx.lineTo(cx + r * 0.42, cy - r * 0.22);
        ctx.closePath(); ctx.fill();
        ctx.strokeStyle = "#8b5cf6"; ctx.lineWidth = 2.5;
        ctx.beginPath();
        ctx.moveTo(cx + r * 0.72, cy + r * 0.65);
        ctx.lineTo(cx + r * 0.72, cy - r * 0.65);
        ctx.stroke();
        ctx.fillStyle = "#38bdf8";
        ctx.beginPath();
        ctx.arc(cx + r * 0.72, cy - r * 0.72, r * 0.18, 0, 7);
        ctx.fill();
      } else if (arch === "ranger") {
        // Forest hood + recurve bow
        ctx.fillStyle = entry.dark || "#1b4332";
        ctx.beginPath();
        ctx.arc(cx, cy - r * 0.28, r * 0.34, Math.PI, 0);
        ctx.fill();
        ctx.strokeStyle = "#d97706"; ctx.lineWidth = 2.5;
        ctx.beginPath();
        ctx.arc(cx + r * 0.55, cy, r * 0.52, -1.1, 1.1);
        ctx.stroke();
      } else {
        // Warhammer / pickaxe / daggers
        ctx.strokeStyle = "#e2e8f0"; ctx.lineWidth = 2.5;
        ctx.beginPath();
        ctx.moveTo(cx + r * 0.65, cy + r * 0.4);
        ctx.lineTo(cx + r * 0.78, cy - r * 0.5);
        ctx.stroke();
      }
      // Subtle class initial on breastplate
      if (entry.glyph) {
        ctx.fillStyle = entry.fg || "#fff";
        ctx.font = "bold " + Math.round(r * 0.62) + "px monospace";
        ctx.textAlign = "center"; ctx.textBaseline = "middle";
        ctx.fillText(entry.glyph, cx, cy + 6);
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
