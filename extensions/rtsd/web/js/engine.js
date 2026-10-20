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
      return mk === 2 ? theme.tiles.contested :
        mk === 1 ? theme.tiles.plot :
        theme.tiles[ts.data[i] % 10] || theme.tiles[0];
    },

    // battlefield: axis-aligned floor squares, culled by the view rect
    _flatTiles: function (ctx, st, theme, z, v) {
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
          ctx.fillStyle = this._tileStyle(ctx, st, theme, i);
          var sx = (tx * TILE - v.x) * z, sy = (ty * TILE - v.y) * z;
          ctx.fillRect(sx, sy, px + 1, px + 1);
          if (f === 1) {           // explored-but-dim
            ctx.fillStyle = "rgba(0,0,0,0.45)";
            ctx.fillRect(sx, sy, px + 1, px + 1);
          }
          // #133 breach alarm: a failed ledger gate keeps its whole
          // territory pulsing red until the gate set goes green
          if (ts.breach && ts.breach[i]) {
            ctx.fillStyle = "rgba(248,81,73," +
              (0.16 + 0.10 * Math.sin(performance.now() / 280))
                .toFixed(3) + ")";
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
          var f = st.fog ? st.fog[i] : 2;
          if (f === 0) continue;
          var p0 = this.toScreen(tx * TILE, ty * TILE),
              p1 = this.toScreen((tx + 1) * TILE, ty * TILE),
              p2 = this.toScreen((tx + 1) * TILE, (ty + 1) * TILE),
              p3 = this.toScreen(tx * TILE, (ty + 1) * TILE);
          ctx.beginPath();
          ctx.moveTo(p0.x, p0.y); ctx.lineTo(p1.x, p1.y);
          ctx.lineTo(p2.x, p2.y); ctx.lineTo(p3.x, p3.y);
          ctx.closePath();
          ctx.fillStyle = this._tileStyle(ctx, st, theme, i);
          ctx.fill();
          if (f === 1) {
            ctx.fillStyle = "rgba(0,0,0,0.45)"; ctx.fill();
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
      if (!st.tiles) return;
      var ts = st.tiles, W = ts.w, H = ts.h;
      if (this.iso) { this._isoTiles(ctx, st, theme, z); }
      else { this._flatTiles(ctx, st, theme, z, v); }
      // POI markers: quests show through fog, others only once seen (#122)
      var self = this;
      (st.pois || []).forEach(function (p) {
        var i = p.y * W + p.x;
        var f = st.fog ? st.fog[i] : 2;
        if (f === 0 && p.kind !== "quest") return;
        var s = self.toScreen(p.x * TILE + TILE / 2, p.y * TILE + TILE / 2);
        if (s.x < -30 || s.y < -30 || s.x > cv.width + 30 ||
            s.y > cv.height + 30) return;
        // #130 quest marker states: open "!" gold, blocked "?" grey,
        // done "*" rewards stamp (green), failed "!" red until retried
        var g = p.kind === "quest"
          ? (p.qst === "done" ? "*" : p.qst === "blocked" ? "?" : "!")
          : { gold: "*", camp: "x" }[p.kind] || "?";
        var c = p.kind === "quest"
          ? ({ done: "#3fb950", blocked: "#8b949e", failed: pal.err,
               open: "#ffd54a" })[p.qst] || "#ffd54a"
          : { gold: "#ffd54a", camp: pal.err }[p.kind] || pal.text;
        ctx.fillStyle = c;
        ctx.font = "bold " + Math.max(10, 14 * z) + "px monospace";
        ctx.textAlign = "center"; ctx.textBaseline = "middle";
        ctx.fillText(g, s.x, s.y);
      });
      this.buildings = st.buildings || [];
      (st.buildings || []).forEach(function (b) {
        var s = self.toScreen(b.x, b.y);
        if (s.x < -64 || s.y < -64 || s.x > cv.width + 64 ||
            s.y > cv.height + 64) return;
        var w = 44 * z, h = 44 * z;
        Theme.sprite(ctx, theme.buildings[b.bid] || theme.buildings["vault"],
                     s.x - w / 2, s.y - h / 2, w, h);
        if (b.sel) {
          ctx.strokeStyle = pal.sel; ctx.lineWidth = 2;
          ctx.strokeRect(s.x - w / 2 - 3, s.y - h / 2 - 3, w + 6, h + 6);
          ctx.lineWidth = 1;
        }
      });
      if (this.iso) this._officeProps(ctx, st, theme, z, t0); // #134
      (st.units || []).forEach(function (u) {
        var s = self.toScreen(u.x, u.y);
        if (s.x < -40 || s.y < -40 || s.x > cv.width + 40 ||
            s.y > cv.height + 40) return;
        var sz = (u.kind === "minion" ? 14 : u.kind === "worker" ? 10 : 22)
            * Math.max(z, 0.7);
        var ent = theme.units[u.cls] || theme.units.Squire;
        var dy = 0, ph = hash(String(u.id));
        if (self.iso) {          // #134: desk under office workers
          var dw = u.kind === "minion" ? sz * 2.2 : sz * 1.3;
          ctx.fillStyle = "#4a4034";
          ctx.fillRect(s.x - dw / 2, s.y + sz * 0.15, dw, sz * 0.38);
          ctx.fillStyle = "#5c503f";
          ctx.fillRect(s.x - dw / 2, s.y + sz * 0.15, dw, 2);
        }
        // #136 animation states: walk bounce while gliding on an order,
        // work-loop hammering on an active task, slow fidget when idle
        if (u.moving)
          dy = -Math.abs(Math.sin(t0 / 90 + ph)) * 2.5 * z;
        else if (u.status_live === "running")
          dy = Math.sin(t0 / 160 + ph) * 1.5 * z;
        else
          dy = Math.sin(t0 / 2400 + ph) * 1.0 * z;
        Theme.sprite(ctx, ent, s.x - sz / 2, s.y - sz / 2 + dy, sz, sz);
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
            // low mana (compaction near) flashes the bar (#125)
            var low = u.mana < 25;
            ctx.fillStyle = low && (performance.now() % 600 < 300)
              ? pal.err : "#58a6ff";
            ctx.fillRect(s.x - bw / 2, s.y - sz / 2 - 4,
              bw * u.mana / 100, 2);
          }
        }
        if (z > 1.2 && u.name) {
          ctx.fillStyle = pal.text; ctx.font = "9px monospace";
          ctx.textAlign = "center";
          ctx.fillText(u.name, s.x, s.y + sz / 2 + 9);
        }
        // voice bark: heartbeat note / ack floats over the head (#125)
        if (u.bark && z > 0.6) {
          ctx.fillStyle = "rgba(230,242,230,0.9)";
          ctx.font = "italic " + Math.max(9, 10 * z) + "px monospace";
          ctx.textAlign = "center";
          ctx.fillText(u.bark, s.x, s.y - sz / 2 - 14);
        }
      });
      // worker peasants scurry between buildings (#125)
      var now = performance.now();
      var srvNow = st.srvClock ? st.srvClock.srv +
        (now - st.srvClock.perf) / 1000 : now / 1000;
      (st.workers || []).forEach(function (wk) {
        var prog = Math.min(1, Math.max(0, (srvNow - wk.ts) / 4));
        var wx = (wk.from[0] + (wk.to[0] - wk.from[0]) * prog) * TILE + 16;
        var wy = (wk.from[1] + (wk.to[1] - wk.from[1]) * prog) * TILE + 16;
        var s = self.toScreen(wx, wy);
        if (s.x < -20 || s.y < -20 || s.x > cv.width + 20 ||
            s.y > cv.height + 20) return;
        var wsize = 9 * Math.max(z, 0.7);
        Theme.sprite(ctx, theme.units.Worker, s.x - wsize / 2,
                     s.y - wsize / 2, wsize, wsize);
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
      var self = this;
      (st.buildings || []).forEach(function (b) {
        ctx.fillStyle = "#c9b37e";
        ctx.fillRect(b.x / TILE * kx - 2, b.y / TILE * ky - 2, 4, 4);
      });
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
      (st.units || []).forEach(function (u) {
        var big = u.kind === "hero";
        ctx.fillStyle = u.status_live === "failed" || u.gate_fail
          ? "#f85149" : big ? "#ffd54a" : "#9fb4c7";
        var r = big ? 2.6 : 1.4;
        ctx.beginPath();
        ctx.arc(u.x / TILE * kx, u.y / TILE * ky, r, 0, 7);
        ctx.fill();
      });
      // viewport rectangle (top-down minimap stays a world overview;
      // under the iso theme the camera rect has no tile-space shape)
      if (!this.iso) {
        var v = this.view();
        ctx.strokeStyle = "#e6f2e6";
        ctx.strokeRect(v.x / TILE * kx, v.y / TILE * ky,
          v.w / TILE * kx, v.h / TILE * ky);
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
