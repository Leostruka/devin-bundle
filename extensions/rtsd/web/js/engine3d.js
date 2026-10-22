/* engine3d.js - rtsd #194 optional WebGL render path.
   Real 3D meshes (terrain quads, building boxes/cones, unit cylinders,
   GL selection rings, point-sprite fx, rain streaks) drawn through a
   depth-tested, lambert-lit pipeline under the same camera math as the
   Canvas painter - so picking, clamps, minimap and HUD math are shared
   1:1. The 2D canvas stays on top as the HUD overlay pass (names, HP
   bars, barks, waypoint flags, order marks, pings, armed preview).
   Falls back to the Canvas painter for isometric office mode or when
   WebGL is unavailable. Zero deps, classic script (file:// safe). */
(function (g) {
  "use strict";

  var TILE = 32, PITCH = 0.74;

  function hex(c, d) {
    var n = parseInt((c || d || "#8899aa").slice(1), 16);
    return [((n >> 16) & 255) / 255, ((n >> 8) & 255) / 255,
            (n & 255) / 255];
  }
  function mix(a, b, k) {
    return [a[0] + (b[0] - a[0]) * k, a[1] + (b[1] - a[1]) * k,
            a[2] + (b[2] - a[2]) * k];
  }

  /* ---- geometry emitters: write pos3/nrm3/col3 triples into V ---- */
  function face(V, ax, ay, az, bx, by, bz, cx, cy, cz, dx, dy, dz,
                nx, ny, nz, col) {
    var i, xs = [ax, bx, cx, ax, cx, dx], ys = [ay, by, cy, ay, cy, dy],
        zs = [az, bz, cz, az, cz, dz];
    for (i = 0; i < 6; i++) {
      V.push(xs[i], ys[i], zs[i], nx, ny, nz, col[0], col[1], col[2]);
    }
  }
  function emitBox(V, x, y, z0, hx, hy, hz, col) {
    // six faces; +y faces south (brighter), -z face is the lit side
    var x0 = x - hx, x1 = x + hx, y0 = y - hy, y1 = y + hy, z1 = z0 + hz;
    face(V, x0, y0, z1, x1, y0, z1, x1, y1, z1, x0, y1, z1, 0, 0, 1,
         mix(col, [1, 1, 1], 0.18));                 // top (brightest)
    face(V, x0, y1, z0, x1, y1, z0, x1, y1, z1, x0, y1, z1, 0, 1, 0,
         col);                                       // south face
    face(V, x0, y0, z0, x0, y0, z1, x0, y1, z1, x0, y1, z0, -1, 0, 0,
         mix(col, [0, 0, 0], 0.3));                  // west (shaded)
    face(V, x1, y0, z0, x1, y0, z1, x1, y1, z1, x1, y1, z0, 1, 0, 0,
         mix(col, [0, 0, 0], 0.18));                 // east
    face(V, x0, y0, z0, x1, y0, z0, x1, y0, z1, x0, y0, z1, 0, -1, 0,
         mix(col, [0, 0, 0], 0.38));                 // north (darkest)
  }
  function emitCone(V, x, y, z0, r, h, seg, col) {
    var i, a0, a1;
    for (i = 0; i < seg; i++) {
      a0 = i / seg * Math.PI * 2; a1 = (i + 1) / seg * Math.PI * 2;
      var x0 = x + Math.cos(a0) * r, y0 = y + Math.sin(a0) * r,
          x1 = x + Math.cos(a1) * r, y1 = y + Math.sin(a1) * r,
          nx = Math.cos((a0 + a1) / 2), ny = Math.sin((a0 + a1) / 2),
          sh = 0.55 + 0.45 * Math.max(0, -nx * 0.4 + ny * 0.75);
      var c = [col[0] * sh, col[1] * sh, col[2] * sh];
      V.push(x0, y0, z0, nx, ny, 0.55, c[0], c[1], c[2],
             x1, y1, z0, nx, ny, 0.55, c[0], c[1], c[2],
             x, y, z0 + h, nx, ny, 0.55, c[0], c[1], c[2]);
    }
  }
  function emitCyl(V, x, y, z0, z1, r, seg, col) {
    var i, a0, a1;
    for (i = 0; i < seg; i++) {
      a0 = i / seg * Math.PI * 2; a1 = (i + 1) / seg * Math.PI * 2;
      var c0 = Math.cos(a0), s0 = Math.sin(a0),
          c1 = Math.cos(a1), s1 = Math.sin(a1),
          nx = Math.cos((a0 + a1) / 2), ny = Math.sin((a0 + a1) / 2),
          sh = 0.55 + 0.45 * Math.max(0, -nx * 0.4 + ny * 0.75);
      var cc = [col[0] * sh, col[1] * sh, col[2] * sh];
      V.push(x + c0 * r, y + s0 * r, z0, nx, ny, 0, cc[0], cc[1], cc[2],
             x + c1 * r, y + s1 * r, z0, nx, ny, 0, cc[0], cc[1], cc[2],
             x + c1 * r, y + s1 * r, z1, nx, ny, 0, cc[0], cc[1], cc[2],
             x + c0 * r, y + s0 * r, z0, nx, ny, 0, cc[0], cc[1], cc[2],
             x + c1 * r, y + s1 * r, z1, nx, ny, 0, cc[0], cc[1], cc[2],
             x + c0 * r, y + s0 * r, z1, nx, ny, 0, cc[0], cc[1], cc[2]);
    }
  }

  var MESH_VS =
    "attribute vec3 aPos;attribute vec3 aNrm;attribute vec3 aCol;" +
    "uniform vec4 uCam;uniform vec2 uRes;varying vec3 vCol;" +
    "void main(){" +
    " float sx=(aPos.x-uCam.x)*uCam.z;" +
    " float sy=(aPos.y*" + PITCH + "+aPos.z-uCam.y)*uCam.z;" +
    " vec2 clip=vec2(sx/uRes.x*2.0-1.0,1.0-sy/uRes.y*2.0);" +
    " gl_Position=vec4(clip,-aPos.y*0.00004,1.0);" +
    " float d=max(dot(normalize(aNrm),normalize(vec3(-0.35,-0.7,0.62))),0.0);" +
    " vCol=aCol*(0.62+0.38*d);}";
  var MESH_FS =
    "precision mediump float;varying vec3 vCol;" +
    "void main(){gl_FragColor=vec4(vCol,1.0);}";
  var PT_VS =
    "attribute vec3 aPos;attribute vec4 aCol;attribute float aSize;" +
    "uniform vec4 uCam;uniform vec2 uRes;varying vec4 vCol;" +
    "void main(){" +
    " float sx=(aPos.x-uCam.x)*uCam.z;" +
    " float sy=(aPos.y*" + PITCH + "+aPos.z-uCam.y)*uCam.z;" +
    " vec2 clip=vec2(sx/uRes.x*2.0-1.0,1.0-sy/uRes.y*2.0);" +
    " gl_Position=vec4(clip,-aPos.y*0.00004,1.0);" +
    " gl_PointSize=aSize*uCam.z;vCol=aCol;}";
  var PT_FS =
    "precision mediump float;varying vec4 vCol;" +
    "void main(){vec2 q=gl_PointCoord*2.0-1.0;float d=dot(q,q);" +
    " if(d>1.0)discard;gl_FragColor=vec4(vCol.rgb,vCol.a*(1.0-d));}";

  function shader(gl, type, src) {
    var s = gl.createShader(type);
    gl.shaderSource(s, src); gl.compileShader(s);
    return gl.getShaderParameter(s, gl.COMPILE_STATUS) ? s : null;
  }
  function program(gl, vs, fs) {
    var p = gl.createProgram();
    gl.attachShader(p, shader(gl, gl.VERTEX_SHADER, vs));
    gl.attachShader(p, shader(gl, gl.FRAGMENT_SHADER, fs));
    gl.linkProgram(p);
    return gl.getProgramParameter(p, gl.LINK_STATUS) ? p : null;
  }

  var BLD_COL = { // per-bid wall / roof palette
    "town-hall":  ["#8a7f66", "#4a5f8a"], "barracks":  ["#8a6f4d", "#7a3d2d"],
    "tavern":     ["#9a7b52", "#6b4a2f"], "library":   ["#7d8aa8", "#3d5a8a"],
    "watchtower": ["#7d7466", "#4a3f33"], "runeforge": ["#6b625a", "#8a3d1f"],
    "vault":      ["#8a8266", "#8a7a2d"], "portal":    ["#5a5a8a", "#2d2d5a"],
    "marketplace":["#9a8a5a", "#6b5a2d"], "altar":     ["#9a9488", "#8a7a2d"],
    "trophy-hall":["#8a7f66", "#c9a227"],
  };

  function Engine3D(canvas) {
    g.Engine._ctor.call(this, canvas);     // 2D overlay canvas + input
    var glc = document.createElement("canvas");
    glc.id = "cv3d";
    glc.style.cssText =
      "position:absolute;inset:0;width:100%;height:100%;z-index:0";
    canvas.parentNode.insertBefore(glc, canvas);
    canvas.style.position = "relative";
    canvas.style.zIndex = "1";
    canvas.style.background = "transparent";
    this.glc = glc;
    this.gl = glc.getContext("webgl2", { antialias: true, alpha: false }) ||
              glc.getContext("webgl", { antialias: true, alpha: false });
    if (this.gl) this._glInit();
  }
  Engine3D.prototype = Object.create(g.Engine._ctor.prototype);
  Engine3D.prototype.constructor = Engine3D;
  Engine3D.supported = function () {
    try {
      var c = document.createElement("canvas");
      return !!(c.getContext("webgl2") || c.getContext("webgl"));
    } catch (e) { return false; }
  };

  Engine3D.prototype._glInit = function () {
    var gl = this.gl;
    this._mesh = program(gl, MESH_VS, MESH_FS);
    this._pts = program(gl, PT_VS, PT_FS);
    this._vb = gl.createBuffer();
    this._pb = gl.createBuffer();
    gl.enable(gl.DEPTH_TEST);
    gl.depthFunc(gl.LEQUAL);
  };

  /* full scene: terrain, deco trees, buildings, units, selection, fx,
     rain - emitted CPU-side into one vertex buffer per frame */
  Engine3D.prototype._glScene = function (st, theme, now) {
    var self = this, ts = st.tiles, V = [], L = [], P = [];
    var fog = st.fog;
    var pal = (theme && theme.ui) || {};
    var tiles = (theme && theme.tiles) || [];
    var W = ts.w, H = ts.h;
    // visible tile range (camera clamp math, world px -> tile idx)
    var v = self.view();
    var tx0 = Math.max(0, Math.floor(v.x / TILE) - 1),
        tx1 = Math.min(W, Math.ceil((v.x + v.w) / TILE) + 1),
        ty0 = Math.max(0, Math.floor(v.y / (TILE * PITCH)) - 1),
        ty1 = Math.min(H, Math.ceil((v.y + v.h) / (TILE * PITCH)) + 1);
    var fogF = function (i) {
      var f = fog ? fog[i] : 2;
      return f >= 2 ? 1 : f === 1 ? 0.45 : 0.06;
    };
    var waterC = hex(tiles.water || "#1d4d70"),
        deepC = hex(tiles.waterDeep || "#153a58");
    // --- terrain quads (z: water -5, bridge +1, ground 0) ---
    for (var ty = ty0; ty < ty1; ty++) {
      for (var tx = tx0; tx < tx1; tx++) {
        var i = ty * W + tx;
        var wt = ts._water ? ts._water[i] : 0,
            rd = ts._roads ? ts._roads[i] : 0;
        var col;
        if (wt === 3) col = hex("#7c5836");
        else if (wt === 2) {
          var wv = 0.85 + 0.15 * Math.sin(now / 900 + tx * 0.7 + ty * 0.5);
          col = [deepC[0] * wv, deepC[1] * wv, deepC[2] * wv];
        } else if (wt === 1) {
          var w2 = 0.85 + 0.15 * Math.sin(now / 700 + tx * 0.9 - ty * 0.4);
          col = [waterC[0] * w2, waterC[1] * w2, waterC[2] * w2];
        } else if (rd === 2) col = hex(tiles.plaza || "#786954");
        else if (rd === 1) col = hex(tiles.road || "#63503a");
        else col = hex(tiles[ts.data[i] % 10] || tiles[0]);
        var f = fogF(i);
        col = [col[0] * f, col[1] * f, col[2] * f];
        var z = wt === 3 ? 1.5 : wt ? -5 : 0;
        var x0 = tx * TILE, x1 = x0 + TILE, y0 = ty * TILE, y1 = y0 + TILE;
        V.push(x0, y0, z, 0, 0, 1, col[0], col[1], col[2],
               x1, y0, z, 0, 0, 1, col[0], col[1], col[2],
               x1, y1, z, 0, 0, 1, col[0], col[1], col[2],
               x0, y0, z, 0, 0, 1, col[0], col[1], col[2],
               x1, y1, z, 0, 0, 1, col[0], col[1], col[2],
               x0, y1, z, 0, 0, 1, col[0], col[1], col[2]);
      }
    }
    // --- deco trees/rocks (cones + trunks) in view ---
    (ts._deco || []).forEach(function (d) {
      if (d.x < tx0 || d.x >= tx1 || d.y < ty0 || d.y >= ty1) return;
      var wx = (d.x + 0.5) * TILE, wy = (d.y + 0.5) * TILE;
      var i = (d.y | 0) * W + (d.x | 0), f = fogF(i);
      if (d.kind === "tree" || d.kind === "willow" || d.kind === "reed") {
        var tc = d.kind === "willow" ? hex("#3f7d3a") :
                 d.kind === "reed" ? hex("#4a7d4a") : hex("#2d5a26");
        tc = [tc[0] * f, tc[1] * f, tc[2] * f];
        emitCyl(V, wx, wy, 0, 8, 1.6, 5, hex("#5a4326"));
        emitCone(V, wx, wy, 6, 9, 14, 6, tc);
        emitCone(V, wx, wy, 13, 6.5, 9, 6, tc);
      } else if (d.kind === "rock") {
        emitBox(V, wx, wy, 0, 5, 4, 5, hex("#6b6b70"));
      }
    });
    // --- buildings: stacked boxes + roof cones/prisms ---
    (st.buildings || []).forEach(function (b) {
      if (b.x < tx0 * TILE || b.x >= tx1 * TILE ||
          b.y < ty0 * TILE || b.y >= ty1 * TILE) return;
      var pc = BLD_COL[b.bid] || BLD_COL["town-hall"];
      var wall = hex(pc[0]), roof = hex(pc[1]);
      var fi = ((b.y / TILE) | 0) * W + ((b.x / TILE) | 0);
      var f = fogF(fi);
      wall = [wall[0] * f, wall[1] * f, wall[2] * f];
      roof = [roof[0] * f, roof[1] * f, roof[2] * f];
      emitBox(V, b.x, b.y, 0, 16, 12, 16, wall);
      emitCone(V, b.x, b.y, 16, 13, 10, 4, roof);
      if (b.bid === "town-hall" || b.bid === "watchtower") {
        emitCyl(V, b.x - 14, b.y + 6, 0, 22, 4, 6, wall);
        emitCone(V, b.x - 14, b.y + 6, 22, 5, 8, 6, roof);
      }
      if (b.bid === "runeforge")
        emitCyl(V, b.x + 10, b.y - 4, 16, 30, 3, 5, hex("#3a3a42"));
      if (b.sel) {
        L.push(b.x - 20, b.y + 14, 2, 0, 0, 1, 0.25, 0.9, 0.4,
               b.x + 20, b.y + 14, 2, 0, 0, 1, 0.25, 0.9, 0.4);
      }
    });
    // --- units: cylinder body + box head + selection ring ---
    (st.units || []).forEach(function (u) {
      if (u.x < tx0 * TILE || u.x >= tx1 * TILE ||
          u.y < ty0 * TILE || u.y >= ty1 * TILE) return;
      var ent = (theme.units && theme.units[u.cls]) ||
                (theme.units && theme.units.Squire) || {};
      var body = hex(ent.c2 || ent.c1 || "#3a6ea5"),
          head = hex("#d8b58a");
      var r = u.kind === "hero" ? 5 : u.kind === "minion" ? 3.4 : 3,
          h = u.kind === "hero" ? 13 : 9;
      var bob = u.moving ? Math.abs(Math.sin(now / 85 +
                  (u.x % 31))) * 2 : 0;
      emitCyl(V, u.x, u.y, bob, h + bob, r, 7, body);
      emitBox(V, u.x, u.y - 1, h + bob, 3.2, 3.2, 4, head);
      if (u.sel) {                        // GL ellipse selection ring
        for (var s = 0; s < 24; s++) {
          var a0 = s / 24 * Math.PI * 2, a1 = (s + 1) / 24 * Math.PI * 2;
          L.push(u.x + Math.cos(a0) * r * 1.7, u.y + Math.sin(a0) * r * 0.9,
                 1, 0, 0, 1, 0.25, 0.85, 0.38,
                 u.x + Math.cos(a1) * r * 1.7, u.y + Math.sin(a1) * r * 0.9,
                 1, 0, 0, 1, 0.25, 0.85, 0.38);
        }
      }
      if (u.buff === "flame") {           // flaming weapons buff ring
        var fl = 0.5 + 0.4 * Math.sin(now / 90 + u.x);
        for (var s2 = 0; s2 < 16; s2++) {
          var b0 = s2 / 16 * Math.PI * 2, b1 = (s2 + 1) / 16 * Math.PI * 2;
          L.push(u.x + Math.cos(b0) * r * 1.4, u.y + Math.sin(b0) * r * 0.8,
                 h * 0.5, 0, 0, 1, 1, 0.42 * fl, 0,
                 u.x + Math.cos(b1) * r * 1.4, u.y + Math.sin(b1) * r * 0.8,
                 h * 0.5, 0, 0, 1, 1, 0.42 * fl, 0);
        }
      }
    });
    // --- fx + weather particles as point sprites ---
    (st.fx || []).forEach(function (fx) {
      var c = hex(fx.col || "#ffd54a");
      P.push(fx.x, fx.y, 14, c[0], c[1], c[2], 0.9, 7);
    });
    var cond = st.weather && st.weather.condition;
    if (cond === "rain" || cond === "storm") {
      var drop = hex("#9fc8ff");
      for (var d = 0; d < 160; d++) {
        var rx = v.x + ((d * 97 + (now * 0.4)) % v.w),
            ry = v.y + ((d * 57 + (now * 0.55)) % v.h);
        L.push(rx, ry, 10, 0, 0, 1, drop[0], drop[1], drop[2],
               rx + 2, ry + 9, 0, 0, 0, 1, drop[0], drop[1], drop[2]);
      }
    }
    return { V: V, L: L, P: P };
  };

  Engine3D.prototype._glDraw = function (V, L, P) {
    var gl = this.gl, cv = this.glc;
    var W = cv.width, H = cv.height;
    gl.viewport(0, 0, W, H);
    gl.clearColor(0.035, 0.05, 0.035, 1);
    gl.clear(gl.COLOR_BUFFER_BIT | gl.DEPTH_BUFFER_BIT);
    var pr = this._mesh;
    if (!pr) return;
    gl.useProgram(pr);
    var uCam = gl.getUniformLocation(pr, "uCam"),
        uRes = gl.getUniformLocation(pr, "uRes");
    gl.uniform4f(uCam, this.cam.x, this.cam.y, this.cam.zoom, 0);
    gl.uniform2f(uRes, W, H);
    gl.bindBuffer(gl.ARRAY_BUFFER, this._vb);
    var aPos = gl.getAttribLocation(pr, "aPos"),
        aNrm = gl.getAttribLocation(pr, "aNrm"),
        aCol = gl.getAttribLocation(pr, "aCol");
    gl.enableVertexAttribArray(aPos);
    gl.enableVertexAttribArray(aNrm);
    gl.enableVertexAttribArray(aCol);
    gl.vertexAttribPointer(aPos, 3, gl.FLOAT, false, 36, 0);
    gl.vertexAttribPointer(aNrm, 3, gl.FLOAT, false, 36, 12);
    gl.vertexAttribPointer(aCol, 3, gl.FLOAT, false, 36, 24);
    var tri = V.concat(L);   // L shares the pos/nrm/col layout
    if (V.length) {
      gl.bufferData(gl.ARRAY_BUFFER, new Float32Array(tri),
                    gl.DYNAMIC_DRAW);
      gl.drawArrays(gl.TRIANGLES, 0, V.length / 9);
      gl.drawArrays(gl.LINES, V.length / 9, L.length / 9);
    }
    if (P.length && this._pts) {
      pr = this._pts;
      gl.useProgram(pr);
      uCam = gl.getUniformLocation(pr, "uCam");
      uRes = gl.getUniformLocation(pr, "uRes");
      gl.uniform4f(uCam, this.cam.x, this.cam.y, this.cam.zoom, 0);
      gl.uniform2f(uRes, W, H);
      gl.bindBuffer(gl.ARRAY_BUFFER, this._pb);
      gl.bufferData(gl.ARRAY_BUFFER, new Float32Array(P),
                    gl.DYNAMIC_DRAW);
      var pPos = gl.getAttribLocation(pr, "aPos"),
          pCol = gl.getAttribLocation(pr, "aCol"),
          pSiz = gl.getAttribLocation(pr, "aSize");
      gl.enableVertexAttribArray(pPos);
      gl.enableVertexAttribArray(pCol);
      gl.enableVertexAttribArray(pSiz);
      gl.vertexAttribPointer(pPos, 3, gl.FLOAT, false, 40, 0);
      gl.vertexAttribPointer(pCol, 4, gl.FLOAT, false, 40, 12);
      gl.vertexAttribPointer(pSiz, 1, gl.FLOAT, false, 40, 28);
      gl.enable(gl.BLEND);
      gl.blendFunc(gl.SRC_ALPHA, gl.ONE_MINUS_SRC_ALPHA);
      gl.depthMask(false);
      gl.drawArrays(gl.POINTS, 0, P.length / 10);
      gl.depthMask(true);
      gl.disable(gl.BLEND);
    }
  };

  /* 2D HUD overlay pass on the top canvas: names, bars, barks, badges,
     waypoints, order marks, pings, armed preview, night dim */
  Engine3D.prototype._overlay = function (st, theme, now) {
    var self = this, ctx = this.ctx, cv = this.cv, z = this.cam.zoom;
    var pal = (theme && theme.ui) || {};
    ctx.clearRect(0, 0, cv.width, cv.height);
    var t0 = now;
    (st.units || []).forEach(function (u) {
      var s = self.toScreen(u.x, u.y, 0);
      if (s.x < -48 || s.y < -48 || s.x > cv.width + 48 ||
          s.y > cv.height + 48) return;
      var sz = (u.kind === "minion" ? 16 : u.kind === "worker" ? 12 : 26) *
               Math.max(z, 0.72);
      if (u.kind === "hero" && typeof u.hp === "number" && z > 0.45) {
        var bw = sz * 1.15;
        ctx.fillStyle = "rgba(0,0,0,0.85)";
        ctx.fillRect(s.x - bw / 2 - 1, s.y - sz / 2 - 10, bw + 2, 7);
        ctx.fillStyle = u.hp > 50 ? (pal.ok || "#3fb950") :
                        u.hp > 25 ? "#d29922" : (pal.err || "#f85149");
        ctx.fillRect(s.x - bw / 2, s.y - sz / 2 - 9, bw * u.hp / 100, 3);
        if (typeof u.mana === "number") {
          ctx.fillStyle = u.mana < 25 && (t0 % 600 < 300)
                          ? (pal.err || "#f85149") : "#58a6ff";
          ctx.fillRect(s.x - bw / 2, s.y - sz / 2 - 5,
            bw * u.mana / 100, 2);
        }
      }
      if (z > 0.75 && u.name) {
        ctx.fillStyle = "rgba(0,0,0,0.65)";
        ctx.fillRect(s.x - 24 * z, s.y + sz / 2 + 2, 48 * z, 10 * z);
        ctx.fillStyle = pal.text || "#e6e2d0";
        ctx.font = "bold " + Math.max(8, Math.round(9 * z)) + "px monospace";
        ctx.textAlign = "center"; ctx.textBaseline = "middle";
        ctx.fillText(u.name, s.x, s.y + sz / 2 + 7 * z);
      }
      if (u.statusFx && z > 0.45) {
        var bc = ({ patrol: "#58a6ff", gather: "#ffd54a",
                    attack: "#f85149", focus: "#ff6a00" })[u.statusFx] ||
                 "#8b949e";
        var bg = ({ patrol: "P", gather: "G",
                    attack: "A", focus: "F" })[u.statusFx] || "?";
        ctx.fillStyle = "rgba(10,14,20,0.92)";
        ctx.beginPath();
        ctx.arc(s.x + sz * 0.44, s.y - sz * 0.5, 6.5 * z, 0, 7);
        ctx.fill();
        ctx.strokeStyle = bc; ctx.stroke();
        ctx.fillStyle = bc;
        ctx.font = "bold " + Math.max(8, Math.round(8 * z)) + "px monospace";
        ctx.textAlign = "center"; ctx.textBaseline = "middle";
        ctx.fillText(bg, s.x + sz * 0.44, s.y - sz * 0.5);
      }
      if (u.bark && z > 0.55) {
        ctx.fillStyle = "rgba(18,26,20,0.88)";
        var tw = Math.min(180, (u.bark.length * 5.5 + 10) * z);
        ctx.fillRect(s.x - tw / 2, s.y - sz / 2 - 25 * z, tw, 12 * z);
        ctx.strokeStyle = "#d4a72c";
        ctx.strokeRect(s.x - tw / 2, s.y - sz / 2 - 25 * z, tw, 12 * z);
        ctx.fillStyle = "#fff8dc";
        ctx.font = "italic " + Math.max(9, Math.round(9.5 * z)) +
                   "px monospace";
        ctx.textAlign = "center"; ctx.textBaseline = "middle";
        ctx.fillText(u.bark, s.x, s.y - sz / 2 - 19 * z);
      }
    });
    // waypoint flags (#127) + client order marks (#193) + armed preview
    (st.waypoints || []).forEach(function (wp) {
      var s = self.toScreen(wp.x, wp.y), us = self.toScreen(wp.ux, wp.uy);
      ctx.globalAlpha = wp.state === "queued" ? 0.4 : 0.95;
      ctx.strokeStyle = "#58a6ff";
      ctx.setLineDash([4 * z, 4 * z]);
      ctx.beginPath(); ctx.moveTo(us.x, us.y); ctx.lineTo(s.x, s.y);
      ctx.stroke(); ctx.setLineDash([]);
      var fh = 12 * Math.max(z, 0.7);
      ctx.fillStyle = "#58a6ff";
      ctx.fillRect(s.x - 1, s.y - fh, 2, fh);
      ctx.beginPath();
      ctx.moveTo(s.x + 1, s.y - fh);
      ctx.lineTo(s.x + 9 * z, s.y - fh * 0.75);
      ctx.lineTo(s.x + 1, s.y - fh * 0.5); ctx.fill();
      ctx.fillStyle = pal.text || "#e6e2d0";
      ctx.font = "bold " + Math.max(9, 10 * z) + "px monospace";
      ctx.textAlign = "center"; ctx.textBaseline = "bottom";
      ctx.fillText(String(wp.n), s.x, s.y - fh - 1);
      ctx.globalAlpha = 1;
    });
    var MARK_COL = { patrol: "#58a6ff", gather: "#ffd54a",
                     attack: "#f85149", focus: "#ff6a00" };
    (st.orderMarks || []).forEach(function (mk) {
      var col = MARK_COL[mk.kind] || "#58a6ff";
      ctx.globalAlpha = 0.8; ctx.strokeStyle = col;
      ctx.setLineDash([5 * z, 4 * z]);
      ctx.beginPath();
      var s0 = self.toScreen(mk.fx, mk.fy);
      ctx.moveTo(s0.x, s0.y);
      mk.pts.forEach(function (p) {
        var s = self.toScreen(p.x, p.y); ctx.lineTo(s.x, s.y);
      });
      ctx.stroke(); ctx.setLineDash([]);
      var e = mk.pts[mk.pts.length - 1], se = self.toScreen(e.x, e.y);
      ctx.fillStyle = col;
      ctx.fillRect(se.x - 1, se.y - 13 * z, 2, 13 * z);
      ctx.beginPath();
      ctx.moveTo(se.x + 1, se.y - 13 * z);
      ctx.lineTo(se.x + 8 * z, se.y - 10 * z);
      ctx.lineTo(se.x + 1, se.y - 7 * z); ctx.fill();
      ctx.globalAlpha = 1;
    });
    if (st.armed && st.armed.to) {
      var ac = ({ move: "#58a6ff", attack: "#f85149",
                  focus: "#ff6a00" })[st.armed.order] || "#bc8cff";
      var ts = self.toScreen(st.armed.to.x, st.armed.to.y);
      ctx.globalAlpha = 0.85; ctx.strokeStyle = ac; ctx.lineWidth = 2;
      ctx.setLineDash([6 * z, 5 * z]);
      (st.armed.from || []).forEach(function (f) {
        var fs = self.toScreen(f.x, f.y);
        ctx.beginPath(); ctx.moveTo(fs.x, fs.y); ctx.lineTo(ts.x, ts.y);
        ctx.stroke();
      });
      ctx.setLineDash([]);
      var pr = (9 + 3 * Math.sin(now / 160)) * z;
      ctx.beginPath(); ctx.arc(ts.x, ts.y, pr, 0, 7); ctx.stroke();
      ctx.lineWidth = 1; ctx.globalAlpha = 1;
    }
    (st.pings || []).forEach(function (p) {
      var age = (now - p.t0) / 1000;
      if (age < 0 || age > 6) return;
      var s = self.toScreen(p.x, p.y);
      ctx.globalAlpha = Math.max(0, 1 - age / 6);
      ctx.strokeStyle = ({ decision: "#ffd54a", fail: "#f85149",
        spawn: "#3fb950", contested: "#e3813f", file: "#9fb4c7",
        order: "#58a6ff" })[p.kind] || pal.sel || "#d4a72c";
      ctx.lineWidth = 2;
      ctx.beginPath();
      ctx.arc(s.x, s.y, (8 + age * 26) * z, 0, 7); ctx.stroke();
      ctx.globalAlpha = 1; ctx.lineWidth = 1;
    });
    if (st.night) {
      ctx.fillStyle = "rgba(10,12,40," + (st.night * 0.5).toFixed(3) + ")";
      ctx.fillRect(0, 0, cv.width, cv.height);
    }
  };

  Engine3D.prototype.render = function (st, theme) {
    this.units = st.units; this.buildings = st.buildings;
    if (st.tiles) this.map = st.tiles;
    this.clampCam();
    // Office/iso stays on the Canvas painter (the overlay path is
    // battlefield-only), and no-GL environments fall back wholesale.
    if (this.iso || !this.gl || !this._mesh || !st.tiles) {
      return g.Engine._ctor.prototype.render.call(this, st, theme);
    }
    var cv = this.glc;
    if (cv.width !== this.cv.clientWidth ||
        cv.height !== this.cv.clientHeight) {
      cv.width = this.cv.clientWidth; cv.height = this.cv.clientHeight;
      this.cv.width = cv.width; this.cv.height = cv.height;
    }
    this._ensureEnv(st.tiles, st);
    var now = performance.now();
    var sc = this._glScene(st, theme, now);
    this._glDraw(sc.V, sc.L, sc.P);
    this._overlay(st, theme, now);
  };

  g.Engine3D = {
    supported: Engine3D.supported,
    create: function (cv) { return new Engine3D(cv); },
  };
})(window);
