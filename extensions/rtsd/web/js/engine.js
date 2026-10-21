/* engine.js - rtsd v2 canvas-2D renderer: tilemap, camera, fog, sprites.
   Zero deps, classic script (file:// safe). The engine owns no game state:
   App feeds it {tiles, fog, regions, units, buildings} every frame.
   World coords are pixels; one tile = TILE px at zoom 1. */
(function (g) {
  "use strict";

  var TILE = 32;
  var ZMIN = 0.35, ZMAX = 3.0;
  var PITCH = 0.74; // #170: 3D RTS camera tilt (cos ~42 deg foreshortening)

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
    /* hard map clamp: the view never shows outside-map space. When the
       view is larger than the map span on an axis (deep zoom-out or a
       small map) the map is centered on that axis instead of pinned at
       the origin, the standard clamp-to-map + center-align convention. */
    _clampAxis: function (c, lo, span, v) {
      if (v >= span) return lo + (span - v) / 2;
      return Math.max(lo, Math.min(lo + span - v, c));
    },
    clampCam: function () {
      if (!this.map) return;
      var mw = this.map.w * TILE, mh = this.map.h * TILE, v = this.view();
      if (this.iso) {          // iso plane spans x:[-mh, mw], y:[0,(mw+mh)/2]
        this.cam.x = this._clampAxis(this.cam.x, -mh, mw + mh, v.w);
        this.cam.y = this._clampAxis(this.cam.y, 0, (mw + mh) / 2, v.h);
        return;
      }
      this.cam.x = this._clampAxis(this.cam.x, 0, mw, v.w);
      this.cam.y = this._clampAxis(this.cam.y, -40, mh * PITCH + 40, v.h);
    },
    centerOn: function (wx, wy) {   // wx,wy are world px in both themes
      var v = this.view();
      var px = this.iso ? (wx - wy) : wx,
          py = this.iso ? (wx + wy) / 2 : wy * PITCH;
      this.cam.x = px - v.w / 2; this.cam.y = py - v.h / 2; this.clampCam();
    },
    panBy: function (dx, dy) {
      this.cam.x += dx; this.cam.y += dy; this.clampCam();
    },
    /* #134/#170: 3D RTS camera projection. Ground plane (wx, wy) is
       foreshortened by PITCH (or isometric diamond under office mode)
       and vertical height wz lifts upward in screen Y (-wz * 0.88 * z).
       toWorld() is the exact inverse on the ground plane (wz=0). */
    toWorld: function (sx, sy) {
      var vx = this.cam.x + sx / this.cam.zoom,
          vy = this.cam.y + sy / this.cam.zoom;
      if (!this.iso) return { x: vx, y: vy / PITCH };
      return { x: vy + vx / 2, y: vy - vx / 2 };
    },
    toScreen: function (wx, wy, wz) {
      var px = wx, py = wy * PITCH;
      if (this.iso) { px = wx - wy; py = (wx + wy) / 2; }
      return {
        x: (px - this.cam.x) * this.cam.zoom,
        y: (py - this.cam.y - (wz || 0) * 0.88) * this.cam.zoom
      };
    },

    // #170 3D Volumetric Geometry Primitives in World Space (wx, wy, wz)
    _box3D: function (ctx, wx, wy, wz, dx, dy, dz, cTop, cFront, cSide) {
      var hx = dx / 2, hy = dy / 2;
      var b0 = this.toScreen(wx - hx, wy - hy, wz),
          b1 = this.toScreen(wx + hx, wy - hy, wz),
          b2 = this.toScreen(wx + hx, wy + hy, wz),
          b3 = this.toScreen(wx - hx, wy + hy, wz);
      var t0 = this.toScreen(wx - hx, wy - hy, wz + dz),
          t1 = this.toScreen(wx + hx, wy - hy, wz + dz),
          t2 = this.toScreen(wx + hx, wy + hy, wz + dz),
          t3 = this.toScreen(wx - hx, wy + hy, wz + dz);
      // South / Front face
      ctx.fillStyle = cFront;
      ctx.beginPath();
      ctx.moveTo(b3.x, b3.y); ctx.lineTo(b2.x, b2.y);
      ctx.lineTo(t2.x, t2.y); ctx.lineTo(t3.x, t3.y);
      ctx.closePath(); ctx.fill();
      ctx.strokeStyle = "rgba(0,0,0,0.35)"; ctx.stroke();
      // East / Right face (visible in iso or 3D bevel)
      if (cSide) {
        ctx.fillStyle = cSide;
        ctx.beginPath();
        ctx.moveTo(b2.x, b2.y); ctx.lineTo(b1.x, b1.y);
        ctx.lineTo(t1.x, t1.y); ctx.lineTo(t2.x, t2.y);
        ctx.closePath(); ctx.fill();
      }
      // Top face (wz + dz)
      ctx.fillStyle = cTop;
      ctx.beginPath();
      ctx.moveTo(t0.x, t0.y); ctx.lineTo(t1.x, t1.y);
      ctx.lineTo(t2.x, t2.y); ctx.lineTo(t3.x, t3.y);
      ctx.closePath(); ctx.fill();
      ctx.strokeStyle = "rgba(255,255,255,0.12)"; ctx.stroke();
    },

    _cyl3D: function (ctx, wx, wy, wz, rad, dz, cHi, cMid, cDark, cTop) {
      var z = this.cam.zoom;
      var sb = this.toScreen(wx, wy, wz),
          st = this.toScreen(wx, wy, wz + dz);
      var rx = rad * z, ry = rad * PITCH * 0.65 * z;
      var grad = ctx.createLinearGradient(sb.x - rx, 0, sb.x + rx, 0);
      grad.addColorStop(0.0, cMid);
      grad.addColorStop(0.25, cHi);
      grad.addColorStop(0.65, cMid);
      grad.addColorStop(1.0, cDark);
      ctx.fillStyle = grad;
      ctx.beginPath();
      ctx.ellipse(sb.x, sb.y, rx, ry, 0, 0, Math.PI);
      ctx.lineTo(st.x - rx, st.y);
      ctx.ellipse(st.x, st.y, rx, ry, 0, Math.PI, 0, true);
      ctx.closePath();
      ctx.fill();
      ctx.strokeStyle = "rgba(0,0,0,0.32)";
      ctx.stroke();
      // Top cap at wz + dz
      ctx.fillStyle = cTop || cHi;
      ctx.beginPath();
      ctx.ellipse(st.x, st.y, rx, ry, 0, 0, 7);
      ctx.fill();
      ctx.stroke();
    },

    _cone3D: function (ctx, wx, wy, wz, rad, dz, cHi, cDark) {
      var z = this.cam.zoom;
      var sb = this.toScreen(wx, wy, wz),
          pk = this.toScreen(wx, wy, wz + dz);
      var rx = rad * z, ry = rad * PITCH * 0.65 * z;
      var grad = ctx.createLinearGradient(sb.x - rx, 0, sb.x + rx, 0);
      grad.addColorStop(0, cHi);
      grad.addColorStop(0.55, cHi);
      grad.addColorStop(1, cDark);
      ctx.fillStyle = grad;
      ctx.beginPath();
      ctx.moveTo(pk.x, pk.y);
      ctx.lineTo(sb.x + rx, sb.y);
      ctx.ellipse(sb.x, sb.y, rx, ry, 0, 0, Math.PI);
      ctx.closePath();
      ctx.fill();
      ctx.strokeStyle = "rgba(0,0,0,0.32)";
      ctx.stroke();
    },

    _roofPrism3D: function (ctx, wx, wy, wz, dx, dy, dz, colW, colE, trim) {
      var hx = dx / 2, hy = dy / 2;
      var b0 = this.toScreen(wx - hx, wy - hy, wz),
          b1 = this.toScreen(wx + hx, wy - hy, wz),
          b2 = this.toScreen(wx + hx, wy + hy, wz),
          b3 = this.toScreen(wx - hx, wy + hy, wz);
      var rN = this.toScreen(wx, wy - hy + 2, wz + dz),
          rS = this.toScreen(wx, wy + hy - 2, wz + dz);
      // West sunlit roof slope
      ctx.fillStyle = colW;
      ctx.beginPath();
      ctx.moveTo(b0.x, b0.y); ctx.lineTo(rN.x, rN.y);
      ctx.lineTo(rS.x, rS.y); ctx.lineTo(b3.x, b3.y);
      ctx.closePath(); ctx.fill();
      // East shadowed roof slope
      ctx.fillStyle = colE;
      ctx.beginPath();
      ctx.moveTo(rN.x, rN.y); ctx.lineTo(b1.x, b1.y);
      ctx.lineTo(b2.x, b2.y); ctx.lineTo(rS.x, rS.y);
      ctx.closePath(); ctx.fill();
      // Front South gable triangle
      ctx.fillStyle = colW;
      ctx.beginPath();
      ctx.moveTo(b3.x, b3.y); ctx.lineTo(rS.x, rS.y);
      ctx.lineTo(b2.x, b2.y); ctx.closePath(); ctx.fill();
      ctx.strokeStyle = trim || "#d4a72c";
      ctx.lineWidth = 1.4;
      ctx.stroke();
      ctx.lineWidth = 1;
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
            py = E.iso ? (p.x + p.y) / 2 : p.y * PITCH;
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
      this.clampCam();         // resize/zoom may leave the view off-map
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

    // battlefield: blits 3D PITCH-foreshortened splatted terrain + 3D plateaus,
    // sunken riverbanks, 3D arched bridges, and Gerstner water waves (#170)
    _flatTiles: function (ctx, st, theme, z, v, now, wind) {
      var ts = st.tiles, W = ts.w, H = ts.h;
      var fog = st.visFog || st.fog;
      var tyPitch = TILE * PITCH;
      var x0 = Math.max(0, Math.floor(v.x / TILE) - 1),
          y0 = Math.max(0, Math.floor(v.y / tyPitch) - 1),
          x1 = Math.min(W, Math.ceil((v.x + v.w) / TILE) + 1),
          y1 = Math.min(H, Math.ceil((v.y + v.h) / tyPitch) + 2);
      var px = TILE * z, py = tyPitch * z;
      var tcv = this._ensureTerrainCanvas(ts, theme);
      if (tcv) {
        var sx0 = x0 * TILE, sy0 = y0 * TILE,
            sw0 = (x1 - x0) * TILE, sh0 = (y1 - y0) * TILE;
        if (sw0 > 0 && sh0 > 0) {
          ctx.drawImage(tcv, sx0, sy0, sw0, sh0,
                        (sx0 - v.x) * z, (y0 * tyPitch - v.y) * z,
                        sw0 * z, (y1 - y0) * py);
        }
      }
      for (var ty = y0; ty < y1; ty++) {
        for (var tx = x0; tx < x1; tx++) {
          var i = ty * W + tx;
          var f = fog ? fog[i] : 2;
          var sx = (tx * TILE - v.x) * z,
              sy = (ty * tyPitch - v.y) * z;
          if (f === 0) {
            ctx.fillStyle = (tx + ty) % 2 ? "#0b140d" : "#09110b";
            ctx.fillRect(sx, sy, px + 1, py + 1);
            continue;
          }
          if (!tcv) {
            ctx.fillStyle = this._tileStyle(ctx, st, theme, i);
            ctx.fillRect(sx, sy, px + 1, py + 1);
          } else if (ts.mark && ts.mark[i] === 2) {
            ctx.fillStyle = "rgba(180,45,45,0.45)";
            ctx.fillRect(sx, sy, px, py);
          }
          var wt = ts._water ? ts._water[i] : 0;
          var rd = ts._roads ? ts._roads[i] : 0;
          // #170 3D Elevated Citadel Plateau cliff wall on South border
          if (rd === 2 && ty + 1 < H && (!ts._roads || ts._roads[i + W] !== 2)) {
            ctx.fillStyle = "#4a4338";
            ctx.fillRect(sx, sy + py - 5 * z, px + 1, 6 * z);
            ctx.fillStyle = "#8c8270";
            ctx.fillRect(sx, sy + py - 6 * z, px + 1, 1.8 * z);
          }
          // #170 3D Sunken Riverbank ledge on North border + Gerstner waves
          if ((wt === 1 || wt === 2) && z > 0.45) {
            if (ty > 0 && (!ts._water || !ts._water[i - W])) {
              ctx.fillStyle = "#5c4d38";
              ctx.fillRect(sx, sy, px + 1, 4.5 * z);
            }
            var wph1 = (now / 360) * wind.str + tx * wind.ux * 1.4 +
                       ty * wind.uy * 1.4;
            var wph2 = (now / 520) * wind.str - tx * wind.uy * 0.9 +
                       ty * wind.ux * 0.9;
            var eta = 0.6 * Math.sin(wph1) + 0.4 * Math.cos(wph2);
            ctx.strokeStyle = wt === 2
              ? "rgba(130,210,255,0.38)" : "rgba(195,240,255,0.52)";
            ctx.lineWidth = Math.max(1, 1.3 * z);
            ctx.beginPath();
            var wx0 = sx + (0.18 + 0.14 * eta) * px,
                wy0 = sy + (0.42 + 0.12 * Math.cos(wph1)) * py;
            ctx.moveTo(wx0, wy0);
            ctx.quadraticCurveTo(wx0 + px * 0.28, wy0 - 2.5 * z * eta,
                                 wx0 + px * 0.56, wy0);
            ctx.stroke();
            if (eta > 0.62) {
              ctx.fillStyle = "rgba(255,250,220,0.68)";
              ctx.fillRect(wx0 + px * 0.2, wy0 - 1.5 * z, 2.5 * z, 1.5 * z);
            }
            if (wt === 1) {
              var foam = 0.22 + 0.18 * Math.sin(now / 400 + tx + ty);
              ctx.strokeStyle = "rgba(235,248,255," + foam.toFixed(2) + ")";
              ctx.beginPath();
              ctx.ellipse(sx + px * 0.5, sy + py * 0.5,
                          px * 0.44, py * 0.44, 0, 0, 7);
              ctx.stroke();
            }
            ctx.lineWidth = 1;
          } else if (wt === 3 && z > 0.45) {
            // #170 3D Arched Timber & Stone Bridge with 3D piers + rails
            var archZ = 4.5 * z;
            ctx.fillStyle = "rgba(0,0,0,0.45)";
            ctx.fillRect(sx + 2 * z, sy + 2 * z, px, py);
            // Stone side piers
            ctx.fillStyle = "#595449";
            ctx.fillRect(sx, sy - archZ + py, px, archZ);
            // Arched wooden deck
            ctx.fillStyle = "#8a623c";
            ctx.fillRect(sx, sy - archZ, px, py);
            ctx.strokeStyle = "#4d3319";
            for (var bp = 1; bp < 4; bp++) {
              ctx.beginPath();
              ctx.moveTo(sx + bp * px / 4, sy - archZ);
              ctx.lineTo(sx + bp * px / 4, sy - archZ + py);
              ctx.stroke();
            }
            // 3D Handrail posts + top rail
            ctx.fillStyle = "#b88b58";
            ctx.fillRect(sx, sy - archZ - 3 * z, px, 2.5 * z);
            ctx.fillRect(sx, sy - archZ + py - 2.5 * z, px, 2.5 * z);
          } else if (z > 0.55 && ((tx * 7 + ty * 13) % 5 === 0)) {
            var sway = Math.sin(now / 520 + tx * 0.7 + ty * 0.5) *
                       wind.vx * 2.4 * z;
            ctx.strokeStyle = "rgba(96,168,78,0.48)";
            ctx.beginPath();
            ctx.moveTo(sx + px * 0.5, sy + py * 0.7);
            ctx.lineTo(sx + px * 0.5 + sway, sy + py * 0.25);
            ctx.stroke();
          }
          if (ts.tileRegion && tx + 1 < W &&
              ts.tileRegion[i] !== ts.tileRegion[i + 1]) {
            ctx.fillStyle = "rgba(255,213,74,0.14)";
            ctx.fillRect(sx + px - 1, sy, 2, py);
          }
          if (f === 1) {
            ctx.fillStyle = "rgba(8,14,10,0.28)";
            ctx.fillRect(sx, sy, px + 1, py + 1);
          }
          if (ts.breach && ts.breach[i]) {
            ctx.fillStyle = "rgba(248,81,73," +
              (0.16 + 0.10 * Math.sin(now / 280)).toFixed(3) + ")";
            ctx.fillRect(sx, sy, px + 1, py + 1);
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
      // 3. 3D Multi-Tier Conical/Spherical Swaying Forest Trees (#170)
      (ts._trees || []).forEach(function (tr) {
        var f = fog ? fog[tr.ty * W + tr.tx] : 2;
        if (f === 0) return;
        var s = self.toScreen(tr.x, tr.y, 0);
        if (s.x < -44 || s.y < -44 || s.x > cv.width + 44 ||
            s.y > cv.height + 44) return;
        var sc = tr.scale;
        var swX = (Math.sin(now / 620 + (tr.seed % 50)) * 0.6 + 0.7) *
                  wind.vx * 3.8 * sc;
        var swY = (Math.cos(now / 740 + (tr.seed % 50)) * 0.5 + 0.5) *
                  wind.vy * 2.2 * sc;
        ctx.globalAlpha = f === 1 ? 0.55 : 0.96;
        // 3D Projected Ground Cast Shadow
        ctx.fillStyle = "rgba(0,0,0,0.36)";
        ctx.beginPath();
        ctx.ellipse(s.x + 6 * sc * z, s.y + 2 * sc * z,
                    10 * sc * z, 4.5 * sc * z, 0.25, 0, 7);
        ctx.fill();
        // 3D Cylindrical Trunk (wz: 0 -> 10)
        self._cyl3D(ctx, tr.x, tr.y, 0, 2.3 * sc, 10 * sc,
                    "#734f34", "#4d3422", "#2b1c11", "#4d3422");
        var cHi = tr.kind === "pine" ? "#3b8554" :
                  tr.kind === "goldleaf" ? "#e0b03e" :
                  tr.kind === "willow" ? "#4ca179" : "#49964f";
        var cDark = tr.kind === "pine" ? "#14331f" :
                    tr.kind === "goldleaf" ? "#634814" :
                    tr.kind === "willow" ? "#1c4230" : "#1a401f";
        // 3 Stacked 3D Conical / Spherical Canopy Tiers rising to wz = 34
        self._cone3D(ctx, tr.x + swX * 0.35, tr.y + swY * 0.35,
                     7 * sc, 9.5 * sc, 12 * sc, cHi, cDark);
        self._cone3D(ctx, tr.x + swX * 0.75, tr.y + swY * 0.75,
                     14 * sc, 7.6 * sc, 11 * sc, cHi, cDark);
        self._cone3D(ctx, tr.x + swX * 1.15, tr.y + swY * 1.15,
                     21 * sc, 5.4 * sc, 10 * sc, cHi, cDark);
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

    /* #170 3D Volumetric Multi-Face Building Renderer: constructs all 11
       structures from real 3D (wx, wy, wz) boxes, cylinders, cones,
       pitched roofs, and animated 3D attachments. */
    _drawBuilding3D: function (ctx, b, theme, z, now, wind, pal) {
      var bid = b.bid || "vault", wx = b.x, wy = b.y, i;
      var s0 = this.toScreen(wx, wy, 0);
      // 0. 3D Directional Ground Cast Shadow + AO Contact Footprint
      ctx.fillStyle = "rgba(0,0,0,0.42)";
      ctx.beginPath();
      ctx.ellipse(s0.x + 8 * z, s0.y + 4 * z, 28 * z, 15 * z, 0.2, 0, 7);
      ctx.fill();
      // 3D Stone Foundation Plinth (wz: 0 -> 5)
      this._box3D(ctx, wx, wy, 0, 38, 32, 5, "#787163", "#595449", "#3d3930");

      if (bid === "town-hall") {
        // 3D Citadel Keep: central Great Hall + 4 corner 3D cylindrical towers
        this._box3D(ctx, wx, wy, 5, 24, 20, 20, "#949aa6", "#7d8490", "#525863");
        this._roofPrism3D(ctx, wx, wy, 25, 26, 22, 14, "#386ec2", "#1c3b6e", "#ffd54a");
        var tOff = [[-13, -10], [13, -10], [-13, 10], [13, 10]];
        for (i = 0; i < 4; i++) {
          var tx = wx + tOff[i][0], ty = wy + tOff[i][1];
          this._cyl3D(ctx, tx, ty, 5, 5.2, 24, "#b8bfc9", "#7d8490", "#454a52", "#949aa6");
          this._cone3D(ctx, tx, ty, 29, 6.2, 12, "#3b6ebf", "#17325c");
        }
        // 3D Gatehouse Arch on South facade
        var gs = this.toScreen(wx, wy + 10, 5);
        ctx.fillStyle = "#2b1b0e";
        ctx.beginPath();
        ctx.arc(gs.x, gs.y - 6 * z, 5.5 * z, Math.PI, 0);
        ctx.lineTo(gs.x + 5.5 * z, gs.y); ctx.lineTo(gs.x - 5.5 * z, gs.y);
        ctx.closePath(); ctx.fill();
        ctx.strokeStyle = "#ffd54a"; ctx.stroke();
      } else if (bid === "barracks") {
        // 3D Garrison Fortress + crenellated battlements + crimson roof
        this._box3D(ctx, wx, wy, 5, 30, 22, 18, "#8a9099", "#6e747d", "#484d54");
        this._roofPrism3D(ctx, wx, wy, 23, 28, 20, 12, "#b03a30", "#661e18", "#d4a72c");
        for (i = -12; i <= 12; i += 8) {
          this._box3D(ctx, wx + i, wy + 10, 23, 4, 3, 4, "#9aa0aa", "#7d8490", "#525863");
        }
      } else if (bid === "tavern") {
        // 3D Two-story Half-Timbered Inn + tall 3D stone chimney
        this._box3D(ctx, wx, wy, 5, 24, 18, 10, "#9e8c70", "#7d6e56", "#544938");
        this._box3D(ctx, wx, wy, 15, 27, 20, 10, "#dec79e", "#c9b289", "#8c7a5b");
        this._roofPrism3D(ctx, wx, wy, 25, 29, 22, 13, "#9e6832", "#593818", "#d4a72c");
        this._box3D(ctx, wx + 10, wy - 5, 5, 5, 5, 31, "#8a7968", "#6e5f50", "#42382e");
        this._cyl3D(ctx, wx - 11, wy + 11, 5, 3.2, 6, "#a67038", "#6e4720", "#38220d");
      } else if (bid === "library") {
        // 3D Arcane Sanctum: octagonal marble tower + 3D dome + 3-axis gyroscope rings
        this._cyl3D(ctx, wx, wy, 5, 12, 22, "#a5b4cc", "#6b7a94", "#3b4454", "#8d9bb5");
        this._cone3D(ctx, wx, wy, 27, 13, 13, "#5ec2f7", "#16425b");
        var topS = this.toScreen(wx, wy, 44);
        var ang = now / 480;
        ctx.strokeStyle = "#ffd54a"; ctx.lineWidth = Math.max(1.2, 1.6 * z);
        ctx.beginPath();
        ctx.ellipse(topS.x, topS.y, 10 * z, 4.2 * z, Math.sin(ang) * 0.6, 0, 7);
        ctx.stroke();
        ctx.strokeStyle = "#38bdf8";
        ctx.beginPath();
        ctx.ellipse(topS.x, topS.y, 8 * z, 3.5 * z, -Math.cos(ang) * 0.7, 0, 7);
        ctx.stroke();
        ctx.lineWidth = 1;
      } else if (bid === "watchtower") {
        // 3D Guard Spire: tall cylindrical shaft + overhanging timber gallery + spire
        this._cyl3D(ctx, wx, wy, 5, 6.8, 30, "#a3ab9c", "#6c7366", "#393d35", "#8a9184");
        this._box3D(ctx, wx, wy, 33, 18, 18, 6, "#785534", "#5c3f24", "#3b2715");
        this._cone3D(ctx, wx, wy, 39, 10.5, 14, "#486999", "#1d2d45");
      } else if (bid === "runeforge") {
        // 3D Blacksmith Foundry + smokestack + animated 3D trip-hammer on anvil
        this._box3D(ctx, wx - 3, wy, 5, 24, 18, 16, "#6e6763", "#4a4542", "#292523");
        this._roofPrism3D(ctx, wx - 3, wy, 21, 26, 20, 10, "#803d28", "#421d12", "#c99a49");
        this._cyl3D(ctx, wx - 9, wy - 4, 5, 4.2, 28, "#594842", "#382d29", "#1f1816");
        // 3D Anvil + Trip-hammer slamming in +Z
        this._box3D(ctx, wx + 11, wy + 6, 5, 6, 4, 5, "#d0d7de", "#8b949e", "#484f58");
        var hLift = Math.abs(Math.sin(now / 180)) * 7;
        this._box3D(ctx, wx + 11, wy + 6, 10 + hLift, 5, 3.5, 3.5, "#ffd54a", "#b8860b", "#7a5905");
      } else if (bid === "portal") {
        // 3D Waygate: twin 3D carved obelisks + lintel arch + upright 3D vortex
        this._box3D(ctx, wx - 11, wy, 5, 6, 6, 28, "#7a6599", "#463859", "#241b30");
        this._box3D(ctx, wx + 11, wy, 5, 6, 6, 28, "#7a6599", "#463859", "#241b30");
        this._box3D(ctx, wx, wy, 31, 28, 8, 5, "#8b74ad", "#5a4873", "#312542");
        var vs = this.toScreen(wx, wy, 18);
        var pg = ctx.createRadialGradient(vs.x, vs.y, 1, vs.x, vs.y, 12 * z);
        pg.addColorStop(0, "#ffffff");
        pg.addColorStop(0.4, "#e879f9");
        pg.addColorStop(0.8, "#6d28d9");
        pg.addColorStop(1, "rgba(30,27,75,0)");
        ctx.fillStyle = pg;
        ctx.beginPath();
        ctx.ellipse(vs.x, vs.y, 9 * z, 13 * z, 0, 0, 7);
        ctx.fill();
      } else if (bid === "marketplace") {
        // 3D Market Pavilion with 3D columns + striped awning roof + crates
        this._box3D(ctx, wx, wy, 5, 28, 20, 12, "#8a623c", "#6e4e2e", "#47311b");
        this._roofPrism3D(ctx, wx, wy, 17, 30, 22, 9, "#cf3636", "#8c2020", "#f5ebd6");
        this._box3D(ctx, wx - 8, wy + 11, 5, 6, 5, 5, "#e3b341", "#b88b28", "#7a5b16");
        this._box3D(ctx, wx + 8, wy + 11, 5, 6, 5, 5, "#e3b341", "#b88b28", "#7a5b16");
      } else if (bid === "altar") {
        // 3D Stepped Ziggurat Altar of Kings + 4 marble pillars + 3D winged statue
        this._box3D(ctx, wx, wy, 5, 30, 24, 5, "#b8b2c4", "#8a8496", "#575261");
        this._box3D(ctx, wx, wy, 10, 22, 18, 5, "#ccc6d9", "#9b95a8", "#656070");
        this._cyl3D(ctx, wx, wy, 15, 4.2, 16, "#fff3b0", "#d4a72c", "#7a5c0c", "#fff3b0");
        var as = this.toScreen(wx, wy, 32);
        ctx.fillStyle = "#ffd54a";
        ctx.beginPath();
        ctx.moveTo(as.x, as.y);
        ctx.lineTo(as.x - 13 * z, as.y - 8 * z);
        ctx.lineTo(as.x - 6 * z, as.y + 4 * z);
        ctx.moveTo(as.x, as.y);
        ctx.lineTo(as.x + 13 * z, as.y - 8 * z);
        ctx.lineTo(as.x + 6 * z, as.y + 4 * z);
        ctx.fill();
      } else {
        // 3D Vault & Trophy Hall Pantheon with cylindrical columns + golden pediment
        this._box3D(ctx, wx, wy, 5, 28, 20, 18, "#8a9099", "#5c6169", "#3b3f45");
        for (i = -10; i <= 10; i += 6.6) {
          this._cyl3D(ctx, wx + i, wy + 10, 5, 1.8, 18, "#f0f4f8", "#9ca3af", "#4b5563");
        }
        this._roofPrism3D(ctx, wx, wy, 23, 30, 22, 11, "#d4a72c", "#7d5f14", "#fff3b0");
      }
      // Animated banners, smoke, sparks, braziers, beacon in 3D space
      var topP = this.toScreen(wx, wy, 36);
      this._drawBuildingAnim(ctx, b, topP, 48 * z, 24 * z, z, now, wind, pal);
    },
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

    /* #170 14-Joint 3D Articulated Skeletal Rig & 8 Keyframed 3D Animations:
       Every unit/hero has a smooth 3D facing angle `u._yaw` (lerped toward
       its movement/target direction), local 3D frame (Forward F, Right R,
       Up Z), Z-sorted 3D limbs (Pelvis, Torso, Head/Helm, Shoulders, Elbows,
       Hands with 3D Shield & Weapon, Hips, Knees, Boots, 4-node 3D Cape),
       and 8 real 3D skeletal animation clips. */
    _drawUnitLive: function (ctx, u, s, sz, dy, ent, z, now, wind, pal, all) {
      var self = this, ph = hash(String(u.id));
      var isHero = u.kind === "hero";
      var sc = (u.kind === "minion" ? 0.68 : u.kind === "worker" ? 0.56 : 1.0);
      var wx = u.x, wy = u.y;

      // 1. Smooth 3D Facing Yaw (turns toward movement vector or target)
      var tgtYaw = typeof u._yaw === "number" ? u._yaw : 1.15;
      if (u.moving || u.acting) {
        var mdx = (u.tx || wx) - wx, mdy = (u.ty || wy) - wy;
        if (mdx * mdx + mdy * mdy > 1) tgtYaw = Math.atan2(mdy, mdx);
      } else {
        var fidgetSlot = Math.floor((now / 2600 + (ph % 19))) % 8;
        var subT = ((now / 2600 + (ph % 19)) % 1);
        if (fidgetSlot === 2) {
          tgtYaw = 1.15 + Math.sin(subT * 6.283) * 0.65; // Stand-2 look-around
        } else if (fidgetSlot === 5) {
          for (var ai = 0; ai < all.length; ai++) {
            var o = all[ai];
            if (o.id !== u.id && Math.hypot(o.x - wx, o.y - wy) < TILE * 3.2) {
              tgtYaw = Math.atan2(o.y - wy, o.x - wx);
              break;
            }
          }
        } else {
          tgtYaw = 1.15 + Math.sin(now / 1900 + ph) * 0.18;
        }
      }
      var curYaw = typeof u._yaw === "number" ? u._yaw : tgtYaw;
      var dYaw = ((tgtYaw - curYaw + Math.PI * 3) % (Math.PI * 2)) - Math.PI;
      u._yaw = curYaw + dYaw * 0.22;
      var cy = Math.cos(u._yaw), sy = Math.sin(u._yaw);
      // Local 3D character space (f=forward, r=right, up=+wz) -> screen
      var J = function (f, r, up) {
        return self.toScreen(
          wx + (f * cy - r * sy) * sc,
          wy + (f * sy + r * cy) * sc,
          up * sc
        );
      };
      var limb = function (p0, p1, rad, col) {
        ctx.strokeStyle = col;
        ctx.lineWidth = Math.max(1.4, rad * sc * z);
        ctx.lineCap = "round";
        ctx.beginPath();
        ctx.moveTo(p0.x, p0.y); ctx.lineTo(p1.x, p1.y);
        ctx.stroke();
      };

      // 2. Ground Shadow + WC3 Hero Glow + Rotating 3D Aura Ring
      var g0 = J(0, 0, 0);
      ctx.fillStyle = "rgba(0,0,0,0.40)";
      ctx.beginPath();
      ctx.ellipse(g0.x + 3 * sc * z, g0.y + 1.5 * sc * z,
                  9.5 * sc * z, 5 * sc * z, 0.2, 0, 7);
      ctx.fill();
      if (isHero) {
        var gRad = 18 * sc * z;
        var grad = ctx.createRadialGradient(g0.x, g0.y, 2, g0.x, g0.y, gRad);
        grad.addColorStop(0, "rgba(255,213,74,0.42)");
        grad.addColorStop(1, "rgba(255,213,74,0)");
        ctx.fillStyle = grad;
        ctx.beginPath(); ctx.arc(g0.x, g0.y, gRad, 0, 7); ctx.fill();
        if (z > 0.5) {
          var aAng = now / 850 + (ph % 10);
          ctx.strokeStyle = ent.trim || "#ffd54a";
          ctx.globalAlpha = 0.52;
          ctx.setLineDash([3 * z, 3 * z]);
          ctx.beginPath();
          ctx.ellipse(g0.x, g0.y, 13 * sc * z, 13 * PITCH * sc * z, 0, 0, 7);
          ctx.stroke();
          ctx.setLineDash([]);
          ctx.globalAlpha = 1;
        }
      }

      // 3. Determine Active 3D Animation Clip & Joint Poses
      var clip = u.moving ? "walk" :
                 (u.status_live === "running" || u.acting) ? "attack" :
                 (["idle", "idle", "look", "flourish", "idle", "social",
                   "wave", "dance"][Math.floor((now / 2600 + (ph % 19))) % 8]);
      var wPh = now / 82 + ph;
      var strideF = clip === "walk" ? Math.sin(wPh) * 6.2 :
                    clip === "dance" ? Math.sin(now / 140 + ph) * 3.5 : 0;
      var kneeLiftL = clip === "walk" ? Math.max(0, -Math.cos(wPh)) * 5.2 :
                      clip === "dance" ? Math.max(0, Math.sin(now / 140)) * 4.5 : 0;
      var kneeLiftR = clip === "walk" ? Math.max(0, Math.cos(wPh)) * 5.2 :
                      clip === "dance" ? Math.max(0, -Math.sin(now / 140)) * 4.5 : 0;
      var jumpZ = (clip === "wave" || clip === "dance")
        ? Math.abs(Math.sin(now / 160 + ph)) * 4.5 : 0;
      var pelvZ = 8.5 + (clip === "walk" ? -Math.abs(Math.cos(wPh)) * 1.6 :
                         Math.sin(now / 420 + ph) * 0.7) + jumpZ;
      var leanF = clip === "walk" ? 2.2 : clip === "attack" ? 3.2 * Math.sin(now / 95 + ph) : 0;

      // 4. 4-Node 3D Verlet Cape (drawn behind torso when facing south/camera)
      var drawCape = function () {
        if (!isHero && ent.arch !== "martial" && ent.arch !== "caster" &&
            ent.arch !== "commander") return;
        var c0L = J(-2, -4.5, pelvZ + 8), c0R = J(-2, 4.5, pelvZ + 8);
        var billow = (u.moving ? -7.5 : -3.5) + Math.sin(now / 130 + ph) * 2.4;
        var wLat = (wind.vx * -sy + wind.vy * cy) * 2.5;
        var cMidL = J(billow * 0.55, -5.2 + wLat * 0.5, pelvZ + 3),
            cMidR = J(billow * 0.55, 5.2 + wLat * 0.5, pelvZ + 3);
        var cBotL = J(billow, -6.2 + wLat, 2 + jumpZ * 0.5),
            cBotR = J(billow, 6.2 + wLat, 2 + jumpZ * 0.5);
        ctx.fillStyle = ent.dark || "#1b325f";
        ctx.beginPath();
        ctx.moveTo(c0L.x, c0L.y); ctx.lineTo(c0R.x, c0R.y);
        ctx.lineTo(cMidR.x, cMidR.y); ctx.lineTo(cBotR.x, cBotR.y);
        ctx.lineTo(cBotL.x, cBotL.y); ctx.lineTo(cMidL.x, cMidL.y);
        ctx.closePath(); ctx.fill();
        ctx.strokeStyle = ent.trim || "#ffd54a";
        ctx.lineWidth = Math.max(0.8, 1.1 * z); ctx.stroke();
      };
      if (sy >= -0.2) drawCape();

      // 5. Articulated 3D Legs (Hip -> Knee -> Ankle/Boot)
      var hipL = J(0, -2.8, pelvZ), hipR = J(0, 2.8, pelvZ);
      var kneeL = J(strideF * 0.65 + 1.2, -3.0, 4.5 + kneeLiftL * 0.6 + jumpZ * 0.5),
          kneeR = J(-strideF * 0.65 + 1.2, 3.0, 4.5 + kneeLiftR * 0.6 + jumpZ * 0.5);
      var footL = J(strideF, -3.0, kneeLiftL + jumpZ),
          footR = J(-strideF, 3.0, kneeLiftR + jumpZ);
      var legOrder = (cy * -1 + sy * 0 > 0) ? ["L", "R"] : ["R", "L"];
      legOrder.forEach(function (side) {
        var hp = side === "L" ? hipL : hipR,
            kn = side === "L" ? kneeL : kneeR,
            ft = side === "L" ? footL : footR;
        limb(hp, kn, 3.2, ent.dark || "#2b2623");
        limb(kn, ft, 2.8, ent.bg || "#48525c");
        // 3D Armored Boot
        var btTip = J((side === "L" ? strideF : -strideF) + 2.4,
                      side === "L" ? -3.0 : 3.0,
                      (side === "L" ? kneeLiftL : kneeLiftR) + jumpZ);
        limb(ft, btTip, 3.0, "#3d2916");
      });

      // 6. 3D Tapered Armored Torso / Cuirass & Belt
      var torsoX = wx + leanF * cy * sc, torsoY = wy + leanF * sy * sc;
      this._cyl3D(ctx, torsoX, torsoY, pelvZ * sc, 5.2 * sc, 8.8 * sc,
                  ent.trim || "#e2e8f0", ent.bg || "#3b5bdb",
                  ent.dark || "#182447", ent.bg || "#3b5bdb");
      // Golden belt + tabard
      var beltP = J(leanF + 2.2, 0, pelvZ + 0.8),
          tabP = J(leanF + 2.6 + Math.sin(wPh) * 1.2, 0, pelvZ - 3.5);
      limb(beltP, tabP, 2.6, ent.trim || "#ffd54a");

      // 7. Articulated 3D Shoulders, Arms, Shield & Weapons
      var shL = J(leanF, -5.8, pelvZ + 7.5),
          shR = J(leanF, 5.8, pelvZ + 7.5);
      var armSwing = clip === "walk" ? -strideF * 0.75 : 0;
      var elbL = J(leanF + 2.5 - armSwing * 0.4, -7.2, pelvZ + 4.2),
          handL = J(leanF + 5.2 - armSwing * 0.7, -6.2, pelvZ + 3.0);
      var rF = leanF + 3.5 + armSwing * 0.8,
          rR = 6.8,
          rZ = pelvZ + 3.8;
      if (clip === "attack") {
        var slash = Math.sin(now / 85 + ph);
        rF = leanF + 6.5 + slash * 5.5;
        rR = 5.0 - slash * 6.5;
        rZ = pelvZ + 8.5 - slash * 6.0;
      } else if (clip === "flourish" || clip === "wave") {
        rF = leanF + 2.0;
        rR = 7.5 + Math.sin(now / 110) * 3.0;
        rZ = pelvZ + 14.5;
      } else if (clip === "dance") {
        rF = leanF + 3.0;
        rR = 7.8;
        rZ = pelvZ + 12.0 + Math.sin(now / 120) * 3.5;
      }
      var elbR = J((leanF + rF) * 0.5, 6.8, (pelvZ + 7.5 + rZ) * 0.5),
          handR = J(rF, rR, rZ);

      var drawArmL = function () {
        // Left Pauldron + Arm + 3D Shield / Off-hand Tome
        ctx.fillStyle = ent.bg || "#3b5bdb";
        ctx.beginPath(); ctx.arc(shL.x, shL.y, 3.6 * sc * z, 0, 7); ctx.fill();
        ctx.strokeStyle = ent.trim || "#ffd54a"; ctx.lineWidth = 1.2; ctx.stroke();
        limb(shL, elbL, 2.6, ent.bg || "#3b5bdb");
        limb(elbL, handL, 2.3, "#e8be8a");
        if (ent.arch === "martial" || ent.arch === "commander") {
          // 3D Kite Shield oriented on left forearm
          var shTop = J(leanF + 4.8 - armSwing * 0.5, -7.8, pelvZ + 7.2),
              shBot = J(leanF + 4.8 - armSwing * 0.5, -7.8, pelvZ - 1.2),
              shIn = J(leanF + 6.8 - armSwing * 0.5, -4.8, pelvZ + 3.5),
              shOut = J(leanF + 2.5 - armSwing * 0.5, -9.2, pelvZ + 3.5);
          ctx.fillStyle = ent.bg || "#254e8a";
          ctx.beginPath();
          ctx.moveTo(shTop.x, shTop.y); ctx.lineTo(shIn.x, shIn.y);
          ctx.lineTo(shBot.x, shBot.y); ctx.lineTo(shOut.x, shOut.y);
          ctx.closePath(); ctx.fill();
          ctx.strokeStyle = "#ffd54a"; ctx.lineWidth = 1.5; ctx.stroke();
        }
      };

      var drawArmR = function () {
        // Right Pauldron + Arm + 3D Weapon (Broadsword / Staff / Bow / Hammer)
        ctx.fillStyle = ent.bg || "#3b5bdb";
        ctx.beginPath(); ctx.arc(shR.x, shR.y, 3.6 * sc * z, 0, 7); ctx.fill();
        ctx.strokeStyle = ent.trim || "#ffd54a"; ctx.lineWidth = 1.2; ctx.stroke();
        limb(shR, elbR, 2.6, ent.bg || "#3b5bdb");
        limb(elbR, handR, 2.3, "#e8be8a");
        var wpTip = J(rF + (clip === "attack" ? 9.5 : 5.5),
                      rR - (clip === "attack" ? 3.5 : 1.0),
                      rZ + (clip === "attack" ? 4.5 : 11.5));
        if (ent.arch === "caster") {
          limb(J(rF - 1.5, rR, rZ - 6), wpTip, 2.0, "#9333ea");
          ctx.fillStyle = "#38bdf8";
          ctx.beginPath(); ctx.arc(wpTip.x, wpTip.y, 3.2 * sc * z, 0, 7); ctx.fill();
          ctx.fillStyle = "#fff";
          ctx.beginPath(); ctx.arc(wpTip.x, wpTip.y, 1.4 * sc * z, 0, 7); ctx.fill();
        } else if (ent.arch === "ranger") {
          var bowT = J(rF + 3, rR, rZ + 7), bowB = J(rF + 3, rR, rZ - 5);
          ctx.strokeStyle = "#d97706"; ctx.lineWidth = Math.max(1.6, 2.2 * z);
          ctx.beginPath();
          ctx.moveTo(bowT.x, bowT.y);
          ctx.quadraticCurveTo(handR.x + 5 * cy * z, handR.y + 5 * sy * z,
                               bowB.x, bowB.y);
          ctx.stroke();
        } else {
          // 3D Broadsword / Warhammer blade + golden crossguard
          limb(handR, wpTip, 2.6, "#f0f6fc");
          var cgL = J(rF + 1, rR - 2.5, rZ + 1.5),
              cgR = J(rF + 1, rR + 2.5, rZ + 1.5);
          limb(cgL, cgR, 2.0, "#ffd54a");
        }
        // 3D Slash Ribbon during active combat/work
        if (clip === "attack") {
          ctx.strokeStyle = ent.arch === "caster"
            ? "rgba(56,189,248,0.65)" : "rgba(255,213,74,0.72)";
          ctx.lineWidth = Math.max(2, 3.2 * z);
          var sl0 = J(leanF + 4, 8, pelvZ + 12),
              sl1 = J(leanF + 12, 0, pelvZ + 6),
              sl2 = J(leanF + 5, -7, pelvZ + 2);
          ctx.beginPath();
          ctx.moveTo(sl0.x, sl0.y);
          ctx.quadraticCurveTo(sl1.x, sl1.y, sl2.x, sl2.y);
          ctx.stroke();
        }
      };

      if (cy >= 0) { drawArmL(); drawArmR(); }
      else { drawArmR(); drawArmL(); }

      // 8. 3D Head, Directional Visor/Eyes & Class Helmet/Crown/Hat
      var headP = J(leanF * 0.7, 0, pelvZ + 12.2);
      var hr = 4.4 * sc * z;
      ctx.fillStyle = Theme._sphereGrad
        ? Theme._sphereGrad(ctx, headP.x, headP.y, hr, "#ffe4bd", "#e8be8a", "#9c6f3e")
        : "#e8be8a";
      ctx.beginPath(); ctx.arc(headP.x, headP.y, hr, 0, 7); ctx.fill();
      // Directional Eyes oriented along facing vector (cy, sy)
      if (sy > -0.35) {
        var eyeL = J(leanF * 0.7 + 3.6, -1.5, pelvZ + 12.4),
            eyeR = J(leanF * 0.7 + 3.6, 1.5, pelvZ + 12.4);
        ctx.fillStyle = ent.arch === "caster" ? "#38bdf8" : "#111";
        ctx.fillRect(eyeL.x - 1, eyeL.y - 1, 2.2 * z, 2.2 * z);
        ctx.fillRect(eyeR.x - 1, eyeR.y - 1, 2.2 * z, 2.2 * z);
      }
      // 3D Helmet Plume / Wizard Cone / Hood Crest at wz = pelvZ + 16..21
      var crestPeak = J(leanF * 0.5 - 1.0, 0, pelvZ + 18.5);
      ctx.fillStyle = ent.arch === "caster" ? (ent.dark || "#3b0764")
                    : (ent.trim || "#ffd54a");
      ctx.beginPath();
      ctx.moveTo(headP.x - hr * 0.85, headP.y - hr * 0.3);
      ctx.lineTo(crestPeak.x, crestPeak.y);
      ctx.lineTo(headP.x + hr * 0.85, headP.y - hr * 0.3);
      ctx.closePath(); ctx.fill();

      if (sy < -0.2) drawCape();
      ctx.lineWidth = 1;
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
      (st.buildings || []).slice().sort(function (a, b) {
        return a.y - b.y;
      }).forEach(function (b) {
        var s = self.toScreen(b.x, b.y, 0);
        if (s.x < -80 || s.y < -80 || s.x > cv.width + 80 ||
            s.y > cv.height + 80) return;
        var w = 48 * z, h = 48 * z;
        self._drawBuilding3D(ctx, b, theme, z, t0, wind, pal);
        if (b.sel) {
          ctx.strokeStyle = pal.sel; ctx.lineWidth = 2;
          ctx.beginPath();
          ctx.ellipse(s.x, s.y, w * 0.58, h * 0.34, 0, 0, 7);
          ctx.stroke();
          ctx.lineWidth = 1;
        }
        if (z > 0.72 && b.name) {
          ctx.fillStyle = "rgba(10,16,12,0.82)";
          ctx.fillRect(s.x - 28 * z, s.y + 10 * z, 56 * z, 11 * z);
          ctx.fillStyle = "#ffd54a";
          ctx.font = "bold " + Math.max(8, Math.round(9 * z)) + "px monospace";
          ctx.textAlign = "center"; ctx.textBaseline = "middle";
          ctx.fillText(b.name, s.x, s.y + 15.5 * z);
        }
      });
      if (this.iso) this._officeProps(ctx, st, theme, z, t0); // #134
      var allUnits = (st.units || []).slice().sort(function (a, b) {
        return a.y - b.y;
      });
      allUnits.forEach(function (u) {
        var s = self.toScreen(u.x, u.y, 0);
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
        ctx.strokeRect(v.x / TILE * kx, v.y / (TILE * PITCH) * ky,
          v.w / TILE * kx, v.h / (TILE * PITCH) * ky);
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
