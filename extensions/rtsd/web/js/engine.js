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
    this.onPick = null;                      // cb(unit|null, worldPt)
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
      this.cam.x = Math.max(-200, Math.min(mw - v.w + 200, this.cam.x));
      this.cam.y = Math.max(-200, Math.min(mh - v.h + 200, this.cam.y));
    },
    centerOn: function (wx, wy) {
      var v = this.view();
      this.cam.x = wx - v.w / 2; this.cam.y = wy - v.h / 2; this.clampCam();
    },
    panBy: function (dx, dy) {
      this.cam.x += dx; this.cam.y += dy; this.clampCam();
    },
    toWorld: function (sx, sy) {
      return { x: this.cam.x + sx / this.cam.zoom,
               y: this.cam.y + sy / this.cam.zoom };
    },
    toScreen: function (wx, wy) {
      return { x: (wx - this.cam.x) * this.cam.zoom,
               y: (wy - this.cam.y) * this.cam.zoom };
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
        var v = E.view();
        E.cam.x = p.x - e.offsetX / E.cam.zoom;
        E.cam.y = p.y - e.offsetY / E.cam.zoom;
        E.clampCam();
      }, { passive: false });
      cv.addEventListener("mousemove", function (e) {
        E.mouse.x = e.offsetX; E.mouse.y = e.offsetY; E.mouse.in = true;
      });
      cv.addEventListener("mouseleave", function () { E.mouse.in = false; });
      cv.addEventListener("click", function (e) {
        if (!E.onPick || !E.map) return;
        E.onPick(E.pickUnit(e.offsetX, e.offsetY),
                 E.toWorld(e.offsetX, e.offsetY), e);
      });
      var drag = null;
      cv.addEventListener("mousedown", function (e) {
        if (e.button === 1 || (e.button === 0 && e.altKey))
          drag = { x: e.clientX, y: e.clientY, cx: E.cam.x, cy: E.cam.y };
      });
      window.addEventListener("mousemove", function (e) {
        if (!drag) return;
        E.cam.x = drag.cx - (e.clientX - drag.x) / E.cam.zoom;
        E.cam.y = drag.cy - (e.clientY - drag.y) / E.cam.zoom;
        E.clampCam();
      });
      window.addEventListener("mouseup", function () { drag = null; });
    },

    // per-frame camera update: WASD/arrows + edge pan
    step: function (dt) {
      var sp = 520 * dt / this.cam.zoom;
      var k = this.keys;
      if (k["w"] || k["arrowup"]) this.panBy(0, -sp);
      if (k["s"] || k["arrowdown"]) this.panBy(0, sp);
      if (k["a"] || k["arrowleft"]) this.panBy(-sp, 0);
      if (k["d"] || k["arrowright"]) this.panBy(sp, 0);
      if (this.mouse.in) {
        var m = this.mouse, W = this.cv.width, H = this.cv.height, E = 24;
        if (m.x < E) this.panBy(-sp, 0);
        if (m.x > W - E) this.panBy(sp, 0);
        if (m.y < E) this.panBy(0, -sp);
        if (m.y > H - E) this.panBy(0, sp);
      }
    },

    pickUnit: function (sx, sy) {
      var p = this.toWorld(sx, sy), best = null, bd = 14 / this.cam.zoom + 8;
      (this.units || []).forEach(function (u) {
        var d = Math.hypot(u.x - p.x, u.y - p.y);
        if (d < bd) { bd = d; best = u; }
      });
      return best;
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
      var v = this.view(), z = this.cam.zoom, pal = theme.palette;
      ctx.fillStyle = pal.bg; ctx.fillRect(0, 0, cv.width, cv.height);
      this.units = st.units || [];
      if (!st.tiles) return;
      var ts = st.tiles, W = ts.w, H = ts.h;
      var x0 = Math.max(0, Math.floor(v.x / TILE)),
          y0 = Math.max(0, Math.floor(v.y / TILE)),
          x1 = Math.min(W, Math.ceil((v.x + v.w) / TILE)),
          y1 = Math.min(H, Math.ceil((v.y + v.h) / TILE));
      var px = TILE * z;
      for (var ty = y0; ty < y1; ty++) {
        for (var tx = x0; tx < x1; tx++) {
          var i = ty * W + tx;
          var f = st.fog ? st.fog[i] : 2;
          if (f === 0) continue; // shroud: stays palette.bg
          var mk = ts.mark ? ts.mark[i] : 0;
          ctx.fillStyle = mk === 2 ? theme.tiles.contested :
            mk === 1 ? theme.tiles.plot :
            theme.tiles[ts.data[i] % 10] || theme.tiles[0];
          var sx = (tx * TILE - v.x) * z, sy = (ty * TILE - v.y) * z;
          ctx.fillRect(sx, sy, px + 1, px + 1);
          if (f === 1) {           // explored-but-dim
            ctx.fillStyle = "rgba(0,0,0,0.45)";
            ctx.fillRect(sx, sy, px + 1, px + 1);
          }
        }
      }
      // POI markers: quests show through fog, others only once seen (#122)
      var self = this;
      (st.pois || []).forEach(function (p) {
        var i = p.y * W + p.x;
        var f = st.fog ? st.fog[i] : 2;
        if (f === 0 && p.kind !== "quest") return;
        var s = self.toScreen(p.x * TILE + TILE / 2, p.y * TILE + TILE / 2);
        if (s.x < -30 || s.y < -30 || s.x > cv.width + 30 ||
            s.y > cv.height + 30) return;
        var g = { quest: "!", gold: "*", camp: "x" }[p.kind] || "?";
        var c = { quest: pal.sel, gold: "#ffd54a",
                  camp: pal.err }[p.kind] || pal.text;
        ctx.fillStyle = c;
        ctx.font = "bold " + Math.max(10, 14 * z) + "px monospace";
        ctx.textAlign = "center"; ctx.textBaseline = "middle";
        ctx.fillText(g, s.x, s.y);
      });
      (st.buildings || []).forEach(function (b) {
        var s = self.toScreen(b.x, b.y);
        if (s.x < -64 || s.y < -64 || s.x > cv.width + 64 ||
            s.y > cv.height + 64) return;
        var w = 44 * z, h = 44 * z;
        Theme.sprite(ctx, theme.buildings[b.bid] || theme.buildings["vault"],
                     s.x - w / 2, s.y - h / 2, w, h);
      });
      (st.units || []).forEach(function (u) {
        var s = self.toScreen(u.x, u.y);
        if (s.x < -40 || s.y < -40 || s.x > cv.width + 40 ||
            s.y > cv.height + 40) return;
        var sz = (u.kind === "minion" ? 14 : u.kind === "worker" ? 10 : 22)
            * Math.max(z, 0.7);
        var ent = theme.units[u.cls] || theme.units.Squire;
        Theme.sprite(ctx, ent, s.x - sz / 2, s.y - sz / 2, sz, sz);
        if (u.status_live === "failed" || u.gate_fail) {
          ctx.strokeStyle = pal.err; ctx.lineWidth = 2;
          ctx.beginPath(); ctx.arc(s.x, s.y, sz / 2 + 3, 0, 7); ctx.stroke();
          ctx.lineWidth = 1;
        }
        if (u.sel) {
          ctx.strokeStyle = pal.sel; ctx.lineWidth = 2;
          ctx.beginPath(); ctx.arc(s.x, s.y, sz / 2 + 4, 0, 7); ctx.stroke();
          ctx.lineWidth = 1;
        }
        if (u.kind === "hero" && typeof u.hp === "number" && z > 0.5) {
          var bw = sz;
          ctx.fillStyle = "#000"; ctx.fillRect(s.x - bw / 2, s.y - sz / 2 - 8,
            bw, 3);
          ctx.fillStyle = u.hp > 50 ? pal.ok : u.hp > 25 ? "#d29922" : pal.err;
          ctx.fillRect(s.x - bw / 2, s.y - sz / 2 - 8, bw * u.hp / 100, 3);
          if (typeof u.mana === "number") {
            ctx.fillStyle = "#000";
            ctx.fillRect(s.x - bw / 2, s.y - sz / 2 - 4, bw, 2);
            ctx.fillStyle = "#58a6ff";
            ctx.fillRect(s.x - bw / 2, s.y - sz / 2 - 4,
              bw * u.mana / 100, 2);
          }
        }
        if (z > 1.2 && u.name) {
          ctx.fillStyle = pal.text; ctx.font = "9px monospace";
          ctx.textAlign = "center";
          ctx.fillText(u.name, s.x, s.y + sz / 2 + 9);
        }
      });
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
      for (var y = 0; y < H; y++) {
        for (var x = 0; x < W; x++) {
          var i = y * W + x;
          var f = st.fog ? st.fog[i] : 2;
          if (f === 0) continue;
          var mk = ts.mark ? ts.mark[i] : 0;
          ctx.fillStyle = mk === 2 ? theme.tiles.contested :
            mk === 1 ? theme.tiles.plot :
            theme.tiles[ts.data[i] % 10] || theme.tiles[0];
          ctx.fillRect(x * kx, y * ky, sx + 0.5, sy + 0.5);
          if (f === 1) {
            ctx.fillStyle = "rgba(0,0,0,0.5)";
            ctx.fillRect(x * kx, y * ky, sx + 0.5, sy + 0.5);
          }
        }
      }
      var self = this;
      (st.units || []).forEach(function (u) {
        var big = u.kind === "hero";
        ctx.fillStyle = u.status_live === "failed" || u.gate_fail
          ? "#f85149" : big ? "#ffd54a" : "#9fb4c7";
        var r = big ? 2.6 : 1.4;
        ctx.beginPath();
        ctx.arc(u.x / TILE * kx, u.y / TILE * ky, r, 0, 7);
        ctx.fill();
      });
      // viewport rectangle
      var v = this.view();
      ctx.strokeStyle = "#e6f2e6";
      ctx.strokeRect(v.x / TILE * kx, v.y / TILE * ky,
        v.w / TILE * kx, v.h / TILE * ky);
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
