/* engine.js - rtsd v2 canvas-2D renderer: tilemap, camera, fog, sprites.
   Zero deps, classic script (file:// safe). The engine owns no game state:
   App feeds it {tiles, fog, regions, units, buildings} every frame.
   World coords are pixels; one tile = TILE px at zoom 1. */
(function (g) {
  "use strict";

  var TILE = 32;
  var ZMIN = 0.35, ZMAX = 3.0;

  function hash(s) { // deterministic placement jitter
    var h = 2166136261;
    for (var i = 0; i < s.length; i++) {
      h ^= s.charCodeAt(i); h = Math.imul(h, 16777619);
    }
    return (h >>> 0);
  }

  function Engine(canvas) {
    this.cv = canvas;
    this.ctx = canvas.getContext("2d");
    this.cam = { x: 0, y: 0, zoom: 1 };      // world-px at view top-left
    this.keys = {};                          // held keys for pan
    this.mouse = { x: 0, y: 0, in: false };
    this.map = null;                         // {w,h,tiles,fog,regions,poi}
    this.fps = { n: 0, t: 0, v: 0 };         // measured, shown in HUD
    this.onPick = null;                      // cb(unit|null, worldPt, ev)
    this.onBox = null;                       // cb(rectScreen, ev) (#126)
    this.onDblPick = null;                   // cb(unit|null, worldPt, ev)
    this.box = null;                         // live drag-select rect (screen)
    this._boxUp = false;                     // swallow the click after a box
    this.iso = false;                        // isometric projection (#134)
    this._install();
  }

  Engine.prototype = {

    // ---- camera ----------------------------------------------------
    view: function () {
      return { x: this.cam.x, y: this.cam.y,
        w: this.cv.width / this.cam.zoom,
        h: this.cv.height / this.cam.zoom };
    },
    clampCam: function () {
      if (!this.map) return;
      var mw = this.map.w * TILE, mh = this.map.h * TILE, v = this.view();
      if (this.iso) {          // iso plane spans x:[-mh, mw], y:[0,(mw+mh)/2]
        this.cam.x = Math.max(-mh - 200,
          Math.min(mw - v.w + 200, this.cam.x));
        this.cam.y = Math.max(-200,
          Math.min((mw + mh) / 2 - v.h + 200, this.cam.y));
        return;
      }
      this.cam.x = Math.max(-200, Math.min(mw - v.w + 200, this.cam.x));
      this.cam.y = Math.max(-200, Math.min(mh - v.h + 200, this.cam.y));
    },
    centerOn: function (wx, wy) {   // wx,wy are world px in both themes
      var v = this.view();
      if (this.iso) { var px = wx - wy, py = (wx + wy) / 2;
                      wx = px; wy = py; }
      this.cam.x = wx - v.w / 2; this.cam.y = wy - v.h / 2; this.clampCam();
    },
    panBy: function (dx, dy) {
      this.cam.x += dx; this.cam.y += dy; this.clampCam();
    },
    /* #134: under the office theme every world point is projected
       isometrically (x' = x - y, y' = (x + y)/2) before the camera is
       applied. ALL render and picking paths funnel through these two
       functions so what you see is exactly what you click. */
    toWorld: function (sx, sy) {
      var vx = this.cam.x + sx / this.cam.zoom,
          vy = this.cam.y + sy / this.cam.zoom;
      if (!this.iso) return { x: vx, y: vy };
      return { x: vy + vx / 2, y: vy - vx / 2 };
    },
    toScreen: function (wx, wy) {
      var px = wx, py = wy;
      if (this.iso) { px = wx - wy; py = (wx + wy) / 2; }
      return { x: (px - this.cam.x) * this.cam.zoom,
               y: (py - this.cam.y) * this.cam.zoom };
    },

    // ---- input -----------------------------------------------------
    _install: function () {
      var E = this, cv = this.cv;
      window.addEventListener("keydown", function (e) {
        if (e.target && e.target.tagName === "INPUT") return;
        E.keys[e.key.toLowerCase()] = true;
      });
      window.addEventListener("keyup", function (e) {
        E.keys[e.key.toLowerCase()] = false;
      });
      cv.addEventListener("wheel", function (e) {
        e.preventDefault();
        var p = E.toWorld(e.offsetX, e.offsetY);
        var f = e.deltaY < 0 ? 1.15 : 1 / 1.15;
        E.cam.zoom = Math.max(ZMIN, Math.min(ZMAX, E.cam.zoom * f));
        var px = E.iso ? p.x - p.y : p.x,
            py = E.iso ? (p.x + p.y) / 2 : p.y;
        E.cam.x = px - e.offsetX / E.cam.zoom;
        E.cam.y = py - e.offsetY / E.cam.zoom;
        E.clampCam();
      }, { passive: false });
      cv.addEventListener("mousemove", function (e) {
        E.mouse.x = e.offsetX; E.mouse.y = e.offsetY; E.mouse.in = true;
        if (box0) {                         // left-drag = box select (#126)
          var dx = e.offsetX - box0.x, dy = e.offsetY - box0.y;
          if (E.box || dx * dx + dy * dy > 16)
            E.box = { x0: Math.min(box0.x, e.offsetX),
                      y0: Math.min(box0.y, e.offsetY),
                      x1: Math.max(box0.x, e.offsetX),
                      y1: Math.max(box0.y, e.offsetY) };
        }
      });
      cv.addEventListener("mouseleave", function () { E.mouse.in = false; });
      cv.addEventListener("click", function (e) {
        if (E._boxUp) { E._boxUp = false; return; }
        if (!E.onPick || !E.map) return;
        E.onPick(E.pickUnit(e.offsetX, e.offsetY),
                 E.toWorld(e.offsetX, e.offsetY), e);
      });
      cv.addEventListener("dblclick", function (e) {
        if (!E.onDblPick || !E.map) return;
        E.onDblPick(E.pickUnit(e.offsetX, e.offsetY),
                    E.toWorld(e.offsetX, e.offsetY), e);
      });
      var box0 = null;                       // left-button drag origin
      var drag = null;
      cv.addEventListener("mousedown", function (e) {
        if (e.button === 1 || (e.button === 0 && e.altKey))
          drag = { x: e.clientX, y: e.clientY, cx: E.cam.x, cy: E.cam.y };
        else if (e.button === 0)
          box0 = { x: e.offsetX, y: e.offsetY };
      });
      window.addEventListener("mousemove", function (e) {
        if (!drag) return;
        E.cam.x = drag.cx - (e.clientX - drag.x) / E.cam.zoom;
        E.cam.y = drag.cy - (e.clientY - drag.y) / E.cam.zoom;
        E.clampCam();
      });
      window.addEventListener("mouseup", function (e) {
        drag = null;
        if (E.box) {          // drag ended: emit the rectangle, eat the click
          E._boxUp = true;
          if (E.onBox) E.onBox(E.box, e);
          E.box = null;
        }
        box0 = null;
      });
    },

    // per-frame camera update: WASD/arrows + edge pan
    step: function (dt) {
      var sp = 520 * dt / this.cam.zoom;
      var k = this.keys;
      if (k["w"] || k["arrowup"]) this.panBy(0, -sp);
      if (k["s"] || k["arrowdown"]) this.panBy(0, sp);
      // #136: 'a' is the WC3 attack hotkey now; left-pan = arrow/edge
      if (k["arrowleft"]) this.panBy(-sp, 0);
      if (k["d"] || k["arrowright"]) this.panBy(sp, 0);
      if (this.mouse.in) {
        var m = this.mouse, W = this.cv.width, H = this.cv.height, E = 24;
        if (m.x < E) this.panBy(-sp, 0);
        if (m.x > W - E) this.panBy(sp, 0);
        if (m.y < E) this.panBy(0, -sp);
        if (m.y > H - E) this.panBy(0, sp);
      }
    },

    /* picking happens in screen space (#134): each entity is projected
       through the same toScreen() the renderer used, so the sprite you
       see is the sprite you click - under both projections. */
    pickUnit: function (sx, sy) {
      var self = this, best = null, bd = 14 + 8 * this.cam.zoom;
      (this.units || []).forEach(function (u) {
        var s = self.toScreen(u.x, u.y);
        var d = Math.hypot(s.x - sx, s.y - sy);
        if (d < bd) { bd = d; best = u; }
      });
      return best;
    },

    pickBuilding: function (sx, sy) {
      var self = this, best = null, bd = 26 + 8 * this.cam.zoom;
      (this.buildings || []).forEach(function (b) {
        var s = self.toScreen(b.x, b.y);
        var d = Math.hypot(s.x - sx, s.y - sy);
        if (d < bd) { bd = d; best = b; }
      });
      return best;
    },

    // units whose sprite center falls inside a screen-space rect (#126)
    unitsInBox: function (r) {
      var self = this, out = [];
      (this.units || []).forEach(function (u) {
        var s = self.toScreen(u.x, u.y);
        if (s.x >= r.x0 && s.x <= r.x1 && s.y >= r.y0 && s.y <= r.y1)
          out.push(u);
      });
      return out;
    },

    // units currently inside the viewport (double-click class sweep, #126)
    unitsInView: function () {
      var self = this, W = this.cv.width, H = this.cv.height;
      return (this.units || []).filter(function (u) {
        var s = self.toScreen(u.x, u.y);
        return s.x >= 0 && s.x <= W && s.y >= 0 && s.y <= H;
      });
    },

    /* tile fill shared by both projections: floor color, explored-dim
       veil, and the #133 breach pulse drawn along `path()`. */
    _tileStyle: function (ctx, st, theme, i) {
      var ts = st.tiles, mk = ts.mark ? ts.mark[i] : 0;
      var wt = ts._water ? ts._water[i] : 0;
      var rd = ts._roads ? ts._roads[i] : 0;
      if (mk === 2) return theme.tiles.contested;
      if (wt === 3) return "#7c5836"; // wooden bridge over water
      if (wt === 2) return theme.tiles.waterDeep || theme.tiles.water;
      if (wt === 1) return theme.tiles.water;
      if (mk === 1) return theme.tiles.plot;
      if (rd === 2) return theme.tiles.plaza || theme.tiles.plot;
      if (rd === 1) return theme.tiles.road || theme.tiles.plot;
      return theme.tiles[ts.data[i] % 10] || theme.tiles[0];
    },

    /* #157 wind physics: meteorological wind_deg is the direction wind
       blows FROM, so particles/waves/trees bend toward wind_deg + 180. */
    _windVec: function (st, now) {
      var wx = (st && st.weather) || {};
      var kph = typeof wx.wind_kph === "number" ? wx.wind_kph : 14;
      var gust = typeof wx.wind_gust_kph === "number" ? wx.wind_gust_kph : 22;
      var deg = typeof wx.wind_deg === "number" ? wx.wind_deg : 75;
      var rad = ((deg + 180) % 360) * Math.PI / 180;
      var gWave = 0.5 + 0.5 * Math.sin(now / 950) * Math.cos(now / 1700);
      var eff = kph + (gust - kph) * gWave;
      var str = Math.max(0.25, Math.min(3.2, eff / 16));
      return { vx: Math.cos(rad) * str, vy: Math.sin(rad) * str,
               ux: Math.cos(rad), uy: Math.sin(rad),
               str: str, kph: eff, deg: deg, rad: rad,
               gust: Math.sin(now / 520) };
    },

    /* #157 dynamic Line-of-Sight: in WC3/AoE3 every owned structure and
       unit illuminates the terrain around it. Server fog remains the
       baseexplored memory; active vision lifts nearby tiles to lit (2)
       with an explored skirt (1). */
    _sightFog: function (st) {
      var ts = st.tiles;
      if (!ts) return null;
      var W = ts.w, H = ts.h, n = W * H;
      if (!ts._visFog || ts._visFog.length !== n)
        ts._visFog = new Uint8Array(n);
      var out = ts._visFog, src = st.fog;
      for (var i = 0; i < n; i++) out[i] = src ? src[i] : 2;
      var reveal = function (wx, wy, rLit, rDim) {
        var cx = Math.floor(wx / TILE), cy = Math.floor(wy / TILE);
        var r2 = rLit * rLit, rd2 = rDim * rDim;
        var x0 = Math.max(0, cx - rDim), x1 = Math.min(W - 1, cx + rDim);
        var y0 = Math.max(0, cy - rDim), y1 = Math.min(H - 1, cy + rDim);
        for (var y = y0; y <= y1; y++) {
          for (var x = x0; x <= x1; x++) {
            var d2 = (x - cx) * (x - cx) + (y - cy) * (y - cy);
            var idx = y * W + x;
            if (d2 <= r2) out[idx] = 2;
            else if (d2 <= rd2 && out[idx] < 1) out[idx] = 1;
          }
        }
      };
      (st.buildings || []).forEach(function (b) {
        var r = b.bid === "watchtower" ? 10 : b.bid === "town-hall" ? 7 : 5;
        reveal(b.x, b.y, r, r + 2);
      });
      (st.units || []).forEach(function (u) {
        var r = u.kind === "hero" ? 6 : 4;
        reveal(u.x, u.y, r, r + 2);
      });
      (st.workers || []).forEach(function (wk) {
        if (wk.from && wk.to)
          reveal(wk.to[0] * TILE, wk.to[1] * TILE, 3, 5);
      });
      return out;
    },

    /* #157 deterministic WC3/AoE3 environment synthesis: cobblestone plazas,
       dirt roads between Keep and capitals, winding river + lake water
       channels with wooden bridges, swaying forest trees, meadow grass,
       reeds, boulders, and wandering critters. */
    _ensureEnv: function (ts, st) {
      var sig = (ts.sig || 1) + ":" + (st.buildings ? st.buildings.length : 0);
      if (ts._envSig === sig) return;
      ts._envSig = sig;
      var W = ts.w, H = ts.h, n = W * H;
      var roads = new Uint8Array(n);
      var water = new Uint8Array(n);
      var keep = (ts.caps && ts.caps.root) ||
                 (ts.caps && ts.caps[Object.keys(ts.caps)[0]]) ||
                 { cx: (W / 2) | 0, cy: (H / 2) | 0 };
      var markPlaza = function (cx, cy, rad) {
        for (var dy = -rad; dy <= rad; dy++) {
          for (var dx = -rad; dx <= rad; dx++) {
            var x = cx + dx, y = cy + dy;
            if (x >= 0 && x < W && y >= 0 && y < H &&
                dx * dx + dy * dy <= rad * rad + 1)
              roads[y * W + x] = 2;
          }
        }
      };
      var carveRoad = function (x0, y0, x1, y1) {
        var steps = Math.max(Math.abs(x1 - x0), Math.abs(y1 - y0), 1);
        for (var s = 0; s <= steps; s++) {
          var t = s / steps;
          var bend = Math.sin(t * Math.PI) * 1.4;
          var rx = Math.round(x0 + (x1 - x0) * t + bend),
              ry = Math.round(y0 + (y1 - y0) * t - bend * 0.6);
          if (rx >= 0 && rx < W && ry >= 0 && ry < H) {
            var idx = ry * W + rx;
            if (!roads[idx]) roads[idx] = 1;
          }
        }
      };
      markPlaza(keep.cx, keep.cy, 2);
      if (ts.caps) {
        Object.keys(ts.caps).forEach(function (k) {
          var c = ts.caps[k];
          markPlaza(c.cx, c.cy, 2);
          carveRoad(keep.cx, keep.cy, c.cx, c.cy);
        });
      }
      (st.buildings || []).forEach(function (b) {
        var bx = Math.floor(b.x / TILE), by = Math.floor(b.y / TILE);
        markPlaza(bx, by, 1);
        carveRoad(keep.cx, keep.cy, bx, by);
      });
      // Winding river channel across the valley + natural lake basin,
      // avoiding plazas and plots (road crossings become wooden bridges=3)
      for (var x = 0; x < W; x++) {
        var ry = Math.round(H * 0.48 + Math.sin(x / 6.5) * 5.5 +
                            Math.cos(x / 3.2) * 1.8);
        for (var wy = ry - 1; wy <= ry + 1; wy++) {
          if (wy < 1 || wy >= H - 1) continue;
          var idx = wy * W + x;
          if (roads[idx] === 2 || (ts.mark && ts.mark[idx])) continue;
          if (roads[idx] === 1) water[idx] = 3; // wooden bridge!
          else water[idx] = (wy === ry) ? 2 : 1;
        }
      }
      // Scenic lake in the NW/SE basin if clear of capitals
      var lx = Math.round(W * 0.28), ly = Math.round(H * 0.56);
      for (var dy = -4; dy <= 4; dy++) {
        for (var dx = -5; dx <= 5; dx++) {
          var tx = lx + dx, ty = ly + dy;
          if (tx < 1 || tx >= W - 1 || ty < 1 || ty >= H - 1) continue;
          var d = (dx * dx) / 25 + (dy * dy) / 16;
          if (d > 1) continue;
          var idx2 = ty * W + tx;
          if (roads[idx2] === 2 || (ts.mark && ts.mark[idx2])) continue;
          water[idx2] = roads[idx2] === 1 ? 3 : (d < 0.45 ? 2 : 1);
        }
      }
      ts._roads = roads;
      ts._water = water;
      // Trees & Doodads
      var trees = [], doodads = [], critters = [];
      for (var ty2 = 1; ty2 < H - 1; ty2++) {
        for (var tx2 = 1; tx2 < W - 1; tx2++) {
          var i0 = ty2 * W + tx2;
          if (roads[i0] || water[i0] || (ts.mark && ts.mark[i0])) continue;
          var h = hash("env:" + tx2 + ":" + ty2);
          // Check if adjacent to water -> reeds / willow
          var nearWater = (water[i0 - 1] === 1 || water[i0 + 1] === 1 ||
                           water[i0 - W] === 1 || water[i0 + W] === 1);
          if (nearWater && (h % 5 === 0)) {
            doodads.push({ tx: tx2, ty: ty2,
              x: (tx2 + 0.3 + (h % 40) / 100) * TILE,
              y: (ty2 + 0.3 + ((h >> 6) % 40) / 100) * TILE,
              kind: "reed", seed: h });
            continue;
          }
          // Forest clustering using deterministic wave + hash
          var fval = Math.sin(tx2 * 0.42) * Math.cos(ty2 * 0.38) +
                     ((h % 100) / 100 - 0.5) * 0.8;
          if (fval > 0.36 && (h % 3 !== 0)) {
            trees.push({
              tx: tx2, ty: ty2,
              x: (tx2 + 0.25 + (h % 50) / 100) * TILE,
              y: (ty2 + 0.25 + ((h >> 8) % 50) / 100) * TILE,
              kind: nearWater ? "willow" : (h % 4 === 0 ? "pine" :
                    h % 7 === 0 ? "goldleaf" : "oak"),
              scale: 0.82 + (h % 38) / 100,
              seed: h
            });
          } else if (h % 11 === 0) {
            doodads.push({
              tx: tx2, ty: ty2,
              x: (tx2 + 0.2 + (h % 60) / 100) * TILE,
              y: (ty2 + 0.2 + ((h >> 5) % 60) / 100) * TILE,
              kind: (h % 4 === 0) ? "rock" : (h % 3 === 0) ? "flower" : "grass",
              seed: h
            });
          }
        }
      }
      // Wandering critters (sheep, stag, frog)
      for (var ci = 0; ci < 16; ci++) {
        var ch = hash("critter:" + ci);
        var cx0 = (4 + (ch % (W - 8))) * TILE,
            cy0 = (4 + ((ch >> 7) % (H - 8))) * TILE;
        critters.push({
          ox: cx0, oy: cy0, x: cx0, y: cy0,
          kind: ci % 3 === 0 ? "stag" : ci % 3 === 1 ? "sheep" : "hare",
          seed: ch
        });
      }
      ts._trees = trees;
      ts._doodads = doodads;
      ts._critters = critters;
      ts._tcv = null; // trigger offscreen organic terrain bake (#163)
    },

    /* #163 seamless organic terrain splatting: bakes the entire map floor
       into an offscreen canvas with soft radial biome transitions, sandy
       riverbanks, stone-paved Keep courtyards, and soft-edged dirt roads
       so blocky tile seams disappear completely. */
    _ensureTerrainCanvas: function (ts, theme) {
      var key = (ts._envSig || "") + ":" + (theme && theme.name);
      if (ts._tcv && ts._tcvKey === key) return ts._tcv;
      if (typeof document === "undefined" || !document.createElement)
        return null;
      var c = document.createElement("canvas");
      if (!c || !c.getContext) return null;
      var W = ts.w, H = ts.h;
      c.width = W * TILE; c.height = H * TILE;
      var g2 = c.getContext("2d");
      if (!g2 || !g2.createRadialGradient) return null;
      ts._tcv = c; ts._tcvKey = key;
      // 1. Base meadow fill
      g2.fillStyle = theme.tiles[0] || "#264b25";
      g2.fillRect(0, 0, c.width, c.height);
      // 2. Soft overlapping organic biome splats per tile (no square edges!)
      for (var ty = 0; ty < H; ty++) {
        for (var tx = 0; tx < W; tx++) {
          var i = ty * W + tx;
          var cx = (tx + 0.5) * TILE, cy = (ty + 0.5) * TILE;
          var wt = ts._water ? ts._water[i] : 0;
          var rd = ts._roads ? ts._roads[i] : 0;
          var col = theme.tiles[ts.data[i] % 10] || theme.tiles[0];
          g2.fillStyle = col;
          g2.beginPath();
          g2.arc(cx, cy, TILE * 0.78, 0, 7);
          g2.fill();
          // Elevation / turf micro-variation
          var h = hash("turf:" + tx + ":" + ty);
          if (!wt && !rd && (h % 3 === 0)) {
            g2.fillStyle = (h % 2)
              ? "rgba(68,125,54,0.22)" : "rgba(20,42,20,0.18)";
            g2.beginPath();
            g2.ellipse(cx + (h % 9) - 4, cy + ((h >> 4) % 9) - 4,
                       TILE * 0.52, TILE * 0.38, (h % 6) * 0.5, 0, 7);
            g2.fill();
          }
        }
      }
      // 3. Soft-edged dirt roads & stone-paved Keep courtyards
      for (var ty2 = 0; ty2 < H; ty2++) {
        for (var tx2 = 0; tx2 < W; tx2++) {
          var i2 = ty2 * W + tx2;
          var rd2 = ts._roads ? ts._roads[i2] : 0;
          var wt2 = ts._water ? ts._water[i2] : 0;
          if (!rd2 || wt2) continue;
          var rx = (tx2 + 0.5) * TILE, ry = (ty2 + 0.5) * TILE;
          if (rd2 === 2) {
            // Keep courtyard: warm stone paving + individual cobblestones
            g2.fillStyle = theme.tiles.plaza || "#786954";
            g2.beginPath();
            g2.arc(rx, ry, TILE * 0.72, 0, 7);
            g2.fill();
            g2.fillStyle = "rgba(45,38,30,0.28)";
            for (var py = -10; py <= 10; py += 7) {
              for (var px = -10; px <= 10; px += 8) {
                g2.beginPath();
                g2.ellipse(rx + px + (py % 2) * 2, ry + py,
                           3.2, 2.2, 0, 0, 7);
                g2.fill();
              }
            }
          } else {
            // Dirt road: feathered sandy verge + packed earth center
            var rg = g2.createRadialGradient(rx, ry, 2, rx, ry, TILE * 0.75);
            rg.addColorStop(0, "#7d674a");
            rg.addColorStop(0.65, "#635038");
            rg.addColorStop(1, "rgba(99,80,56,0)");
            g2.fillStyle = rg;
            g2.beginPath();
            g2.arc(rx, ry, TILE * 0.75, 0, 7);
            g2.fill();
          }
        }
      }
      // 4. Sandy/pebble riverbanks + deep/shallow water basins
      for (var ty3 = 0; ty3 < H; ty3++) {
        for (var tx3 = 0; tx3 < W; tx3++) {
          var i3 = ty3 * W + tx3;
          var wt3 = ts._water ? ts._water[i3] : 0;
          if (!wt3) continue;
          var wx = (tx3 + 0.5) * TILE, wy = (ty3 + 0.5) * TILE;
          // Coastal sand shelf
          g2.fillStyle = "rgba(168,148,106,0.45)";
          g2.beginPath();
          g2.arc(wx, wy, TILE * 0.82, 0, 7);
          g2.fill();
          // Water basin
          g2.fillStyle = wt3 === 2
            ? (theme.tiles.waterDeep || "#113450")
            : (theme.tiles.water || "#184668");
          g2.beginPath();
          g2.arc(wx, wy, TILE * 0.68, 0, 7);
          g2.fill();
        }
      }
      return c;
    },

    // battlefield: blits seamless splatted terrain + Gerstner water waves + fog
    _flatTiles: function (ctx, st, theme, z, v, now, wind) {
      var ts = st.tiles, W = ts.w, H = ts.h;
      var fog = st.visFog || st.fog;
      var x0 = Math.max(0, Math.floor(v.x / TILE)),
          y0 = Math.max(0, Math.floor(v.y / TILE)),
          x1 = Math.min(W, Math.ceil((v.x + v.w) / TILE)),
          y1 = Math.min(H, Math.ceil((v.y + v.h) / TILE));
      var px = TILE * z;
      var tcv = this._ensureTerrainCanvas(ts, theme);
      if (tcv) {
        var sx0 = x0 * TILE, sy0 = y0 * TILE,
            sw0 = (x1 - x0) * TILE, sh0 = (y1 - y0) * TILE;
        if (sw0 > 0 && sh0 > 0) {
          ctx.drawImage(tcv, sx0, sy0, sw0, sh0,
                        (sx0 - v.x) * z, (sy0 - v.y) * z,
                        sw0 * z, sh0 * z);
        }
      }
      for (var ty = y0; ty < y1; ty++) {
        for (var tx = x0; tx < x1; tx++) {
          var i = ty * W + tx;
          var f = fog ? fog[i] : 2;
          var sx = (tx * TILE - v.x) * z, sy = (ty * TILE - v.y) * z;
          if (f === 0) {
            ctx.fillStyle = (tx + ty) % 2 ? "#0b140d" : "#09110b";
            ctx.fillRect(sx, sy, px + 1, px + 1);
            continue;
          }
          if (!tcv) {
            ctx.fillStyle = this._tileStyle(ctx, st, theme, i);
            ctx.fillRect(sx, sy, px + 1, px + 1);
          } else if (ts.mark && ts.mark[i] === 2) {
            ctx.fillStyle = "rgba(180,45,45,0.45)";
            ctx.fillRect(sx, sy, px, px);
          }
          var wt = ts._water ? ts._water[i] : 0;
          // Gerstner 2-wave superposition & specular sun glints (#163)
          if ((wt === 1 || wt === 2) && z > 0.45) {
            var wph1 = (now / 360) * wind.str + tx * wind.ux * 1.4 +
                       ty * wind.uy * 1.4;
            var wph2 = (now / 520) * wind.str - tx * wind.uy * 0.9 +
                       ty * wind.ux * 0.9;
            var eta = 0.6 * Math.sin(wph1) + 0.4 * Math.cos(wph2);
            ctx.strokeStyle = wt === 2
              ? "rgba(130,210,255,0.34)" : "rgba(195,240,255,0.48)";
            ctx.lineWidth = Math.max(1, 1.3 * z);
            ctx.beginPath();
            var wx0 = sx + (0.18 + 0.14 * eta) * px,
                wy0 = sy + (0.38 + 0.12 * Math.cos(wph1)) * px;
            ctx.moveTo(wx0, wy0);
            ctx.quadraticCurveTo(wx0 + px * 0.28, wy0 - 3 * z * eta,
                                 wx0 + px * 0.56, wy0);
            ctx.stroke();
            if (eta > 0.62) {
              // Specular sun/moon water glint
              ctx.fillStyle = "rgba(255,250,220,0.65)";
              ctx.fillRect(wx0 + px * 0.2, wy0 - 1.5 * z, 2.5 * z, 1.5 * z);
            }
            if (wt === 1) {
              var foam = 0.22 + 0.18 * Math.sin(now / 400 + tx + ty);
              ctx.strokeStyle = "rgba(235,248,255," + foam.toFixed(2) + ")";
              ctx.beginPath();
              ctx.arc(sx + px * 0.5, sy + px * 0.5, px * 0.44, 0, 7);
              ctx.stroke();
            }
            ctx.lineWidth = 1;
          } else if (wt === 3 && z > 0.45) {
            // 3D Wooden planked bridge with shadow + handrails
            ctx.fillStyle = "rgba(0,0,0,0.35)";
            ctx.fillRect(sx + 2 * z, sy + 3 * z, px, px);
            ctx.fillStyle = "#7c5836";
            ctx.fillRect(sx, sy, px, px);
            ctx.strokeStyle = "#4d3319";
            for (var bp = 1; bp < 4; bp++) {
              ctx.beginPath();
              ctx.moveTo(sx + bp * px / 4, sy);
              ctx.lineTo(sx + bp * px / 4, sy + px);
              ctx.stroke();
            }
            ctx.fillStyle = "#b08554";
            ctx.fillRect(sx, sy, px, 3 * z);
            ctx.fillRect(sx, sy + px - 3 * z, px, 3 * z);
          } else if (z > 0.55 && ((tx * 7 + ty * 13) % 5 === 0)) {
            var sway = Math.sin(now / 520 + tx * 0.7 + ty * 0.5) *
                       wind.vx * 2.4 * z;
            ctx.strokeStyle = "rgba(96,168,78,0.48)";
            ctx.beginPath();
            ctx.moveTo(sx + px * 0.5, sy + px * 0.7);
            ctx.lineTo(sx + px * 0.5 + sway, sy + px * 0.35);
            ctx.stroke();
          }
          if (ts.tileRegion && tx + 1 < W &&
              ts.tileRegion[i] !== ts.tileRegion[i + 1]) {
            ctx.fillStyle = "rgba(255,213,74,0.14)";
            ctx.fillRect(sx + px - 1, sy, 2, px);
          }
          if (f === 1) {
            ctx.fillStyle = "rgba(8,14,10,0.28)";
            ctx.fillRect(sx, sy, px + 1, px + 1);
          }
          if (ts.breach && ts.breach[i]) {
            ctx.fillStyle = "rgba(248,81,73," +
              (0.16 + 0.10 * Math.sin(now / 280)).toFixed(3) + ")";
            ctx.fillRect(sx, sy, px + 1, px + 1);
          }
        }
      }
    },

    /* office (#134): the same tiles drawn as iso floor diamonds. The
       visible world bbox comes from unprojecting the four screen
       corners through toWorld() - the same transform clicks use. */
    _isoTiles: function (ctx, st, theme, z) {
      var ts = st.tiles, W = ts.w, H = ts.h, cv = this.cv;
      var fog = st.visFog || st.fog;
      var a = this.toWorld(0, 0), b = this.toWorld(cv.width, 0),
          c = this.toWorld(0, cv.height), d = this.toWorld(cv.width,
                                                          cv.height);
      var x0 = Math.max(0, Math.floor(
            Math.min(a.x, b.x, c.x, d.x) / TILE) - 1),
          y0 = Math.max(0, Math.floor(
            Math.min(a.y, b.y, c.y, d.y) / TILE) - 1),
          x1 = Math.min(W, Math.ceil(
            Math.max(a.x, b.x, c.x, d.x) / TILE) + 1),
          y1 = Math.min(H, Math.ceil(
            Math.max(a.y, b.y, c.y, d.y) / TILE) + 1);
      for (var ty = y0; ty < y1; ty++) {
        for (var tx = x0; tx < x1; tx++) {
          var i = ty * W + tx;
          var f = fog ? fog[i] : 2;
          var p0 = this.toScreen(tx * TILE, ty * TILE),
              p1 = this.toScreen((tx + 1) * TILE, ty * TILE),
              p2 = this.toScreen((tx + 1) * TILE, (ty + 1) * TILE),
              p3 = this.toScreen(tx * TILE, (ty + 1) * TILE);
          ctx.beginPath();
          ctx.moveTo(p0.x, p0.y); ctx.lineTo(p1.x, p1.y);
          ctx.lineTo(p2.x, p2.y); ctx.lineTo(p3.x, p3.y);
          ctx.closePath();
          if (f === 0) {
            ctx.fillStyle = (tx + ty) % 2 ? "#12151e" : "#0e1118";
            ctx.fill();
            continue;
          }
          ctx.fillStyle = this._tileStyle(ctx, st, theme, i);
          ctx.fill();
          ctx.strokeStyle = "rgba(255,255,255,0.04)";
          ctx.stroke();
          if (f === 1) {
            ctx.fillStyle = "rgba(8,10,16,0.28)"; ctx.fill();
          }
          if (ts.breach && ts.breach[i]) {
            ctx.fillStyle = "rgba(248,81,73," +
              (0.16 + 0.10 * Math.sin(performance.now() / 280))
                .toFixed(3) + ")";
            ctx.fill();
          }
        }
      }
    },

    /* #157 doodads, swaying forest trees, and wandering critters */
    _drawNature: function (ctx, st, theme, z, now, wind) {
      if (this.iso) return;
      var ts = st.tiles;
      if (!ts || !ts._trees) return;
      var self = this, cv = this.cv, fog = st.visFog || st.fog, W = ts.w;
      // 1. Doodads (rocks, wildflowers, reeds, grass tufts)
      (ts._doodads || []).forEach(function (d) {
        var f = fog ? fog[d.ty * W + d.tx] : 2;
        if (f === 0) return;
        var s = self.toScreen(d.x, d.y);
        if (s.x < -20 || s.y < -20 || s.x > cv.width + 20 ||
            s.y > cv.height + 20) return;
        var sw = Math.sin(now / 460 + (d.seed % 31)) * wind.vx * 3 * z;
        if (d.kind === "rock") {
          ctx.fillStyle = "#5b6366";
          ctx.beginPath();
          ctx.ellipse(s.x, s.y, 5 * z, 3.5 * z, 0, 0, 7);
          ctx.fill();
          ctx.fillStyle = "#7c8588";
          ctx.beginPath();
          ctx.ellipse(s.x - 1 * z, s.y - 1 * z, 3 * z, 2 * z, 0, 0, 7);
          ctx.fill();
        } else if (d.kind === "reed") {
          ctx.strokeStyle = "#5c8a46";
          ctx.lineWidth = Math.max(1, 1.2 * z);
          for (var r = -1; r <= 1; r++) {
            ctx.beginPath();
            ctx.moveTo(s.x + r * 2.5 * z, s.y);
            ctx.quadraticCurveTo(s.x + r * 2.5 * z + sw * 0.6, s.y - 5 * z,
                                 s.x + r * 2.5 * z + sw, s.y - 9 * z);
            ctx.stroke();
            ctx.fillStyle = "#5c3a21";
            ctx.beginPath();
            ctx.arc(s.x + r * 2.5 * z + sw * 0.9, s.y - 8 * z, 1.3 * z, 0, 7);
            ctx.fill();
          }
          ctx.lineWidth = 1;
        } else if (d.kind === "flower") {
          ctx.fillStyle = (d.seed % 2) ? "#ffd54a" : "#ff7b72";
          ctx.beginPath();
          ctx.arc(s.x + sw * 0.4, s.y - 2 * z, 2 * z, 0, 7);
          ctx.fill();
        } else {
          ctx.strokeStyle = "#48823c";
          ctx.beginPath();
          ctx.moveTo(s.x, s.y);
          ctx.lineTo(s.x + sw * 0.8, s.y - 5 * z);
          ctx.moveTo(s.x + 2 * z, s.y);
          ctx.lineTo(s.x + 2 * z + sw * 0.8, s.y - 4.5 * z);
          ctx.stroke();
        }
      });
      // 2. Wandering Critters (sheep, stag, hare)
      (ts._critters || []).forEach(function (cr) {
        var ph = now / 1800 + (cr.seed % 100);
        var wx = cr.ox + Math.sin(ph * 0.7) * TILE * 1.4,
            wy = cr.oy + Math.cos(ph * 0.5) * TILE * 1.1;
        var ti = Math.floor(wy / TILE) * W + Math.floor(wx / TILE);
        if (fog && fog[ti] !== 2) return;
        var s = self.toScreen(wx, wy);
        if (s.x < -20 || s.y < -20 || s.x > cv.width + 20 ||
            s.y > cv.height + 20) return;
        var hop = Math.abs(Math.sin(now / 220 + cr.seed)) * 1.8 * z;
        ctx.fillStyle = cr.kind === "sheep" ? "#eceff4" :
                        cr.kind === "stag" ? "#9c6b3b" : "#c4a482";
        ctx.beginPath();
        ctx.ellipse(s.x, s.y - hop, 4.2 * z, 2.8 * z, 0, 0, 7);
        ctx.fill();
        ctx.fillStyle = "#2d2a26";
        ctx.beginPath();
        ctx.arc(s.x + 3.5 * z, s.y - 1.5 * z - hop, 1.6 * z, 0, 7);
        ctx.fill();
      });
      // 3. Multi-layered Swaying Forest Trees (#157)
      (ts._trees || []).forEach(function (tr) {
        var f = fog ? fog[tr.ty * W + tr.tx] : 2;
        if (f === 0) return;
        var s = self.toScreen(tr.x, tr.y);
        if (s.x < -36 || s.y < -36 || s.x > cv.width + 36 ||
            s.y > cv.height + 36) return;
        var sc = tr.scale * Math.max(z, 0.55);
        var swayX = (Math.sin(now / 620 + (tr.seed % 50)) * 0.6 + 0.7) *
                    wind.vx * 3.8 * sc;
        var swayY = (Math.cos(now / 740 + (tr.seed % 50)) * 0.5 + 0.5) *
                    wind.vy * 2.2 * sc;
        ctx.globalAlpha = f === 1 ? 0.55 : 0.96;
        // Ground shadow
        ctx.fillStyle = "rgba(0,0,0,0.32)";
        ctx.beginPath();
        ctx.ellipse(s.x + 3 * sc, s.y + 3 * sc, 9 * sc, 5 * sc, 0, 0, 7);
        ctx.fill();
        // Trunk
        ctx.fillStyle = "#4d3422";
        ctx.fillRect(s.x - 1.8 * sc, s.y - 6 * sc, 3.6 * sc, 8 * sc);
        // Canopy crown layers reacting to wind
        var cDark = tr.kind === "pine" ? "#163822" :
                    tr.kind === "goldleaf" ? "#6e5219" :
                    tr.kind === "willow" ? "#204d38" : "#1d4723";
        var cMid = tr.kind === "pine" ? "#1f4f30" :
                   tr.kind === "goldleaf" ? "#9e7724" :
                   tr.kind === "willow" ? "#2e6b4e" : "#296330";
        var cTop = tr.kind === "pine" ? "#2c6b42" :
                   tr.kind === "goldleaf" ? "#cfa036" :
                   tr.kind === "willow" ? "#438c69" : "#3b8242";
        ctx.fillStyle = cDark;
        ctx.beginPath();
        ctx.arc(s.x + swayX * 0.4, s.y - 7 * sc + swayY * 0.4,
                8.5 * sc, 0, 7);
        ctx.fill();
        ctx.fillStyle = cMid;
        ctx.beginPath();
        ctx.arc(s.x - 2.5 * sc + swayX * 0.75, s.y - 9.5 * sc + swayY * 0.75,
                6.5 * sc, 0, 7);
        ctx.arc(s.x + 2.5 * sc + swayX * 0.75, s.y - 9 * sc + swayY * 0.75,
                6 * sc, 0, 7);
        ctx.fill();
        ctx.fillStyle = cTop;
        ctx.beginPath();
        ctx.arc(s.x + swayX * 1.15, s.y - 12 * sc + swayY * 1.15,
                4.8 * sc, 0, 7);
        ctx.fill();
        ctx.globalAlpha = 1;
      });
    },

    /* #157 live weather & atmospheric particles: cloud shadows, blowing
       leaves, slanted rain + puddle ripples, storm lightning, snow, fog. */
    _weatherPass: function (ctx, st, theme, z, now, wind) {
      var wx = (st && st.weather) || {};
      var cond = wx.condition || "cloudy";
      var clouds = typeof wx.cloud_pct === "number" ? wx.cloud_pct : 40;
      var cv = this.cv, W = cv.width, H = cv.height, i;
      // 1. Drifting cloud shadows across the battlefield
      var nClouds = Math.floor(clouds / 18);
      if (nClouds > 0 && !this.iso) {
        ctx.fillStyle = "rgba(8,14,18,0.16)";
        for (i = 0; i < nClouds; i++) {
          var cs = hash("cloud:" + i);
          var cx = ((cs % 1900) + now * 0.018 * (wind.vx + 0.5)) % (W + 360) - 180;
          var cy = (((cs >> 8) % 1300) + now * 0.012 * (wind.vy + 0.2)) % (H + 260) - 130;
          if (cx < -200) cx += W + 360;
          if (cy < -150) cy += H + 260;
          ctx.beginPath();
          ctx.ellipse(cx, cy, (95 + (cs % 65)) * z, (48 + (cs % 35)) * z,
                      0.2, 0, 7);
          ctx.fill();
        }
      }
      // 2. Blowing / falling leaves carried by the wind vector
      if (!this.iso) {
        var nLeaves = Math.min(28, Math.round(8 + wind.str * 7));
        for (i = 0; i < nLeaves; i++) {
          var ls = hash("leaf:" + i);
          var lx = ((ls % 1600) + now * 0.055 * (wind.vx * 1.6 + 0.4)) % W;
          var ly = (((ls >> 7) % 1200) + now * 0.038 * (wind.vy * 1.4 + 0.7) +
                    Math.sin(now / 420 + i) * 14) % H;
          if (lx < 0) lx += W;
          if (ly < 0) ly += H;
          ctx.fillStyle = (i % 3 === 0) ? "rgba(212,167,44,0.75)" :
                          "rgba(78,148,64,0.72)";
          ctx.beginPath();
          ctx.ellipse(lx, ly, 2.6 * z, 1.3 * z,
                      now / 260 + i, 0, 7);
          ctx.fill();
        }
      }
      // 3. Wind gust streaks when wind is strong
      if (wind.kph >= 20) {
        ctx.strokeStyle = "rgba(220,235,245,0.16)";
        ctx.lineWidth = 1.2;
        var nG = Math.min(18, Math.floor(wind.kph / 3));
        for (i = 0; i < nG; i++) {
          var gs = hash("gust:" + i);
          var gx = ((gs % 1700) + now * 0.32 * wind.ux) % W;
          var gy = (((gs >> 6) % 1100) + now * 0.32 * wind.uy) % H;
          if (gx < 0) gx += W;
          if (gy < 0) gy += H;
          ctx.beginPath();
          ctx.moveTo(gx, gy);
          ctx.lineTo(gx + wind.ux * 38 * z, gy + wind.uy * 38 * z);
          ctx.stroke();
        }
        ctx.lineWidth = 1;
      }
      // 4. Rain / Drizzle / Thunderstorm
      if (cond === "rain" || cond === "storm") {
        var nDrops = cond === "storm" ? 110 : 65;
        ctx.strokeStyle = cond === "storm"
          ? "rgba(175,215,255,0.58)" : "rgba(160,205,245,0.45)";
        ctx.lineWidth = 1.2;
        var dx = wind.vx * 6, dy = 15 + Math.abs(wind.vy) * 4;
        ctx.beginPath();
        for (i = 0; i < nDrops; i++) {
          var rs = hash("rain:" + i);
          var rx = ((rs % 1999) + now * (0.18 * wind.vx + 0.05)) % W;
          var ry = (((rs >> 5) % 1499) + now * (0.48 + (rs % 15) * 0.01)) % H;
          if (rx < 0) rx += W;
          ctx.moveTo(rx, ry);
          ctx.lineTo(rx + dx, ry + dy);
        }
        ctx.stroke();
        ctx.lineWidth = 1;
        // Ground rain splash ripples
        ctx.strokeStyle = "rgba(190,225,255,0.32)";
        for (i = 0; i < 18; i++) {
          var sp = hash("splash:" + i);
          var age = ((now / 420 + (sp % 100) / 100) % 1);
          var sx = (sp % W), sy = ((sp >> 8) % H);
          ctx.beginPath();
          ctx.arc(sx, sy, age * 6 * z, 0, 7);
          ctx.stroke();
        }
        // Storm lightning flash + bolt
        if (cond === "storm") {
          var cyc = now % 6800;
          if (cyc < 140 || (cyc > 220 && cyc < 290)) {
            ctx.fillStyle = "rgba(225,240,255,0.28)";
            ctx.fillRect(0, 0, W, H);
            if (cyc < 140) {
              ctx.strokeStyle = "rgba(240,248,255,0.92)";
              ctx.lineWidth = 2.2;
              var bx = W * (0.25 + ((Math.floor(now / 6800) * 37) % 50) / 100);
              ctx.beginPath();
              ctx.moveTo(bx, 0);
              ctx.lineTo(bx - 18, H * 0.28);
              ctx.lineTo(bx + 12, H * 0.48);
              ctx.lineTo(bx - 24, H * 0.78);
              ctx.stroke();
              ctx.lineWidth = 1;
            }
          }
        }
      } else if (cond === "snow") {
        // 5. Snowflakes swirling in wind
        ctx.fillStyle = "rgba(240,248,255,0.82)";
        for (i = 0; i < 75; i++) {
          var ss = hash("snow:" + i);
          var sx2 = ((ss % 1800) + now * 0.04 * wind.vx +
                     Math.sin(now / 600 + i) * 18) % W;
          var sy2 = (((ss >> 6) % 1400) + now * (0.06 + (ss % 10) * 0.004)) % H;
          if (sx2 < 0) sx2 += W;
          ctx.beginPath();
          ctx.arc(sx2, sy2, (1.4 + (ss % 3) * 0.6) * z, 0, 7);
          ctx.fill();
        }
      } else if (cond === "fog") {
        // 6. Rolling mist banks
        for (i = 0; i < 8; i++) {
          var fs = hash("fogbank:" + i);
          var fx = ((fs % 1600) + now * 0.025 * (wind.vx + 0.4)) % (W + 300) - 150;
          var fy = ((fs >> 7) % H);
          ctx.fillStyle = "rgba(205,220,225,0.14)";
          ctx.beginPath();
          ctx.ellipse(fx, fy, 160 * z, 46 * z, 0, 0, 7);
          ctx.fill();
        }
      }
    },

    /* office furniture + ambient life (#134): pure presentation over
       real positions. Meeting table + water cooler sit on the real
       town-hall plot; kanban walls stand behind real quest markers;
       heroes work at desks; a pending decision walks every hero toward
       the meeting table (GDD 3.2 "units walk to table"). */
    _officeProps: function (ctx, st, theme, z, now) {
      var self = this, pal = theme.palette;
      var th = null, rf = null;
      (st.buildings || []).forEach(function (b) {
        if (b.bid === "town-hall") th = b;
        if (b.bid === "runeforge") rf = b;
      });
      if (th) {
        var s = this.toScreen(th.x, th.y);
        // meeting-room table under the town-hall marker
        ctx.fillStyle = "#3a2f28";
        ctx.beginPath();
        ctx.ellipse(s.x, s.y + 16 * z, 30 * z, 12 * z, 0, 0, 7);
        ctx.fill();
        ctx.strokeStyle = "#5a4632"; ctx.stroke();
        // water cooler: idle staff landmark beside the meeting room
        var wc = this.toScreen(th.x + TILE * 1.7, th.y + TILE * 1.7);
        ctx.fillStyle = "#4a5568";
        ctx.fillRect(wc.x - 4 * z, wc.y - 10 * z, 8 * z, 12 * z);
        ctx.fillStyle = "#58a6ff";
        ctx.beginPath(); ctx.arc(wc.x, wc.y - 12 * z, 4.5 * z, 0, 7);
        ctx.fill();
        if (!st.decision) {   // idle heroes gather by the water cooler
          (st.units || []).filter(function (u) {
            return u.kind === "hero" && u.status_live === "idle";
          }).forEach(function (u, i) {
            var a = 6.2832 * i / 6;
            var wp = self.toScreen(th.x + TILE * (1.7 + 0.6 * Math.cos(a)),
                                   th.y + TILE * (1.7 + 0.6 * Math.sin(a)));
            ctx.globalAlpha = 0.55;
            var sz = 14 * Math.max(z, 0.7);
            Theme.sprite(ctx, theme.units[u.cls] || theme.units.Squire,
                         wp.x - sz / 2, wp.y - sz / 2, sz, sz);
            ctx.globalAlpha = 1;
          });
        }
      }
      if (rf && st.tiles && st.tiles.breach &&
          st.tiles.breach.some(function (x) { return x > 0; })) {
        // gate-fail = printer fire (red/orange flash on runeforge)
        var ps = this.toScreen(rf.x, rf.y);
        var fl = 10 + 5 * Math.sin(now / 120);
        ctx.fillStyle = (now % 300 < 150) ? pal.err : "#ff9800";
        ctx.beginPath();
        ctx.arc(ps.x, ps.y - 18 * z, fl * z, 0, 7);
        ctx.fill();
      }
      // kanban wall behind each quest marker (quest log reskin)
      (st.pois || []).forEach(function (p) {
        if (p.kind !== "quest") return;
        var s = self.toScreen((p.x + .5) * TILE, (p.y + .5) * TILE);
        var bw = 34 * z, bh = 20 * z;
        ctx.fillStyle = "#1b1e28";
        ctx.fillRect(s.x - bw / 2, s.y - 26 * z, bw, bh);
        ctx.strokeStyle = pal.border; ctx.strokeRect(s.x - bw / 2,
          s.y - 26 * z, bw, bh);
        for (var k = 1; k < 3; k++) {
          ctx.beginPath();
          ctx.moveTo(s.x - bw / 2 + bw * k / 3, s.y - 26 * z);
          ctx.lineTo(s.x - bw / 2 + bw * k / 3, s.y - 26 * z + bh);
          ctx.stroke();
        }
        var dots = { done: "#3fb950", blocked: "#8b949e",
                     failed: pal.err, open: "#ffd54a" };
        ctx.fillStyle = dots[p.qst] || dots.open;
        for (var q = 0; q < 3; q++)
          ctx.fillRect(s.x - bw / 2 + 3 * z + bw * q / 3,
                       s.y - 23 * z, 5 * z, 4 * z);
      });
      // decision summons: heroes converge on the meeting-room table.
      // Walkers are presentation ghosts - real unit positions (and so
      // picking/selection) stay exactly where the world puts them.
      if (st.decision) {
        var dd = st.decision, heroes = (st.units || []).filter(
          function (u) { return u.kind === "hero"; });
        var p = Math.min(1, Math.max(0, (now - dd.t0) / 3500));
        heroes.forEach(function (u, i) {
          var ang = 6.2832 * i / Math.max(1, heroes.length);
          var sx = dd.x + Math.cos(ang) * TILE * 1.3,
              sy = dd.y + Math.sin(ang) * TILE * 1.3;
          var a = self.toScreen(u.x, u.y), b = self.toScreen(sx, sy);
          ctx.globalAlpha = 0.30;
          ctx.strokeStyle = "#ffd54a"; ctx.setLineDash([4, 4]);
          ctx.beginPath(); ctx.moveTo(a.x, a.y); ctx.lineTo(b.x, b.y);
          ctx.stroke(); ctx.setLineDash([]); ctx.globalAlpha = 1;
          var wp = self.toScreen(u.x + (sx - u.x) * p,
                                 u.y + (sy - u.y) * p);
          var sz = 16 * Math.max(z, 0.7);
          Theme.sprite(ctx, theme.units[u.cls] || theme.units.Squire,
                       wp.x - sz / 2, wp.y - sz / 2, sz, sz);
        });
      }
    },

    /* #136 ambient life: purely cosmetic critters seeded by hash so the
       scene feels alive without touching world state. Battlefield gets
       birds crossing the sky and fog wisps; office gets dust motes. */
    _ambient: function (ctx, st, theme, z, now) {
      var ts = st.tiles;
      if (!ts) return;
      var mw = ts.w * TILE, mh = ts.h * TILE, cv = this.cv, i, s;
      if (this.iso) {                          // office: drifting motes
        ctx.fillStyle = "rgba(200,210,235,0.28)";
        for (i = 0; i < 8; i++) {
          var sd = hash("mote" + i);
          var mx = ((sd % 977) / 977 * mw + now / 90 * (6 + sd % 9)) % mw;
          var my = mh - ((now / 70 * (5 + sd % 7) + sd % mh) % mh);
          s = this.toScreen(mx, my);
          if (s.x < 0 || s.y < 0 || s.x > cv.width || s.y > cv.height)
            continue;
          ctx.fillRect(s.x, s.y, 1.6, 1.6);
        }
        return;
      }
      // birds: slow crossings high over the field, flap by time parity
      ctx.strokeStyle = "rgba(30,36,30,0.8)";
      ctx.lineWidth = Math.max(1, 1.4 * z);
      for (i = 0; i < 5; i++) {
        var bs = hash("bird" + i);
        var per = 38000 + (bs % 5) * 9000;
        var p = ((now + bs % per) % per) / per;
        var bx = -40 + p * (mw + 80);
        var by = (bs % 1000) / 1000 * mh * 0.8 +
                 Math.sin(now / 700 + bs) * 18;
        s = this.toScreen(bx, by);
        if (s.x < -20 || s.y < -20 || s.x > cv.width + 20 ||
            s.y > cv.height + 20) continue;
        var flap = (now % 400 < 200) ? -1 : 1;
        ctx.beginPath();
        ctx.moveTo(s.x - 5 * z, s.y);
        ctx.quadraticCurveTo(s.x, s.y + flap * 4 * z, s.x, s.y);
        ctx.quadraticCurveTo(s.x, s.y + flap * 4 * z, s.x + 5 * z, s.y);
        ctx.stroke();
      }
      ctx.lineWidth = 1;
      // fog wisps: pale motes drifting over the field edges
      ctx.fillStyle = "rgba(210,225,205,0.20)";
      for (i = 0; i < 6; i++) {
        var ws = hash("wisp" + i);
        var wx = ((ws % 1400) / 1400 * mw +
                  Math.sin(now / 3200 + ws) * 60) % mw;
        var wy = ((ws % 900) / 900 * mh +
                  Math.cos(now / 2700 + ws) * 40) % mh;
        s = this.toScreen(wx, wy);
        if (s.x < 0 || s.y < 0 || s.x > cv.width || s.y > cv.height)
          continue;
        ctx.beginPath();
        ctx.arc(s.x, s.y, (2 + ws % 3) * Math.max(z, 0.6), 0, 7);
        ctx.fill();
      }
    },

    /* #158 live building animations: wind-flapping banners, drifting
       chimney/forge smoke, rising sparks, orbiting arcane rings, portal
       vortex, market awning ripple, sacred braziers, watchtower beacon. */
    _drawBuildingAnim: function (ctx, b, s, w, h, z, now, wind, pal) {
      var bid = b.bid || "vault", i;
      // 1. Wind-flapping roof banners on Keep, Barracks, Watchtower, Trophy Hall
      if (bid === "town-hall" || bid === "barracks" ||
          bid === "watchtower" || bid === "trophy-hall") {
        var bx = s.x + (bid === "town-hall" ? -w * 0.28 : 0),
            by = s.y - h * 0.48;
        ctx.strokeStyle = "#d4a72c";
        ctx.lineWidth = Math.max(1, 1.4 * z);
        ctx.beginPath();
        ctx.moveTo(bx, by + 6 * z);
        ctx.lineTo(bx, by - 8 * z);
        ctx.stroke();
        var flCol = bid === "barracks" ? "#f85149" :
                    bid === "watchtower" ? "#58a6ff" : "#ffd54a";
        ctx.fillStyle = flCol;
        var fx1 = bx + (9 + 3 * Math.sin(now / 140)) * wind.ux * z,
            fy1 = by - 7 * z + (3 * Math.cos(now / 160)) * wind.uy * z;
        ctx.beginPath();
        ctx.moveTo(bx, by - 8 * z);
        ctx.quadraticCurveTo(bx + 5 * wind.ux * z,
                             by - 6 * z + 2 * Math.sin(now / 110) * z,
                             fx1, fy1);
        ctx.lineTo(bx, by - 3 * z);
        ctx.closePath();
        ctx.fill();
        ctx.lineWidth = 1;
      }
      // 2. Chimney smoke & forge sparks drifting with the wind
      if (bid === "tavern" || bid === "runeforge") {
        var cx0 = s.x + (bid === "tavern" ? w * 0.24 : -w * 0.22),
            cy0 = s.y - h * 0.42;
        for (i = 0; i < 4; i++) {
          var ph = ((now / 900 + i * 0.25) % 1);
          var sx = cx0 + ph * wind.vx * 18 * z + Math.sin(now / 300 + i) * 2 * z,
              sy = cy0 - ph * 22 * z + ph * wind.vy * 8 * z;
          ctx.fillStyle = bid === "runeforge"
            ? "rgba(90,85,82," + ((1 - ph) * 0.48).toFixed(2) + ")"
            : "rgba(210,215,220," + ((1 - ph) * 0.42).toFixed(2) + ")";
          ctx.beginPath();
          ctx.arc(sx, sy, (2.2 + ph * 4.5) * z, 0, 7);
          ctx.fill();
        }
        if (bid === "runeforge") {
          // Rising orange forge embers/sparks
          ctx.fillStyle = (now % 240 < 120) ? "#ffd54a" : "#ff6a00";
          for (i = 0; i < 3; i++) {
            var ep = ((now / 450 + i * 0.33) % 1);
            ctx.fillRect(cx0 + ep * wind.vx * 12 * z + (i - 1) * 3 * z,
                         cy0 - ep * 18 * z, 2 * z, 2 * z);
          }
        }
      }
      // 3. Orbiting arcane rings / crystal on Library & Vault
      if (bid === "library" || bid === "vault") {
        var ang = now / 520;
        ctx.strokeStyle = bid === "library" ? "#58a6ff" : "#ffd54a";
        ctx.lineWidth = Math.max(1, 1.3 * z);
        ctx.beginPath();
        ctx.ellipse(s.x, s.y - h * 0.36, 9 * z, 3.8 * z,
                    Math.sin(ang) * 0.35, 0, 7);
        ctx.stroke();
        ctx.fillStyle = "#fff";
        ctx.beginPath();
        ctx.arc(s.x + Math.cos(ang) * 9 * z,
                s.y - h * 0.36 + Math.sin(ang) * 3.8 * z, 2 * z, 0, 7);
        ctx.fill();
        ctx.lineWidth = 1;
      }
      // 4. Swirling dimensional vortex on Portal
      if (bid === "portal") {
        ctx.strokeStyle = (now % 320 < 160) ? "#e879f9" : "#38bdf8";
        ctx.lineWidth = Math.max(1.2, 1.6 * z);
        var pa = now / 280;
        ctx.beginPath();
        ctx.arc(s.x, s.y, 7 * z, pa, pa + 2.4);
        ctx.stroke();
        ctx.beginPath();
        ctx.arc(s.x, s.y, 4.5 * z, -pa, -pa + 2.2);
        ctx.stroke();
        ctx.lineWidth = 1;
      }
      // 5. Sacred soul-flame braziers on Altar & Barracks
      if (bid === "altar" || bid === "barracks") {
        var fcol = bid === "altar" ? "#38bdf8" : "#ff7b00";
        var flk = Math.sin(now / 110) * 1.8 * z;
        ctx.fillStyle = fcol;
        ctx.beginPath();
        ctx.arc(s.x - w * 0.30 + wind.vx * z, s.y + h * 0.12 - flk * 0.4,
                2.8 * z, 0, 7);
        ctx.arc(s.x + w * 0.30 + wind.vx * z, s.y + h * 0.12 + flk * 0.4,
                2.8 * z, 0, 7);
        ctx.fill();
      }
      // 6. Rotating lookout beacon on Watchtower
      if (bid === "watchtower") {
        var ba = now / 900;
        ctx.fillStyle = "rgba(255,213,74,0.16)";
        ctx.beginPath();
        ctx.moveTo(s.x, s.y - h * 0.38);
        ctx.lineTo(s.x + Math.cos(ba) * 28 * z,
                   s.y - h * 0.38 + Math.sin(ba) * 18 * z);
        ctx.lineTo(s.x + Math.cos(ba + 0.35) * 28 * z,
                   s.y - h * 0.38 + Math.sin(ba + 0.35) * 18 * z);
        ctx.closePath();
        ctx.fill();
      }
    },

    /* #158/#163 living unit & hero renderer: directional cast shadow,
       WC3 Hero Glow, rotating Aura runes, 4-node Verlet cloth cape,
       2-bone articulated leg stride + dust puffs, Stand-1/2/3 autonomous
       idle fidgets, active weapon slash ribbons, and ranged projectiles. */
    _drawUnitLive: function (ctx, u, s, sz, dy, ent, z, now, wind, pal, all) {
      var ph = hash(String(u.id));
      var isHero = u.kind === "hero";
      // 0. Directional Sun/Moon Projected Cast Shadow (#163)
      ctx.fillStyle = "rgba(0,0,0,0.34)";
      ctx.beginPath();
      ctx.ellipse(s.x + sz * 0.24, s.y + sz * 0.34,
                  sz * 0.48, sz * 0.20, 0.28, 0, 7);
      ctx.fill();
      // 1. WC3 Hero Glow & Rotating Geometric Aura Rune under feet
      if (isHero) {
        var gRad = sz * 0.76;
        var grad = ctx.createRadialGradient(
          s.x, s.y + sz * 0.22, sz * 0.1,
          s.x, s.y + sz * 0.22, gRad);
        grad.addColorStop(0, "rgba(255,213,74,0.38)");
        grad.addColorStop(1, "rgba(255,213,74,0)");
        ctx.fillStyle = grad;
        ctx.beginPath();
        ctx.arc(s.x, s.y + sz * 0.22, gRad, 0, 7);
        ctx.fill();
        if ((u.level || 1) >= 1 && z > 0.55) {
          var aAng = now / 900 + (ph % 10);
          ctx.strokeStyle = ent.trim || "#ffd54a";
          ctx.globalAlpha = 0.48;
          ctx.setLineDash([3 * z, 3 * z]);
          ctx.beginPath();
          ctx.ellipse(s.x, s.y + sz * 0.28, sz * 0.56, sz * 0.23, 0, 0, 7);
          ctx.stroke();
          ctx.setLineDash([]);
          for (var rp = 0; rp < 4; rp++) {
            var ra = aAng + rp * 1.5708;
            ctx.fillStyle = ent.trim || "#ffd54a";
            ctx.fillRect(s.x + Math.cos(ra) * sz * 0.54 - 1.5 * z,
                         s.y + sz * 0.28 + Math.sin(ra) * sz * 0.22 - 1.5 * z,
                         3 * z, 3 * z);
          }
          ctx.globalAlpha = 1;
        }
      }
      // 2. 4-Node Verlet Cloth Cape behind Heroes & Martial/Caster classes (#163)
      if (isHero || ent.arch === "martial" || ent.arch === "caster" ||
          ent.arch === "commander") {
        var vxU = u.moving ? (u.tx - u.x) : 0,
            vyU = u.moving ? (u.ty - u.y) : 0;
        var vLen = Math.hypot(vxU, vyU) || 1;
        var trailX = u.moving ? (-vxU / vLen) * 5 : 0,
            trailY = u.moving ? (-vyU / vLen) * 3 : 0;
        var n1x = s.x + (wind.vx * 2.2 + trailX * 0.4) * z,
            n1y = s.y + sz * 0.08 + dy;
        var n2x = s.x + (wind.vx * 5.0 + trailX * 0.8 +
                  Math.sin(now / 140 + ph) * 2.2) * z,
            n2y = s.y + sz * 0.22 + wind.vy * 1.8 * z + dy * 0.5;
        var n3x = s.x + (wind.vx * 7.8 + trailX * 1.2 +
                  Math.sin(now / 115 + ph + 1.2) * 3.4) * z,
            n3y = s.y + sz * 0.38 + (wind.vy * 3.2 + trailY) * z;
        ctx.fillStyle = ent.dark || "#1b325f";
        ctx.beginPath();
        ctx.moveTo(s.x - sz * 0.28, s.y - sz * 0.06 + dy);
        ctx.quadraticCurveTo(n1x - sz * 0.26, n1y, n2x - sz * 0.24, n2y);
        ctx.lineTo(n3x - sz * 0.20, n3y);
        ctx.lineTo(n3x + sz * 0.20, n3y);
        ctx.lineTo(n2x + sz * 0.24, n2y);
        ctx.quadraticCurveTo(n1x + sz * 0.26, n1y,
                             s.x + sz * 0.28, s.y - sz * 0.06 + dy);
        ctx.closePath();
        ctx.fill();
        ctx.strokeStyle = ent.trim || "#ffd54a";
        ctx.lineWidth = Math.max(0.8, 1.1 * z);
        ctx.stroke();
        ctx.lineWidth = 1;
      }
      // 3. 2-Bone Articulated Leg Stride & Footstep Dust Puffs (#163)
      if (z > 0.5) {
        var lph = u.moving ? (now / 72 + ph) : 0;
        var lStride = u.moving ? Math.sin(lph) * 4.2 * z : 0;
        var lLiftL = u.moving ? Math.max(0, -Math.cos(lph)) * 2.5 * z : 0;
        var lLiftR = u.moving ? Math.max(0, Math.cos(lph)) * 2.5 * z : 0;
        // Left & Right articulated thigh + armored greave/boot
        ctx.strokeStyle = ent.dark || "#2b2623";
        ctx.lineWidth = Math.max(2, 2.8 * z);
        ctx.beginPath();
        ctx.moveTo(s.x - 3.5 * z, s.y + sz * 0.16 + dy);
        ctx.lineTo(s.x - 4 * z + lStride * 0.6,
                   s.y + sz * 0.34 - lLiftL);
        ctx.moveTo(s.x + 3.5 * z, s.y + sz * 0.16 + dy);
        ctx.lineTo(s.x + 4 * z - lStride * 0.6,
                   s.y + sz * 0.34 - lLiftR);
        ctx.stroke();
        ctx.lineWidth = 1;
        ctx.fillStyle = "#4a331d";
        ctx.fillRect(s.x - 5.5 * z + lStride * 0.6,
                     s.y + sz * 0.32 - lLiftL, 3.6 * z, 3.2 * z);
        ctx.fillRect(s.x + 2.0 * z - lStride * 0.6,
                     s.y + sz * 0.32 - lLiftR, 3.6 * z, 3.2 * z);
        if (u.moving) {
          for (var dp = 0; dp < 3; dp++) {
            var dph = ((now / 320 + dp * 0.33 + (ph % 7) * 0.1) % 1);
            ctx.fillStyle = "rgba(185,170,140," +
              ((1 - dph) * 0.45).toFixed(2) + ")";
            ctx.beginPath();
            ctx.arc(s.x - (dp - 1) * 4 * z - wind.vx * dph * 6 * z,
                    s.y + sz * 0.38 + dph * 4 * z,
                    (1.8 + dph * 2.8) * z, 0, 7);
            ctx.fill();
          }
        }
      }
      // 4. Autonomous Idle Fidgets (Stand - 1/2/3: look around, flourish, social)
      var fidgetSlot = Math.floor((now / 2800 + (ph % 19))) % 7;
      var subT = ((now / 2800 + (ph % 19)) % 1);
      var gx = 0;
      if (!u.moving && u.status_live !== "running" && !u.acting) {
        if (fidgetSlot === 2) {
          gx = Math.sin(subT * 6.283) * 2.2 * z;
        }
      }
      // Draw core 3D-shaded multi-part unit sprite
      Theme.sprite(ctx, ent, s.x - sz / 2 + gx, s.y - sz / 2 + dy, sz, sz);

      // 5. Active Combat / Work Swing + Ranged Projectiles (#163)
      if (u.status_live === "running" || u.acting) {
        var swAng = Math.sin(now / 90 + ph) * 1.15;
        ctx.strokeStyle = ent.arch === "caster" ? "#38bdf8" : "#ffd54a";
        ctx.lineWidth = Math.max(1.8, 2.6 * z);
        ctx.beginPath();
        ctx.arc(s.x, s.y + dy, sz * 0.60, swAng - 0.65, swAng + 0.65);
        ctx.stroke();
        ctx.lineWidth = 1;
        // Ranged projectile (arrow for ranger, arcane bolt for caster)
        if (ent.arch === "ranger" || ent.arch === "caster") {
          var pProg = ((now / 420 + (ph % 11) * 0.1) % 1);
          var px2 = s.x + Math.cos(ph) * pProg * 28 * z,
              py2 = s.y + Math.sin(ph) * pProg * 28 * z -
                    Math.sin(pProg * Math.PI) * 10 * z;
          if (ent.arch === "caster") {
            ctx.fillStyle = "#38bdf8";
            ctx.beginPath();
            ctx.arc(px2, py2, 3 * z, 0, 7);
            ctx.fill();
          } else {
            ctx.strokeStyle = "#f0e6d2";
            ctx.lineWidth = Math.max(1.2, 1.6 * z);
            ctx.beginPath();
            ctx.moveTo(px2 - 4 * z, py2 - 2 * z);
            ctx.lineTo(px2 + 4 * z, py2 + 2 * z);
            ctx.stroke();
            ctx.lineWidth = 1;
          }
        }
        if ((now + ph) % 260 < 110) {
          ctx.fillStyle = "#fff8dc";
          ctx.fillRect(s.x + Math.cos(swAng) * sz * 0.58 - 1.5 * z,
                       s.y + Math.sin(swAng) * sz * 0.58 - 1.5 * z,
                       3 * z, 3 * z);
        }
      } else if (!u.moving && z > 0.55) {
        if (fidgetSlot === 4 && subT < 0.55) {
          // Stand - 3: Heroic weapon/staff flourish glint above shoulder
          ctx.strokeStyle = ent.trim || "#ffd54a";
          ctx.lineWidth = 1.6;
          var fy = s.y - sz * 0.55 - Math.sin(subT * 5.5) * 4 * z;
          ctx.beginPath();
          ctx.moveTo(s.x + sz * 0.35, s.y - sz * 0.1);
          ctx.lineTo(s.x + sz * 0.42, fy);
          ctx.stroke();
          ctx.fillStyle = "#fff";
          ctx.beginPath();
          ctx.arc(s.x + sz * 0.42, fy, 2 * z, 0, 7);
          ctx.fill();
          ctx.lineWidth = 1;
        } else if (fidgetSlot === 5 && !u.bark) {
          for (var ai = 0; ai < all.length; ai++) {
            var o = all[ai];
            if (o.id !== u.id && Math.hypot(o.x - u.x, o.y - u.y) < TILE * 3.2) {
              ctx.fillStyle = "rgba(20,28,22,0.82)";
              ctx.beginPath();
              ctx.arc(s.x + sz * 0.42, s.y - sz * 0.48, 5.5 * z, 0, 7);
              ctx.fill();
              ctx.strokeStyle = "#d4a72c";
              ctx.stroke();
              ctx.fillStyle = "#ffd54a";
              ctx.font = "bold " + Math.max(7, Math.round(8 * z)) + "px monospace";
              ctx.textAlign = "center"; ctx.textBaseline = "middle";
              ctx.fillText((ph % 2) ? ".." : "!", s.x + sz * 0.42, s.y - sz * 0.48);
              break;
            }
          }
        }
      }
    },

    // ---- frame -----------------------------------------------------
    /* state = {tiles:{w,h,data}, fog, regions:{id->{cx,cy,tileId}},
       units:[{id,x,y,cls,kind,status_live,hp,mana,gate_fail,sel,bark}],
       buildings:[{id,x,y,bid,activity}], now} */
    render: function (st, theme) {
      var ctx = this.ctx, cv = this.cv;
      if (cv.width !== cv.clientWidth) cv.width = cv.clientWidth;
      if (cv.height !== cv.clientHeight) cv.height = cv.clientHeight;
      var t0 = performance.now();
      this.iso = !!(theme && theme.iso);   // office = isometric (#134)
      var v = this.view(), z = this.cam.zoom, pal = theme.palette;
      ctx.fillStyle = pal.bg; ctx.fillRect(0, 0, cv.width, cv.height);
      this.units = st.units || [];
      this.buildings = st.buildings || [];
      if (!st.tiles) return;
      var ts = st.tiles, W = ts.w, H = ts.h;
      this._ensureEnv(ts, st);
      st.visFog = this._sightFog(st);
      var wind = this._windVec(st, t0);
      this.wind = wind;
      if (this.iso) { this._isoTiles(ctx, st, theme, z); }
      else { this._flatTiles(ctx, st, theme, z, v, t0, wind); }
      this._drawNature(ctx, st, theme, z, t0, wind);
      // POI markers: quests show through fog, others only once seen (#122)
      var self = this;
      var vfog = st.visFog || st.fog;
      (st.pois || []).forEach(function (p) {
        var i = p.y * W + p.x;
        var f = vfog ? vfog[i] : 2;
        if (f === 0 && p.kind !== "quest") return;
        var s = self.toScreen(p.x * TILE + TILE / 2, p.y * TILE + TILE / 2);
        if (s.x < -30 || s.y < -30 || s.x > cv.width + 30 ||
            s.y > cv.height + 30) return;
        if (p.kind === "gold") {
          // WC3 Gold Mine vein: rock mound + glinting gold crystals
          ctx.fillStyle = "#4d4538";
          ctx.beginPath();
          ctx.ellipse(s.x, s.y + 2 * z, 11 * z, 7 * z, 0, 0, 7);
          ctx.fill();
          ctx.fillStyle = "#ffd54a";
          ctx.beginPath();
          ctx.moveTo(s.x - 5 * z, s.y + 2 * z);
          ctx.lineTo(s.x - 2 * z, s.y - 6 * z);
          ctx.lineTo(s.x + 2 * z, s.y + 2 * z);
          ctx.moveTo(s.x + 1 * z, s.y + 3 * z);
          ctx.lineTo(s.x + 5 * z, s.y - 4 * z);
          ctx.lineTo(s.x + 7 * z, s.y + 3 * z);
          ctx.fill();
          return;
        }
        if (p.kind === "camp") {
          // Neutral Creep Campfire: logs + flickering orange/yellow flame
          ctx.strokeStyle = "#5c3a21";
          ctx.lineWidth = Math.max(1.5, 2 * z);
          ctx.beginPath();
          ctx.moveTo(s.x - 5 * z, s.y + 3 * z);
          ctx.lineTo(s.x + 5 * z, s.y - 2 * z);
          ctx.moveTo(s.x - 5 * z, s.y - 2 * z);
          ctx.lineTo(s.x + 5 * z, s.y + 3 * z);
          ctx.stroke();
          ctx.lineWidth = 1;
          var fh = (6 + 2.5 * Math.sin(t0 / 110 + p.x)) * z;
          ctx.fillStyle = "#ff7b00";
          ctx.beginPath();
          ctx.arc(s.x + wind.vx * 1.2 * z, s.y - 2 * z, 4 * z, 0, 7);
          ctx.fill();
          ctx.fillStyle = "#ffd54a";
          ctx.beginPath();
          ctx.arc(s.x + wind.vx * 1.8 * z, s.y - fh * 0.5, 2.2 * z, 0, 7);
          ctx.fill();
          return;
        }
        // #130 quest marker states: open "!" gold, blocked "?" grey,
        // done "*" rewards stamp (green), failed "!" red until retried
        var g = p.qst === "done" ? "*" : p.qst === "blocked" ? "?" : "!";
        var c = ({ done: "#3fb950", blocked: "#8b949e", failed: pal.err,
                   open: "#ffd54a" })[p.qst] || "#ffd54a";
        var bob = Math.sin(t0 / 320 + p.x) * 2.5 * z;
        ctx.fillStyle = "rgba(0,0,0,0.55)";
        ctx.beginPath();
        ctx.arc(s.x, s.y - 8 * z + bob, 8 * z, 0, 7);
        ctx.fill();
        ctx.strokeStyle = c;
        ctx.lineWidth = 1.5;
        ctx.stroke();
        ctx.lineWidth = 1;
        ctx.fillStyle = c;
        ctx.font = "bold " + Math.max(10, 13 * z) + "px monospace";
        ctx.textAlign = "center"; ctx.textBaseline = "middle";
        ctx.fillText(g, s.x, s.y - 8 * z + bob);
      });
      (st.buildings || []).forEach(function (b) {
        var s = self.toScreen(b.x, b.y);
        if (s.x < -72 || s.y < -72 || s.x > cv.width + 72 ||
            s.y > cv.height + 72) return;
        var w = 48 * z, h = 48 * z;
        Theme.sprite(ctx, theme.buildings[b.bid] || theme.buildings["vault"],
                     s.x - w / 2, s.y - h / 2, w, h);
        self._drawBuildingAnim(ctx, b, s, w, h, z, t0, wind, pal);
        if (b.sel) {
          ctx.strokeStyle = pal.sel; ctx.lineWidth = 2;
          ctx.beginPath();
          ctx.ellipse(s.x, s.y + h * 0.25, w * 0.58, h * 0.30, 0, 0, 7);
          ctx.stroke();
          ctx.lineWidth = 1;
        }
        if (z > 0.72 && b.name) {
          ctx.fillStyle = "rgba(10,16,12,0.75)";
          ctx.fillRect(s.x - 28 * z, s.y + h / 2 + 1, 56 * z, 11 * z);
          ctx.fillStyle = "#ffd54a";
          ctx.font = "bold " + Math.max(8, Math.round(9 * z)) + "px monospace";
          ctx.textAlign = "center"; ctx.textBaseline = "middle";
          ctx.fillText(b.name, s.x, s.y + h / 2 + 6.5 * z);
        }
      });
      if (this.iso) this._officeProps(ctx, st, theme, z, t0); // #134
      var allUnits = st.units || [];
      allUnits.forEach(function (u) {
        var s = self.toScreen(u.x, u.y);
        if (s.x < -48 || s.y < -48 || s.x > cv.width + 48 ||
            s.y > cv.height + 48) return;
        var sz = (u.kind === "minion" ? 16 : u.kind === "worker" ? 12 : 26)
            * Math.max(z, 0.72);
        var ent = theme.units[u.cls] || theme.units.Squire;
        var dy = 0, ph = hash(String(u.id));
        if (self.iso) {          // #134: desk under office workers
          var dw = u.kind === "minion" ? sz * 2.2 : sz * 1.3;
          ctx.fillStyle = "#4a4034";
          ctx.fillRect(s.x - dw / 2, s.y + sz * 0.15, dw, sz * 0.38);
          ctx.fillStyle = "#5c503f";
          ctx.fillRect(s.x - dw / 2, s.y + sz * 0.15, dw, 2);
        }
        // #136/#158 animation states: walk stride bounce, active work/combat,
        // or autonomous Stand - 1/2/3 breathing & fidgets
        if (u.moving)
          dy = -Math.abs(Math.sin(t0 / 85 + ph)) * 2.8 * z;
        else if (u.status_live === "running" || u.acting)
          dy = Math.sin(t0 / 130 + ph) * 2.0 * z;
        else
          dy = Math.sin(t0 / 1100 + ph) * 1.2 * z;
        self._drawUnitLive(ctx, u, s, sz, dy, ent, z, t0, wind, pal, allUnits);
        if (u.status_live === "failed" || u.gate_fail) {
          ctx.strokeStyle = pal.err; ctx.lineWidth = 2;
          ctx.beginPath(); ctx.arc(s.x, s.y, sz / 2 + 3, 0, 7); ctx.stroke();
          ctx.lineWidth = 1;
        }
        if (u.sel) {
          // WC3 bright green/gold elliptical ground selection ring
          ctx.strokeStyle = "#3fb950"; ctx.lineWidth = 2.2;
          ctx.beginPath();
          ctx.ellipse(s.x, s.y + sz * 0.34, sz * 0.56, sz * 0.24, 0, 0, 7);
          ctx.stroke();
          ctx.strokeStyle = pal.sel; ctx.lineWidth = 1;
          ctx.beginPath();
          ctx.ellipse(s.x, s.y + sz * 0.34, sz * 0.64, sz * 0.28, 0, 0, 7);
          ctx.stroke();
        }
        if (u.kind === "hero" && typeof u.hp === "number" && z > 0.45) {
          var bw = sz * 1.15;
          ctx.fillStyle = "rgba(0,0,0,0.85)";
          ctx.fillRect(s.x - bw / 2 - 1, s.y - sz / 2 - 10, bw + 2, 7);
          ctx.fillStyle = u.hp > 50 ? pal.ok : u.hp > 25 ? "#d29922" : pal.err;
          ctx.fillRect(s.x - bw / 2, s.y - sz / 2 - 9, bw * u.hp / 100, 3);
          if (typeof u.mana === "number") {
            var low = u.mana < 25;
            ctx.fillStyle = low && (t0 % 600 < 300) ? pal.err : "#58a6ff";
            ctx.fillRect(s.x - bw / 2, s.y - sz / 2 - 5,
              bw * u.mana / 100, 2);
          }
          // Level badge pip next to HP bar
          ctx.fillStyle = "#d4a72c";
          ctx.fillRect(s.x - bw / 2 - 11, s.y - sz / 2 - 10, 9, 8);
          ctx.fillStyle = "#000";
          ctx.font = "bold 7px monospace";
          ctx.textAlign = "center"; ctx.textBaseline = "middle";
          ctx.fillText(String(u.level || 1), s.x - bw / 2 - 6.5, s.y - sz / 2 - 6);
        }
        if (z > 0.75 && u.name) {
          ctx.fillStyle = "rgba(0,0,0,0.65)";
          ctx.fillRect(s.x - 24 * z, s.y + sz / 2 + 2, 48 * z, 10 * z);
          ctx.fillStyle = pal.text;
          ctx.font = "bold " + Math.max(8, Math.round(9 * z)) + "px monospace";
          ctx.textAlign = "center"; ctx.textBaseline = "middle";
          ctx.fillText(u.name, s.x, s.y + sz / 2 + 7 * z);
        }
        // voice bark: heartbeat note / ack floats over the head (#125)
        if (u.bark && z > 0.55) {
          ctx.fillStyle = "rgba(18,26,20,0.88)";
          var tw = Math.min(180, (u.bark.length * 5.5 + 10) * z);
          ctx.fillRect(s.x - tw / 2, s.y - sz / 2 - 25 * z, tw, 12 * z);
          ctx.strokeStyle = "#d4a72c";
          ctx.strokeRect(s.x - tw / 2, s.y - sz / 2 - 25 * z, tw, 12 * z);
          ctx.fillStyle = "#fff8dc";
          ctx.font = "italic " + Math.max(9, Math.round(9.5 * z)) + "px monospace";
          ctx.textAlign = "center"; ctx.textBaseline = "middle";
          ctx.fillText(u.bark, s.x, s.y - sz / 2 - 19 * z);
        }
      });
      // worker peasants scurry between buildings carrying gold/lumber (#125/#158)
      var now = performance.now();
      var srvNow = st.srvClock ? st.srvClock.srv +
        (now - st.srvClock.perf) / 1000 : now / 1000;
      (st.workers || []).forEach(function (wk, wi) {
        var prog = Math.min(1, Math.max(0, (srvNow - wk.ts) / 4));
        var wx = (wk.from[0] + (wk.to[0] - wk.from[0]) * prog) * TILE + 16;
        var wy = (wk.from[1] + (wk.to[1] - wk.from[1]) * prog) * TILE + 16;
        var s = self.toScreen(wx, wy);
        if (s.x < -20 || s.y < -20 || s.x > cv.width + 20 ||
            s.y > cv.height + 20) return;
        var wsize = 13 * Math.max(z, 0.7);
        var wbob = Math.abs(Math.sin(now / 75 + wi)) * 2 * z;
        Theme.sprite(ctx, theme.units.Worker, s.x - wsize / 2,
                     s.y - wsize / 2 - wbob, wsize, wsize);
        // Hauling sack of gold or bundle of timber on shoulder
        ctx.fillStyle = (wi % 2 === 0) ? "#ffd54a" : "#8b5a2b";
        ctx.beginPath();
        ctx.arc(s.x - wsize * 0.28, s.y - wsize * 0.25 - wbob,
                3.2 * z, 0, 7);
        ctx.fill();
      });
      // Active Spell AoE & Floating Combat/Harvest Popups (#158/#159)
      (st.fx || []).forEach(function (fx) {
        var age = (now - fx.t0) / 1000, dur = fx.dur || 2.2;
        if (age < 0 || age > dur) return;
        var p = age / dur;
        var s = self.toScreen(fx.x, fx.y);
        ctx.save();
        ctx.globalAlpha = Math.max(0, 1 - p);
        if (fx.kind === "spell") {
          var rad = (12 + p * 46) * z;
          ctx.strokeStyle = fx.color || "#58a6ff";
          ctx.lineWidth = 2.5;
          ctx.beginPath();
          ctx.arc(s.x, s.y, rad, 0, 7);
          ctx.stroke();
          ctx.beginPath();
          ctx.arc(s.x, s.y, rad * 0.65, p * 4, p * 4 + 4.5);
          ctx.stroke();
          // Vertical pillar of light / lightning bolts
          ctx.fillStyle = fx.color || "#58a6ff";
          ctx.globalAlpha = Math.max(0, (1 - p) * 0.28);
          ctx.fillRect(s.x - 10 * z, s.y - 65 * z * (1 - p * 0.3),
                       20 * z, 65 * z * (1 - p * 0.3));
        } else if (fx.kind === "text") {
          ctx.fillStyle = fx.color || "#ffd54a";
          ctx.font = "bold " + Math.max(10, Math.round(11 * z)) + "px monospace";
          ctx.textAlign = "center";
          ctx.fillText(fx.text || "", s.x, s.y - age * 22 * z);
        }
        ctx.restore();
      });
      // death/despawn fades (#125)
      (st.fades || []).forEach(function (f) {
        var age = (now - f.t0) / 1000;
        if (age > 2.5) return;
        var s = self.toScreen(f.x, f.y - age * 14);
        ctx.globalAlpha = Math.max(0, 1 - age / 2.5);
        Theme.sprite(ctx, theme.units[f.cls] || theme.units.Squire,
                     s.x - 10 * z, s.y - 10 * z, 20 * z, 20 * z);
        ctx.globalAlpha = 1;
      });
      // ravens: mailbox deposits arc sender -> recipient, flap + fade (#128)
      (st.ravens || []).forEach(function (r) {
        var age = (now - r.t0) / 1000, dur = 5;
        if (age > dur) return;
        var p = age / dur;
        var wx = r.fx + (r.tx - r.fx) * p;
        var wy = r.fy + (r.ty - r.fy) * p - Math.sin(p * Math.PI) * TILE;
        var s = self.toScreen(wx, wy);
        if (s.x < -20 || s.y < -20 || s.x > cv.width + 20 ||
            s.y > cv.height + 20) return;
        var flap = (now % 360 < 180) ? -1 : 1;
        ctx.strokeStyle = "#e6e2d0";
        ctx.lineWidth = 2;
        ctx.beginPath();                      // body + flapping wings
        ctx.arc(s.x, s.y, 2.5 * z, 0, 7);
        ctx.moveTo(s.x, s.y);
        ctx.lineTo(s.x - 6 * z, s.y + flap * 5 * z);
        ctx.moveTo(s.x, s.y);
        ctx.lineTo(s.x + 6 * z, s.y + flap * 5 * z);
        ctx.stroke();
        ctx.lineWidth = 1;
        // faint dotted trail back to the origin
        ctx.globalAlpha = 0.35;
        ctx.fillStyle = "#e6e2d0";
        for (var q = 0.15; q < p; q += 0.15) {
          var tx2 = r.fx + (r.tx - r.fx) * q;
          var ty2 = r.fy + (r.ty - r.fy) * q - Math.sin(q * Math.PI) * TILE;
          var ts2 = self.toScreen(tx2, ty2);
          ctx.fillRect(ts2.x - 1, ts2.y - 1, 2, 2);
        }
        ctx.globalAlpha = 1;
      });
      // queued order waypoints (#127): dashed path from the unit to each
      // numbered flag; ghost (translucent) while the intent is pending,
      // solid once the session acknowledged it
      (st.waypoints || []).forEach(function (wp) {
        var s = self.toScreen(wp.x, wp.y);
        var us = self.toScreen(wp.ux, wp.uy);
        var ghost = wp.state === "queued";
        ctx.globalAlpha = ghost ? 0.4 : 0.95;
        ctx.strokeStyle = "#58a6ff";
        ctx.setLineDash([4 * z, 4 * z]);
        ctx.beginPath(); ctx.moveTo(us.x, us.y);
        ctx.lineTo(s.x, s.y); ctx.stroke();
        ctx.setLineDash([]);
        var fh = 12 * Math.max(z, 0.7);
        ctx.fillStyle = "#58a6ff";
        ctx.fillRect(s.x - 1, s.y - fh, 2, fh);
        ctx.beginPath();
        ctx.moveTo(s.x + 1, s.y - fh);
        ctx.lineTo(s.x + 9 * z, s.y - fh * 0.75);
        ctx.lineTo(s.x + 1, s.y - fh * 0.5);
        ctx.fill();
        ctx.fillStyle = pal.text;
        ctx.font = "bold " + Math.max(9, 10 * z) + "px monospace";
        ctx.textAlign = "center"; ctx.textBaseline = "bottom";
        ctx.fillText(String(wp.n), s.x, s.y - fh - 1);
        ctx.globalAlpha = 1;
      });
      // event pings: expanding rings, color = kind (#124)
      (st.pings || []).forEach(function (p) {
        var age = (now - p.t0) / 1000;
        if (age < 0 || age > 6) return;
        var s = self.toScreen(p.x, p.y);
        var r = (8 + age * 26) * z;
        ctx.globalAlpha = Math.max(0, 1 - age / 6);
        ctx.strokeStyle = ({
          decision: "#ffd54a", fail: "#f85149", spawn: "#3fb950",
          contested: "#e3813f", file: "#9fb4c7",
          order: "#58a6ff" })[p.kind] || pal.sel;
        ctx.lineWidth = 2;
        ctx.beginPath(); ctx.arc(s.x, s.y, r, 0, 7); ctx.stroke();
        ctx.globalAlpha = 1; ctx.lineWidth = 1;
      });
      this._ambient(ctx, st, theme, z, now);
      this._weatherPass(ctx, st, theme, z, now, wind);
      // #136 day/night: cosmetic dim over the map (session-time cycle,
      // computed client-side); skipped entirely when the toggle is off
      if (st.night) {
        ctx.fillStyle = "rgba(10,12,40," + (st.night * 0.55).toFixed(3) + ")";
        ctx.fillRect(0, 0, cv.width, cv.height);
        (st.buildings || []).forEach(function (b) {   // lit windows
          var s = self.toScreen(b.x, b.y);
          if (s.x < -64 || s.y < -64 || s.x > cv.width + 64 ||
              s.y > cv.height + 64) return;
          ctx.fillStyle = "rgba(255,214,110," +
            (0.5 + 0.4 * st.night).toFixed(3) + ")";
          var wz = Math.max(z, 0.6);
          ctx.fillRect(s.x - 9 * wz, s.y - 3 * wz, 5 * wz, 6 * wz);
          ctx.fillRect(s.x + 4 * wz, s.y - 3 * wz, 5 * wz, 6 * wz);
        });
      }
      // drag-select rectangle overlay (#126)
      if (this.box) {
        var b = this.box;
        ctx.fillStyle = "rgba(88,166,255,0.10)";
        ctx.fillRect(b.x0, b.y0, b.x1 - b.x0, b.y1 - b.y0);
        ctx.strokeStyle = pal.sel;
        ctx.strokeRect(b.x0 + 0.5, b.y0 + 0.5, b.x1 - b.x0, b.y1 - b.y0);
      }
      // fps meter
      var dt = performance.now() - t0;
      this.fps.n++; this.fps.t += dt;
      if (this.fps.n >= 30) {
        this.fps.v = Math.round(1000 / Math.max(0.1, this.fps.t / this.fps.n));
        this.fps.n = 0; this.fps.t = 0;
      }
    },

    /* minimap: scales the whole tilemap + unit dots into a small canvas. */
    minimap: function (mm, st, theme) {
      var ctx = mm.getContext("2d");
      mm.width = mm.clientWidth; mm.height = mm.clientHeight;
      var ts = st.tiles; if (!ts) return;
      var W = ts.w, H = ts.h;
      var kx = mm.width / W, ky = mm.height / H;
      ctx.fillStyle = theme.ui.minimapBg;
      ctx.fillRect(0, 0, mm.width, mm.height);
      var sx = Math.max(1, kx), sy = Math.max(1, ky);
      var vfog = ts._visFog || st.fog;
      for (var y = 0; y < H; y++) {
        for (var x = 0; x < W; x++) {
          var i = y * W + x;
          var f = vfog ? vfog[i] : 2;
          if (f === 0) continue;
          var mk = ts.mark ? ts.mark[i] : 0;
          var wt = ts._water ? ts._water[i] : 0;
          var rd = ts._roads ? ts._roads[i] : 0;
          ctx.fillStyle = mk === 2 ? theme.tiles.contested :
            wt === 2 ? (theme.tiles.waterDeep || theme.tiles.water) :
            wt === 1 ? theme.tiles.water :
            mk === 1 ? theme.tiles.plot :
            rd ? (theme.tiles.road || theme.tiles.plot) :
            theme.tiles[ts.data[i] % 10] || theme.tiles[0];
          ctx.fillRect(x * kx, y * ky, sx + 0.5, sy + 0.5);
          if (f === 1) {
            ctx.fillStyle = "rgba(0,0,0,0.5)";
            ctx.fillRect(x * kx, y * ky, sx + 0.5, sy + 0.5);
          }
          if (ts.tint && ts.tint[i]) {   // lane-ownership tint (#124)
            ctx.fillStyle = ts.tint[i];
            ctx.fillRect(x * kx, y * ky, sx + 0.5, sy + 0.5);
          }
          if (ts.breach && ts.breach[i] &&   // wall-breach glow (#133)
              (performance.now() % 900) < 450) {
            ctx.fillStyle = "rgba(248,81,73,0.55)";
            ctx.fillRect(x * kx, y * ky, sx + 0.5, sy + 0.5);
          }
        }
      }
      var self = this, mmf = st.mmFilter || "all";
      if (mmf === "all" || mmf === "bld") {
        (st.buildings || []).forEach(function (b) {
          ctx.fillStyle = "#c9b37e";
          ctx.fillRect(b.x / TILE * kx - 2, b.y / TILE * ky - 2, 4, 4);
        });
      }
      var now = performance.now();
      (st.pings || []).forEach(function (p) {
        var age = (now - p.t0) / 1000;
        if (age < 0 || age > 6) return;
        ctx.fillStyle = ({
          decision: "#ffd54a", fail: "#f85149", spawn: "#3fb950",
          contested: "#e3813f" })[p.kind] || "#e6f2e6";
        ctx.globalAlpha = (age % 0.8) < 0.4 ? 1 : 0.25; // blink
        ctx.beginPath();
        ctx.arc(p.x / TILE * kx, p.y / TILE * ky, 2.5, 0, 7);
        ctx.fill();
        ctx.globalAlpha = 1;
      });
      if (mmf === "all" || mmf === "units") {
        (st.units || []).forEach(function (u) {
          var big = u.kind === "hero";
          ctx.fillStyle = u.status_live === "failed" || u.gate_fail
            ? "#f85149" : big ? "#ffd54a" : "#9fb4c7";
          var r = big ? 2.6 : 1.4;
          ctx.beginPath();
          ctx.arc(u.x / TILE * kx, u.y / TILE * ky, r, 0, 7);
          ctx.fill();
        });
      }
      // viewport rectangle (or iso frustum diamond in Office mode, #164)
      ctx.strokeStyle = "#e6f2e6";
      if (!this.iso) {
        var v = this.view();
        ctx.strokeRect(v.x / TILE * kx, v.y / TILE * ky,
          v.w / TILE * kx, v.h / TILE * ky);
      } else if (this.cv) {
        var c0 = this.toWorld(0, 0),
            c1 = this.toWorld(this.cv.width, 0),
            c2 = this.toWorld(this.cv.width, this.cv.height),
            c3 = this.toWorld(0, this.cv.height);
        ctx.beginPath();
        ctx.moveTo(c0.x / TILE * kx, c0.y / TILE * ky);
        ctx.lineTo(c1.x / TILE * kx, c1.y / TILE * ky);
        ctx.lineTo(c2.x / TILE * kx, c2.y / TILE * ky);
        ctx.lineTo(c3.x / TILE * kx, c3.y / TILE * ky);
        ctx.closePath();
        ctx.stroke();
      }
    },

    mmToWorld: function (mm, st, mx, my) {
      var ts = st.tiles;
      return { x: mx / mm.width * ts.w * TILE,
               y: my / mm.height * ts.h * TILE };
    }
  };

  g.Engine = { TILE: TILE, hash: hash, create: function (cv) {
    return new Engine(cv); } };
})(window);
