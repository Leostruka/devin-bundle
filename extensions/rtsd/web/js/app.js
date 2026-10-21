/* app.js - rtsd v2 client: connection, world state, HUD wiring.
   Source of truth is the daemon snapshot (v2 `world` key); when the daemon
   is unreachable the app drops to a clearly-labeled OFFLINE DEMO world so
   the renderer/camera stays exercisable (issue #121 acceptance). */
(function (g) {
  "use strict";

  var TILE = Engine.TILE;
  var qs = new URLSearchParams(location.search);
  var TOK = qs.get("token");
  var BENCH = qs.has("bench");

  var state = {
    snap: null,              // last daemon snapshot (v1+v2 keys)
    world: null,             // world section {units,buildings,resources,...}
    map: null,               // {w,h,tiles,fog,regions:{id:{cx,cy}}}
    units: [],               // renderable units [{id,x,y,cls,...}]
    buildings: [],           // renderable buildings [{id,x,y,bid}]
    sel: null,               // primary selected unit id
    selAll: [],              // all selected unit ids (#126 multi-select)
    selB: null,              // selected building id
    groups: {},              // control groups: "1".."9" -> [unit ids] (#126)
    gtap: { n: 0, t: 0 },    // last group-recall tap for double-tap center
    pending: null,           // targeted order awaiting map click (#126)
    bDetail: null,           // fetched /buildings/<id> payload
    lastEventPos: null,      // {x,y} for spacebar jump
    pings: [],               // event pings {x,y,kind,t0} (#124)
    pingIdx: 0,
    fades: [],               // death/despawn markers {x,y,cls,t0} (#125)
    acks: {},                // unit id -> {text,t0} local ack barks
    demo: false,
    feed: [],                // comms lines {t,kind,who,cls,uid,text} (#128)
    feedFilter: { kind: null, cls: null },
    ravens: [],              // in-flight mailbox birds {fx,fy,tx,ty,t0}
    seenDec: null,           // pending decision ids from last snapshot
    seenBreach: null,        // breached ledger ids from last snapshot (#133)
    prevUpkeep: null,        // upkeep tier from last snapshot (#131)
    heardDec: {},            // ids already alarmed via WS upsert (#129)
    decActive: null,         // decision shown in the council modal
    decT0: 0,                // first-seen time for meeting summons (#134)
    motion: {},              // unit id -> display pos {x,y} glide (#136)
    cams: {},                // F1-F4 camera bookmarks (#136)
    weather: null,           // live local weather forecast (#157)
    fx: [],                  // spell AoE + floating combat/loot text (#159)
    councilClosed: false,    // manual close for war council (#159)
    wxModes: ["live", "rain", "storm", "snow", "fog", "clear", "windy"],
    wxIdx: 0,
    mmFilter: "all",
    dn: localStorage.getItem("rtsd.daynight") === "1" // day/night on
  };

  function esc(s) {
    return (s || "").replace(/[&<>"']/g,
      function (c) { return { "&": "&amp;", "<": "&lt;", ">": "&gt;",
        '"': "&quot;", "'": "&#39;" }[c]; });
  }
  function el(id) { return document.getElementById(id); }

  // ---- comms feed (#128) ----------------------------------------------
  // Server feed lines are event-sourced (world.feed rebuilds identically
  // from events.jsonl); local entries (order echoes, group assigns) are
  // UI-side only and never pretend to be agent traffic.
  var FEED_KINDS = ["spawn", "debrief", "position", "note", "council",
                    "order", "steering", "raven", "quest", "econ",
                    "spell", "breach", "local"];

  function logFeed(m) {   // local UI echo (orders, groups, demo notice)
    pushFeed({ t: Date.now() / 1000, kind: "local", who: "UI",
               cls: null, uid: null, text: m });
  }
  function pushFeed(f) {
    // skip if the snapshot rebuild already delivered this line
    for (var i = 0; i < Math.min(5, state.feed.length); i++) {
      var g = state.feed[i];
      if (g.t === f.t && g.who === f.who && g.text === f.text) return;
    }
    state.feed.unshift(f);
    if (state.feed.length > 200) state.feed.pop();
    renderFeed();
  }
  function renderFeed() {
    var ff = state.feedFilter;
    var lines = state.feed.filter(function (f) {
      return (!ff.kind || f.kind === ff.kind) &&
             (!ff.cls || f.cls === ff.cls || f.who === ff.cls);
    });
    el("feed").innerHTML = lines.map(function (f) {
      var t = new Date((f.t || 0) * 1000).toLocaleTimeString();
      return "<div class='fl k-" + esc(f.kind || "local") + "'" +
        (f.uid ? " data-uid='" + esc(f.uid) + "'" : "") +
        "><span class='ft'>" + t + "</span> " +
        "<span class='fw'>[" + esc(f.who || "?") + "]</span> " +
        esc(f.text || "") + "</div>";
    }).join("");
    // filter chips: one per kind seen + per unit class seen
    var kinds = {}, clss = {};
    state.feed.forEach(function (f) {
      if (f.kind) kinds[f.kind] = 1;
      if (f.cls) clss[f.cls] = 1;
    });
    var chip = function (key, val) {
      return "<button class='fchip" +
        (ff[key] === (val || null) ? " on" : "") + "' data-fk='" + key +
        "' data-fv='" + esc(val) + "'>" + esc(val || "all") + "</button>";
    };
    el("ffilter").innerHTML =
      chip("kind", "") + Object.keys(kinds).sort().map(function (k) {
        return chip("kind", k); }).join("") +
      Object.keys(clss).sort().map(function (c) {
        return chip("cls", c); }).join("");
  }

  // ---- world -> render state ----------------------------------------

  var MAPW = 72, MAPH = 54; // tile grid size must match world.py

  // Authoritative map from the daemon snapshot (#122): tile_region,
  // per-tile fog (0 shroud/1 explored/2 lit), mark codes and POIs are all
  // server-computed; we only pick region-tinted tile colors.
  function serverMap(m) {
    var W = m.w, H = m.h, n = W * H;
    var data = new Uint8Array(n);
    for (var i = 0; i < n; i++) {
      var x = i % W, y = (i / W) | 0;
      data[i] = (m.tile_region[i] * 3 + (Engine.hash(x + ":" + y) % 3)) % 10;
    }
    var caps = {};
    (m.regions || []).forEach(function (r) {
      if (r.capital) caps[r.id] = { cx: r.capital[0], cy: r.capital[1],
                                    region: r };
    });
    return { w: W, h: H, data: data, sig: m.sig, caps: caps,
             tint: laneTint(m),
             fog: new Uint8Array(m.fog || n),
             mark: new Uint8Array(m.mark || n),
             pois: m.pois || [],
             // region lookup for rally channels / lane previews (#127)
             regionIds: (m.regions || []).map(function (r) { return r.id; }),
             tileRegion: m.tile_region || [] };
  }

  // lane-ownership overlay per tile; recomputed each snapshot because
  // region owners shift as lanes touch files (#124)
  function laneTint(m) {
    var tint = new Array(m.w * m.h).fill(null);
    (m.regions || []).forEach(function (r, ri) {
      if (!r.owner) return;
      var col = "hsla(" + (Engine.hash(String(r.owner)) % 360) +
                ",70%,55%,0.22)";
      for (var i = 0; i < tint.length; i++)
        if (m.tile_region[i] === ri) tint[i] = col;
    });
    return tint;
  }

  // Offline/demo fallback: same shape as serverMap, synthesized locally.
  function buildMap(regs) {
    var regs = (regs && regs.length ? regs :
      [{ id: "wilds", revealed: true, activity: 0, contested: 0 }]);
    var caps = {};
    regs.forEach(function (r, i) {
      var ang = 6.2832 * i / regs.length;
      caps[r.id] = { cx: Math.round(MAPW / 2 + Math.cos(ang) * MAPW * .33),
                     cy: Math.round(MAPH / 2 + Math.sin(ang) * MAPH * .33),
                     region: r, idx: i };
    });
    var tiles = new Uint8Array(MAPW * MAPH);
    var fog = new Uint8Array(MAPW * MAPH);
    var mark = new Uint8Array(MAPW * MAPH);
    var pois = [];
    var list = Object.keys(caps);
    for (var y = 0; y < MAPH; y++) {
      for (var x = 0; x < MAPW; x++) {
        var best = list[0], bd = 1e9;
        list.forEach(function (id) {
          var c = caps[id];
          var d = (x - c.cx) * (x - c.cx) + (y - c.cy) * (y - c.cy);
          if (d < bd) { bd = d; best = id; }
        });
        var reg = caps[best].region, i = y * MAPW + x;
        var n = (Engine.hash(x + ":" + y) % 3);
        tiles[i] = ((caps[best].idx * 3 + n) % 10);
        fog[i] = reg.revealed ? 2 : 0;
      }
    }
    list.forEach(function (id) {
      var c = caps[id];
      mark[c.cy * MAPW + c.cx] = 1; // build plot
      if (c.region.contested) mark[c.cy * MAPW + c.cx + 1] = 2;
      if (!c.region.revealed) {
        mark[c.cy * MAPW + c.cx - 1] = 5;
        pois.push({ kind: "camp", x: c.cx - 1, y: c.cy, ref: id });
      }
    });
    pois.push({ kind: "quest", x: caps[list[0]].cx, y: caps[list[0]].cy - 2,
                ref: "demo", title: "offline demo" });
    return { w: MAPW, h: MAPH, data: tiles, fog: fog, mark: mark,
             caps: caps, pois: pois };
  }

  function unitPos(u, map) {
    var h = Engine.hash(String(u.id));
    if (u.kind === "minion" && state.world) {
      var su = (state.world.units || []).filter(function (x) {
        return x.kind === "hero" &&
          (x.id === u.summoner || (u.lane && x.lane === u.lane));
      })[0];
      if (su) {
        var sp = unitPos(su, map), ma = (h % 628) / 100;
        return { x: sp.x + Math.cos(ma) * TILE * 0.65,
                 y: sp.y + Math.sin(ma) * TILE * 0.65 };
      }
    }
    // unit stands in its lane's region, or wanders around its class capital
    var ids = Object.keys(map.caps);
    var reg = map.caps[u.lane] ? u.lane
      : ids[h % ids.length];
    var c = map.caps[reg];
    var ring = 1 + (h % 3), ang = (h % 628) / 100;
    return { x: (c.cx + Math.cos(ang) * ring) * TILE,
             y: (c.cy + Math.sin(ang) * ring) * TILE };
  }

  function pushFade(x, y, cls) {
    state.fades.push({ x: x, y: y, cls: cls, t0: performance.now() });
    if (state.fades.length > 12) state.fades.shift();
  }

  function syncRenderables() {
    var w = state.world;
    if (!w || !state.map) { state.units = []; state.buildings = [];
                            state.workers = []; return; }
    var prev = {};
    state.units.forEach(function (u) { prev[u.id] = u; });
    // prune selection of ids that despawned since the last snapshot
    state.selAll = state.selAll.filter(function (id) {
      return (w.units || []).some(function (u) { return u.id === id; }); });
    if (state.sel && state.selAll.indexOf(state.sel) < 0)
      state.sel = state.selAll[0] || null;
    var now = performance.now();
    // #136: motion bookkeeping survives resyncs so a unit mid-glide does
    // not snap back to its home tile when a new snapshot lands
    var liveIds = {};
    state.units = (w.units || []).map(function (u) {
      var p = unitPos(u, state.map);
      // glide targets (#127/#136): active queued waypoints walked in FIFO
      // order; no active order -> drift back to the unit's home tile
      var pts = [];
      ((u.orders || [])).forEach(function (o) {
        if (o.state !== "consumed" && typeof o.x === "number" &&
            typeof o.y === "number")
          pts.push({ x: (o.x + .5) * TILE, y: (o.y + .5) * TILE });
      });
      var sig = pts.map(function (q) { return q.x + ":" + q.y; }).join(",");
      var mo = state.motion[u.id] ||
               (state.motion[u.id] = { x: p.x, y: p.y, wi: 0, sig: "" });
      if (mo.sig !== sig) { mo.sig = sig; mo.wi = 0; }
      var tgt = pts.length ? pts[Math.min(mo.wi, pts.length - 1)] : p;
      liveIds[u.id] = 1;
      var ack = state.acks[u.id];
      if (ack && now - ack.t0 > 4000) { delete state.acks[u.id]; ack = 0; }
      var live = u.status_live || u.status;
      if (prev[u.id] && prev[u.id].status_live !== "done" &&
          live === "done") {
        ack = state.acks[u.id] = { text: barkLine(u.cls, 2), t0: now };
      }
      // death animation: a hero that just failed gets a fade marker (#125)
      if (prev[u.id] && prev[u.id].status_live !== "failed" &&
          live === "failed") pushFade(mo.x, mo.y, u.cls);
      return { id: u.id, x: mo.x, y: mo.y, tx: tgt.x, ty: tgt.y,
        pts: pts, moving: false, acting: !!mo.acting,
        cls: u.cls || "Squire", level: u.level || 1,
        kind: u.kind, name: u.name, hp: u.hp, mana: u.mana,
        status_live: live, gate_fail: !!u.gate_fail,
        sel: state.selAll.indexOf(u.id) >= 0,
        bark: ack ? ack.text : (u.bark || null),
        unit: u };
    });
    // despawned units leave a fading corpse marker
    Object.keys(prev).forEach(function (id) {
      if (!w.units.some(function (u) { return u.id === id; })) {
        var p = prev[id];
        if (p.kind === "minion" || p.status_live === "failed" ||
            p.kind === "hero") pushFade(p.x, p.y, p.cls);
      }
    });
    // drop motion entries of units that left the world (#136)
    Object.keys(state.motion).forEach(function (id) {
      if (!liveIds[id]) delete state.motion[id];
    });
    // worker peasants carry from/to + server ts; engine lerps per frame
    // via the snapshot's server->client clock offset
    state.srvClock = { srv: w.now || 0, perf: performance.now() };
    state.workers = w.workers || [];
    // queued waypoints (#127): every order intent with x/y on a hero's
    // queue is a numbered flag chained from the unit through each flag
    state.waypoints = [];
    state.units.forEach(function (u) {
      var ords = (u.unit && u.unit.orders) || [];
      var px = u.x, py = u.y, wn = 0;
      ords.forEach(function (o) {
        if (o.state === "consumed" ||
            typeof o.x !== "number" || typeof o.y !== "number") return;
        var wx = (o.x + .5) * TILE, wy = (o.y + .5) * TILE;
        state.waypoints.push({ x: wx, y: wy,
          n: ++wn, state: o.state, order: o.order,
          ux: px, uy: py });
        px = wx; py = wy;
      });
    });
    // buildings sit on their fixed server-assigned plots (#123)
    var regs = Object.keys(state.map.caps);
    state.buildings = (w.buildings || []).map(function (b, i) {
      var out = { id: b.id, bid: b.id, name: b.name || b.id,
        activity: b.activity,
        region: b.pos && b.pos.region, sel: state.selB === b.id };
      if (b.pos && b.pos.xy) {
        out.x = b.pos.xy[0] * TILE + TILE / 2;
        out.y = b.pos.xy[1] * TILE + TILE / 2;
        return out;
      }
      var c = state.map.caps[out.region] ||
              state.map.caps[regs[i % regs.length]];
      if (!c) return out;
      var h = Engine.hash(b.id);
      out.x = (c.cx + ((h % 5) - 2)) * TILE;
      out.y = (c.cy + ((h >> 4) % 5 - 2)) * TILE;
      return out;
    }).filter(function (b) { return typeof b.x === "number"; });
  }

  // ---- connection ----------------------------------------------------

  function setConn(txt, on) {
    var c = el("conn"); c.textContent = txt;
    c.className = on ? "on" : "off";
  }

  // #135 replay/spectator: body classes come from the snapshot (server
  // is authoritative for mode + role); replay bar reflects /replay state
  function syncReplay(rp) {
    state.rp = rp;
    el("rpp").textContent = rp.playing ? "pause" : "play";
    var sc = el("rpscrub");
    sc.max = rp.total;
    if (document.activeElement !== sc) sc.value = rp.index;
    el("rpinfo").textContent = rp.index + "/" + rp.total +
      (rp.done ? " done" : "");
    var btns = document.querySelectorAll(".rpsp");
    for (var i = 0; i < btns.length; i++)
      btns[i].className = "rpsp" + (+btns[i].dataset.s === rp.speed
        ? " on" : "");
  }

  function applySnapshot(snap) {
    state.snap = snap;
    if (snap.weather) {
      state.weather = snap.weather;
      if (snap.weather.source === "pending" && !state._wxFetched) {
        state._wxFetched = true;
        fetch("/weather", { headers: TOK ? { "X-RTS-Token": TOK } : {} })
          .then(function (r) { return r.ok ? r.json() : null; })
          .then(function (wx) {
            if (wx && wx.ok) { state.weather = wx; renderPanels(); }
          }).catch(function () {});
      }
    }
    document.body.className =
      (snap.mode === "replay" ? "replay " : "") +
      (snap.client_role === "spectator" ? "spectator" : "");
    if (snap.replay) syncReplay(snap.replay);
    syncDecisions();
    state.world = snap.world || null;
    syncUpkeep();
    var m2 = state.world ? state.world.map : null;
    if (m2 && m2.tile_region) {          // authoritative server map (#122)
      if (!state.map || state.map.sig !== m2.sig) state.map = serverMap(m2);
      state.map.fog = new Uint8Array(m2.fog || []);
      state.map.mark = new Uint8Array(m2.mark || []);
      state.map.pois = m2.pois || [];
      state.map.tint = laneTint(m2);
      syncBreaches();
    } else {
      var regs = m2 ? m2.regions : [];
      var key = regs.map(function (r) { return r.id; }).join(",");
      if (!state.map || state.mapKey !== key) {
        state.map = buildMap(regs); state.mapKey = key;
      }
    }
    if (!state._camInit && state.map) {
      var c0 = state.map.caps.root ||
               state.map.caps[Object.keys(state.map.caps)[0]];
      eng.centerOn(c0.cx * TILE, c0.cy * TILE); state._camInit = true;
    }
    // comms scrollback is event-sourced: the snapshot carries the full
    // rebuilt feed (world.feed from replayed events) (#128)
    state.feed = ((snap.world || {}).feed || []).slice().reverse();
    renderFeed();
    syncRenderables();
    renderPanels();
  }

  var pollT = null;
  function connect() {
    if (location.protocol === "file:" || BENCH) return demoMode();
    try {
      var proto = location.protocol === "https:" ? "wss" : "ws";
      var ws = new WebSocket(proto + "://" + location.host + "/ws" +
        (TOK ? "?token=" + encodeURIComponent(TOK) : ""));
      var got = false;
      ws.onopen = function () { setConn("online", true); };
      ws.onclose = function () {
        setConn(got ? "offline" : "polling", false);
        setTimeout(connect, 2000);
      };
      ws.onmessage = function (e) {
        var m = JSON.parse(e.data);
        if (m.type === "snapshot") { got = true; applySnapshot(m.snapshot); }
        else if (m.type === "upsert") {
          got = true; refresh(); noteEvent(m.event); pushPing(m.hint);
          if (m.feed) pushFeed(m.feed);
          if (m.hint && m.hint.kind === "raven") pushRaven(m.hint);
          // #129/#133 tiers: decision = modal+sting; gate-fail = red
          // banner+horn; contested = clash; spawn = soft blip; the rest
          // is feed only
          var hk = m.hint && m.hint.kind;
          if (m.event && m.event.type === "decision.created") {
            var pid = (m.event.payload || {}).id;
            if (pid) state.heardDec[pid] = 1;
            tone("decision");
            notify("rtsd: war council",
                   (m.event.payload || {}).prompt || "decision pending");
          } else if (hk === "fail") {
            failBanner((m.feed && m.feed.text) ||
                       (m.event.tool || m.event.type));
          } else if (m.feed && m.feed.kind === "debrief" &&
              /fail|retreat|unit down/i.test(m.feed.text || "")) {
            failBanner(m.feed.text);
          } else if (hk === "contested") {
            tone("contested");
          } else if (hk === "spawn" || hk === "decision" ||
                     hk === "spell") {
            tone(hk === "decision" ? "decision" :
                 hk === "spawn" ? "spawn" : "order");
          }
        } else if (m.type === "tick") { got = true; applyTick(m); }
        else if (m.type === "replay") syncReplay(m.replay);
        else if (m.type === "weather") { state.weather = m.weather;
          renderPanels(); }
        else if (m.type === "score") showScore(m.score);
      };
      ws.onerror = function () { ws.close(); };
      // polling fallback so PWA/remote clients without WS still update
      if (!pollT) {
        pollT = setInterval(function () {
          if (!got) refresh();
        }, 2000);
      }
    } catch (e) { demoMode(); }
  }

  function refresh() {
    var h = { "X-RTS-Token": TOK };
    fetch("/snapshot", { headers: TOK ? h : {} })
      .then(function (r) { return r.json(); })
      .then(applySnapshot)
      .catch(function () { if (!state.world) demoMode(); });
  }

  function applyTick(m) {
    var d = m.deltas || {};
    if (!state.world) return;
    if (d._map && state.map) {           // tile fog demotions from server
      var fd = d._map.fog || {};
      for (var t in fd) state.map.fog[t] = fd[t];
    }
    state.world.units.forEach(function (u) {
      if (d[u.id]) {
        if (d[u.id].expired) u._gone = true;
        else u.status_live = d[u.id].status_live;
      }
    });
    state.world.units = state.world.units.filter(function (u) {
      return !u._gone; });
    syncRenderables(); renderPanels();
  }

  // Class voice lines from the GDD voice table (fallback when the hero's
  // heartbeat status.json has no `note` - barks never fabricate).
  var BARKS = {
    Knight: ["At your command.", "For the keep.", "Work complete."],
    Ranger: ["On the trail.", "Tracking.", "Prey found."],
    Cleric: ["The gates call.", "Verifying.", "All gates green."],
    Spellbreaker: ["Show me the diff.", "Reviewing.", "Judgment passed."],
    "Far Seer": ["I see far.", "Scouting.", "Report delivered."],
    Archmage: ["A grand design.", "Drafting.", "The plan stands."],
    Runesmith: ["Blueprints ready.", "Forging spec.", "Architecture set."],
    Herald: ["What do users need?", "Writing the PRD.", "Spec authored."],
    Marshal: ["Status report.", "Checking artifacts.", "DONE declared."],
    Enchanter: ["Design calls.", "Styling.", "System specced."],
    Bard: ["A tale to tell.", "Drafting docs.", "Published."],
    Inquisitor: ["Trust nothing.", "Auditing.", "Audit filed."],
    Shadowblade: ["Rules of engagement?", "Probing.", "Target assessed."],
    Scout: ["Eyes open.", "Sweeping.", "Map updated."],
    Squire: ["Ready.", "On it.", "Done, sir."]
  };
  function barkLine(cls, i) {
    var t = BARKS[cls] || BARKS.Squire;
    return t[i];
  }

  var PING_TTL_MS = 6000;
  function pushPing(h) {
    if (!h || !h.xy) return;
    state.pings.push({ x: (h.xy[0] + 0.5) * TILE, y: (h.xy[1] + 0.5) * TILE,
                       kind: h.kind, t0: performance.now() });
    if (state.pings.length > 8) state.pings.shift();
  }
  function livePings() {
    var now = performance.now();
    state.pings = state.pings.filter(function (p) {
      return now - p.t0 < PING_TTL_MS; });
    return state.pings;
  }

  // raven flight: mailbox deposit -> bird arcs sender->recipient (#128)
  function pushRaven(h) {
    if (!h.from || !h.to) return;
    state.ravens.push({ fx: (h.from[0] + .5) * TILE,
                        fy: (h.from[1] + .5) * TILE,
                        tx: (h.to[0] + .5) * TILE,
                        ty: (h.to[1] + .5) * TILE,
                        t0: performance.now() });
    if (state.ravens.length > 8) state.ravens.shift();
  }

  // ---- alert sounds + notifications (#133) ----------------------------
  // Per-tier procedural WebAudio signatures (no asset files, zero-dep).
  // Mute + volume persist in localStorage; M toggles, -/= set volume.
  // Browser Notification API is opt-in via the header button and only
  // fires while the tab is hidden (graceful on deny/unsupported).

  var SNDKEY = "rtsd.snd", VOLKEY = "rtsd.vol", NTFKEY = "rtsd.ntf";
  var snd = { on: localStorage.getItem(SNDKEY) !== "0",
              vol: parseFloat(localStorage.getItem(VOLKEY) || "0.6") };
  if (!(snd.vol > 0)) snd.vol = 0.6;

  function sndUi() {
    el("sndBtn").textContent = "snd:" +
      (snd.on ? Math.round(snd.vol * 100) + "%" : "off");
  }
  function setMute(on) {
    snd.on = on;
    localStorage.setItem(SNDKEY, on ? "1" : "0");
    sndUi();
  }
  function setVol(v) {
    snd.vol = Math.max(0.1, Math.min(1, v));
    localStorage.setItem(VOLKEY, String(Math.round(snd.vol * 100) / 100));
    sndUi();
  }

  var _ac = null, _noiseBuf = null, _amb = null;
  function _ctx() {
    _ac = _ac || new (window.AudioContext || window.webkitAudioContext)();
    if (_ac.state === "suspended") _ac.resume();
    return _ac;
  }
  function _getNoise() {
    var ac = _ctx();
    if (_noiseBuf) return _noiseBuf;
    var sr = ac.sampleRate, len = sr * 2;
    _noiseBuf = ac.createBuffer(1, len, sr);
    var d = _noiseBuf.getChannelData(0), b0 = 0, b1 = 0, b2 = 0;
    for (var i = 0; i < len; i++) {
      var w = Math.random() * 2 - 1;
      b0 = 0.997 * b0 + w * 0.029;
      b1 = 0.985 * b1 + w * 0.032;
      b2 = 0.950 * b2 + w * 0.048;
      d[i] = (b0 + b1 + b2 + w * 0.05) * 0.35; // pink-weighted noise
    }
    return _noiseBuf;
  }
  function _osc(type, f0, f1, delay, dur, vol) {
    var ac = _ctx(), t = ac.currentTime + delay;
    var o = ac.createOscillator(), g2 = ac.createGain();
    o.type = type;
    o.frequency.setValueAtTime(f0, t);
    if (f1 && f1 !== f0)
      o.frequency.exponentialRampToValueAtTime(Math.max(20, f1), t + dur);
    g2.gain.setValueAtTime(0.0001, t);
    g2.gain.exponentialRampToValueAtTime(Math.max(0.0002, vol * snd.vol),
                                         t + 0.015);
    g2.gain.exponentialRampToValueAtTime(0.0001, t + dur);
    o.connect(g2); g2.connect(ac.destination);
    o.start(t); o.stop(t + dur + 0.04);
  }
  // #165 Inharmonic FM metallic synth (anvil, sword ring, bell, armor)
  function _fm(fc, fm, idx, delay, dur, vol) {
    var ac = _ctx(), t = ac.currentTime + delay;
    var car = ac.createOscillator(), mod = ac.createOscillator();
    var mg = ac.createGain(), cg = ac.createGain();
    car.frequency.setValueAtTime(fc, t);
    mod.frequency.setValueAtTime(fm, t);
    mg.gain.setValueAtTime(idx, t);
    mg.gain.exponentialRampToValueAtTime(1, t + dur);
    cg.gain.setValueAtTime(0.0001, t);
    cg.gain.exponentialRampToValueAtTime(Math.max(0.0002, vol * snd.vol),
                                         t + 0.008);
    cg.gain.exponentialRampToValueAtTime(0.0001, t + dur);
    mod.connect(mg); mg.connect(car.frequency);
    car.connect(cg); cg.connect(ac.destination);
    mod.start(t); car.start(t);
    mod.stop(t + dur + 0.04); car.stop(t + dur + 0.04);
  }
  // #165 Filtered noise burst (sword impact, steam hiss, key clack, thunder)
  function _noise(type, freq, q, delay, dur, vol) {
    var ac = _ctx(), t = ac.currentTime + delay;
    var src = ac.createBufferSource();
    src.buffer = _getNoise();
    src.loop = true;
    var flt = ac.createBiquadFilter(), g2 = ac.createGain();
    flt.type = type || "bandpass";
    flt.frequency.setValueAtTime(freq, t);
    flt.Q.setValueAtTime(q || 1.5, t);
    g2.gain.setValueAtTime(0.0001, t);
    g2.gain.exponentialRampToValueAtTime(Math.max(0.0002, vol * snd.vol),
                                         t + 0.015);
    g2.gain.exponentialRampToValueAtTime(0.0001, t + dur);
    src.connect(flt); flt.connect(g2); g2.connect(ac.destination);
    src.start(t, Math.random()); src.stop(t + dur + 0.04);
  }
  // #165 Karplus-Strong plucked string synthesis (bowstring, lute, harp)
  function _pluck(freq, delay, dur, vol) {
    var ac = _ctx(), t = ac.currentTime + delay, sr = ac.sampleRate;
    var n = Math.max(2, Math.round(sr / freq)), samples = Math.round(sr * dur);
    var buf = ac.createBuffer(1, samples, sr), ch = buf.getChannelData(0);
    var ring = new Float32Array(n);
    for (var i = 0; i < n; i++) ring[i] = Math.random() * 2 - 1;
    var p = 0;
    for (var s = 0; s < samples; s++) {
      var nxt = (p + 1) % n;
      ch[s] = ring[p];
      ring[p] = 0.496 * (ring[p] + ring[nxt]);
      p = nxt;
    }
    var src = ac.createBufferSource(), g2 = ac.createGain();
    src.buffer = buf;
    g2.gain.setValueAtTime(vol * snd.vol, t);
    src.connect(g2); g2.connect(ac.destination);
    src.start(t);
  }
  // #165 Continuous environmental wind & rain filter bank modulated by weather
  function syncAmbience() {
    if (!snd.on || !_ac) {
      if (_amb) {
        try { _amb.wGain.gain.setValueAtTime(0.0001, _ac.currentTime);
              _amb.rGain.gain.setValueAtTime(0.0001, _ac.currentTime); }
        catch (e) {}
      }
      return;
    }
    if (!_amb) {
      try {
        var ac = _ctx(), src = ac.createBufferSource();
        src.buffer = _getNoise(); src.loop = true;
        var wFlt = ac.createBiquadFilter(), wGain = ac.createGain();
        wFlt.type = "bandpass"; wFlt.Q.value = 2.2; wGain.gain.value = 0.0001;
        var rFlt = ac.createBiquadFilter(), rGain = ac.createGain();
        rFlt.type = "bandpass"; rFlt.frequency.value = 2100; rFlt.Q.value = 0.9;
        rGain.gain.value = 0.0001;
        src.connect(wFlt); wFlt.connect(wGain); wGain.connect(ac.destination);
        src.connect(rFlt); rFlt.connect(rGain); rGain.connect(ac.destination);
        src.start();
        _amb = { wFlt: wFlt, wGain: wGain, rGain: rGain };
      } catch (e) { return; }
    }
    var wx = state.weather || {};
    var kph = wx.wind_kph || 12, cond = wx.condition || "cloudy";
    var nowT = _ac.currentTime;
    _amb.wFlt.frequency.setTargetAtTime(160 + kph * 11, nowT, 0.2);
    var wVol = Math.min(0.035, (0.006 + kph * 0.0005)) * snd.vol;
    _amb.wGain.gain.setTargetAtTime(wVol, nowT, 0.25);
    var rVol = (cond === "storm" ? 0.032 : cond === "rain" ? 0.018 : 0.0001) *
               snd.vol;
    _amb.rGain.gain.setTargetAtTime(rVol, nowT, 0.25);
  }

  // tier & theme signatures (#133/#165): Battlefield vs Office foley
  var SND = {
    decision: function () {            // council sting: brass fanfare
      _fm(523, 261, 180, 0, .16, .05);
      _fm(659, 329, 180, .12, .24, .05);
    },
    breach: function () {              // gate-fail horn: low war-horn + rumble
      _osc("sawtooth", 196, 92, 0, .52, .07);
      _osc("sawtooth", 147, 73, .28, .55, .06);
      _noise("lowpass", 140, 1.2, 0, .5, .05);
    },
    spawn: function () {               // hero summon chord
      _pluck(440, 0, .28, .05);
      _osc("sine", 660, 990, .05, .18, .04);
    },
    contested: function () {           // metallic sword-on-shield clash
      _fm(780, 1120, 420, 0, .14, .05);
      _noise("bandpass", 2600, 2.5, 0, .09, .05);
    },
    upkeep: function () {              // advisor warn: two soft tones
      _osc("triangle", 520, 520, 0, .09, .05);
      _osc("triangle", 392, 392, .12, .14, .05);
    },
    order: function () {               // boot march thud / office key click
      if (Theme.get().name === "office") {
        _noise("bandpass", 3200, 3.0, 0, .03, .04);
      } else {
        _osc("triangle", 140, 65, 0, .07, .05);
        _osc("sine", 880, 980, .02, .05, .03);
      }
    },
    select_hero: function (sub) {      // class-aware & theme-aware selection
      if (Theme.get().name === "office") {
        _noise("bandpass", 2800, 2.8, 0, .03, .04);
        _osc("sine", 880, 1174, .03, .08, .03);
        return;
      }
      if (sub === "Ranger" || sub === "Scout" || sub === "Bard") {
        _pluck(392, 0, .28, .05);
        _pluck(587, .06, .32, .05);
      } else if (sub === "Archmage" || sub === "Far Seer" ||
                 sub === "Enchanter") {
        _fm(880, 1320, 160, 0, .22, .04);
      } else {
        _fm(523, 784, 240, 0, .16, .05);
        _osc("triangle", 440, 659, .04, .14, .04);
      }
    },
    select_bld: function (bid) {       // per-structure acoustic signature (#165)
      var isOff = Theme.get().name === "office";
      if (bid === "runeforge") {
        if (isOff) {                   // printer stepper motor whir
          _osc("sawtooth", 320, 480, 0, .14, .04);
          _noise("bandpass", 1800, 2, .04, .12, .04);
        } else {                       // blacksmith anvil hammer clang!
          _fm(587, 830, 520, 0, .32, .06);
          _fm(1174, 1660, 300, .01, .22, .04);
        }
      } else if (bid === "tavern") {
        if (isOff) {                   // espresso steamer hiss
          _noise("highpass", 3400, 1.2, 0, .22, .05);
        } else {                       // tavern lute chord
          _pluck(293, 0, .35, .05);
          _pluck(440, .05, .35, .05);
          _pluck(587, .10, .40, .05);
        }
      } else if (bid === "altar") {
        if (isOff) {                   // water-cooler bubble glug
          _osc("sine", 260, 520, 0, .09, .05);
          _osc("sine", 310, 640, .11, .09, .05);
        } else {                       // cathedral choir triad
          _osc("sine", 261.6, 261.6, 0, .35, .04);
          _osc("triangle", 329.6, 329.6, .03, .35, .04);
          _osc("sine", 392.0, 392.0, .06, .38, .04);
        }
      } else if (bid === "marketplace") {
        _fm(1568, 2349, 200, 0, .12, .04);
        _fm(2093, 3136, 200, .07, .16, .04);
      } else if (bid === "portal") {
        _osc("sawtooth", 110, 220, 0, .28, .05);
        _fm(440, 311, 280, .04, .26, .04);
      } else if (bid === "library") {
        _pluck(659, 0, .28, .04);
        _fm(1046, 1568, 120, .06, .24, .04);
      } else {
        _fm(392, 587, 180, 0, .20, .05);
      }
    },
    attack: function () {              // metallic sword clash + war drum
      _noise("bandpass", 2400, 2.2, 0, .08, .06);
      _fm(680, 960, 450, 0, .14, .05);
      _osc("triangle", 130, 55, .02, .14, .06);
    },
    gather: function () {              // pickaxe strike + gold coin chime
      _fm(1318, 1975, 220, 0, .09, .04);
      _fm(1760, 2637, 180, .08, .14, .04);
    },
    spell: function () {               // arcane shimmer + harp glissando
      _pluck(523, 0, .25, .04);
      _pluck(659, .05, .25, .04);
      _fm(1046, 1568, 160, .10, .28, .05);
    },
    thunder: function () {             // multi-tap brown/pink noise thunder
      _noise("lowpass", 95, 0.9, 0, .65, .08);
      _osc("sawtooth", 82, 34, .05, .55, .06);
    },
    bird: function () {                // daytime meadow bird FM chirp
      _osc("sine", 1760, 2480, 0, .07, .025);
      _osc("sine", 2320, 1840, .09, .08, .025);
    }
  };
  function tone(kind, sub) {
    if (!snd.on) return;
    try {
      (SND[kind] || SND.order)(sub);
      syncAmbience();
    } catch (e) {}
  }

  function pushFx(kind, x, y, text, color, dur) {
    state.fx.push({ kind: kind, x: x, y: y, text: text || "",
                    color: color || "#ffd54a", dur: dur || 2.0,
                    t0: performance.now() });
    if (state.fx.length > 40) state.fx.shift();
  }

  function ntfOn() {
    return localStorage.getItem(NTFKEY) === "1" &&
      "Notification" in window && Notification.permission === "granted";
  }
  function ntfUi() {
    el("ntfBtn").textContent = "notify:" + (!("Notification" in window)
      ? "n/a" : Notification.permission === "denied" ? "denied"
      : ntfOn() ? "on" : "off");
  }
  function notify(title, body) {
    if (!ntfOn() || !document.hidden) return;
    try { new Notification(title, { body: body || "" }); } catch (e) {}
  }

  // Pending decisions annotated with expiry: rts-decision.py --wait fails
  // closed after `timeout` seconds, so a stale pending file is shown as
  // "timed out: deny applied" and never re-alarms.
  function pendingDecs() {
    var now = Date.now() / 1000;
    return ((state.snap || {}).decisions || []).map(function (d) {
      d._expired = !!(d.timeout && d.created_at &&
                      now - d.created_at > d.timeout);
      return d;
    });
  }

  function reqUnit(d) {   // requesting hero -> real world unit (portrait)
    var ref = d.requester, units = (state.world || {}).units || [];
    if (!ref) return null;
    var u = units.filter(function (x) {
      return x.id === ref || x.name === ref; })[0];
    if (!u) {
      var best = -1;
      units.forEach(function (x) {
        if (x.lane === ref && (x.last_seen || 0) > best) {
          best = x.last_seen; u = x; }
      });
    }
    return u || null;
  }

  function decAlarm(d) {  // new pending decision: flash + sound + gold ping
    tone("decision");
    notify("rtsd: war council", d.prompt || d.kind || "decision pending");
    var th = ((state.world || {}).buildings || []).filter(function (b) {
      return b.id === "town-hall"; })[0];
    if (th && th.pos && th.pos.xy)
      state.pings.push({ x: (th.pos.xy[0] + .5) * TILE,
                         y: (th.pos.xy[1] + .5) * TILE,
                         kind: "decision", t0: performance.now() });
  }

  function syncDecisions() {   // diff pending ids; works on WS and polling
    var decs = pendingDecs(), ids = {};
    decs.forEach(function (d) { ids[d.id] = 1; });
    if (state.seenDec) {
      decs.forEach(function (d) {
        if (!state.seenDec[d.id] && !state.heardDec[d.id] && !d._expired)
          decAlarm(d);
      });
    }
    state.seenDec = ids;
    if (state.decActive && !ids[state.decActive]) state.decActive = null;
  }

  // ---- economy alerts (#131) ------------------------------------------
  // Upkeep tier is derived server-side from the real context-budget
  // thresholds each snapshot; the HUD diffs successive snapshots so a
  // crossing fires an alert within one tick: feed line + portrait-bar
  // flash + tone + a minimap ping on the town hall (same pattern as the
  // war council diff above).
  var UPKEEP_ORDER = { "none": 0, "low": 1, "high": 2, "clear-now": 3 };

  function syncUpkeep() {
    var r = (state.world || {}).resources || {};
    var cur = r.upkeep || "none";
    if (state.prevUpkeep === null || state.prevUpkeep === cur) {
      state.prevUpkeep = cur;
      return;
    }
    var worse = (UPKEEP_ORDER[cur] || 0) > (UPKEEP_ORDER[state.prevUpkeep] || 0);
    var msg = "upkeep " + state.prevUpkeep + " -> " + cur +
      " (context " + (r.lumber_pct | 0) + "% of window)";
    pushFeed({ t: Date.now() / 1000, kind: "econ", who: "Keep",
               cls: null, uid: null, text: msg });
    var rs = el("res");
    rs.classList.remove("flash");
    void rs.offsetWidth;               // restart the CSS animation
    rs.classList.add("flash");
    if (worse) {
      tone("upkeep");
      notify("rtsd: upkeep " + cur, msg);
      var th = ((state.world || {}).buildings || []).filter(function (b) {
        return b.id === "town-hall"; })[0];
      if (th && th.pos && th.pos.xy)
        state.pings.push({ x: (th.pos.xy[0] + .5) * TILE,
                           y: (th.pos.xy[1] + .5) * TILE,
                           kind: "econ", t0: performance.now() });
    }
    state.prevUpkeep = cur;
  }

  // ---- breach alarms (#133) -------------------------------------------
  // A ledger gate fail = a wall breach: the failed ledger's territory
  // glows red on map+minimap until every gate in it passes again. Breach
  // state is snapshot-derived server-side (world.breaches) so polling
  // PWA/remote clients see the same alarm state without push infra.

  function syncBreaches() {
    var br = (state.world || {}).breaches || [];
    var ids = {};
    br.forEach(function (b) { ids[b.ledger] = 1; });
    if (state.seenBreach) {
      br.forEach(function (b) {
        if (!state.seenBreach[b.ledger]) breachAlarm(b); });
      Object.keys(state.seenBreach).forEach(function (l) {
        if (!ids[l])
          pushFeed({ t: Date.now() / 1000, kind: "breach",
                     who: "Watchtower", cls: null, uid: null,
                     text: "breach sealed: " + l + " gates green" });
      });
    }
    state.seenBreach = ids;
    // territory glow mask: every tile of a breached region
    if (state.map && state.map.tileRegion) {
      var rmask = {};
      br.forEach(function (b) {
        var ri = state.map.regionIds.indexOf(b.region);
        if (ri >= 0) rmask[ri] = 1;
      });
      var bt = new Uint8Array(state.map.w * state.map.h);
      for (var i = 0; i < bt.length; i++)
        if (rmask[state.map.tileRegion[i]]) bt[i] = 1;
      state.map.breach = bt;
    }
  }

  function breachAlarm(b) {   // new breach: horn + banner + ping + notify
    tone("breach");
    failBanner("wall breach in " + b.region + " (" + b.ledger + ": " +
               b.gates.join(",") + " failed)");
    pushFeed({ t: Date.now() / 1000, kind: "breach", who: "Watchtower",
               cls: null, uid: null,
               text: "BREACH: " + b.region + " wall down - " + b.ledger +
                 " gate " + b.gates.join(",") + " failed" });
    state.pings.push({ x: (b.xy[0] + .5) * TILE, y: (b.xy[1] + .5) * TILE,
                       kind: "fail", t0: performance.now() });
    notify("rtsd: wall breach",
           b.ledger + " gate fail in " + b.region);
  }

  // gate-fail tier: red breach banner + low tone (ping comes from the
  // event hint); auto-clears - the ledger stays the persistent record
  function failBanner(msg) {
    var b = el("banner");
    b.textContent = "BREACH: " + msg;
    b.className = "on";
    tone("breach");
    clearTimeout(state._bt);
    state._bt = setTimeout(function () { b.className = ""; }, 6000);
  }

  function decHtml(d, active) {
    var opts = (d.options && d.options.length) ? d.options
                                             : ["allow", "deny"];
    var deny = opts.length - 1;
    var u = reqUnit(d);
    var h = "<div class='dec" + (d._expired ? " exp" : "") + "'" +
      (active ? "" : " data-decid='" + esc(d.id) + "'") + ">";
    if (u)
      h += "<div class='req'><span class='rface'>" +
        esc((u.cls || "?")[0]) + "</span> <b>" + esc(u.name || u.id) +
        "</b> <span class='meta'>" + esc(u.cls || "") +
        " asks the council</span></div>";
    else if (d.requester)
      h += "<div class='req meta'>requester: " + esc(d.requester) +
        "</div>";
    h += "<b>" + esc(d.kind || "decision") + "</b>" +
      "<div class='meta'>" + esc(d.prompt || d.summary || "") + "</div>";
    if (d._expired)
      h += "<div class='meta'>timed out - deny applied (fail-closed)</div>";
    else if (d.timeout)
      h += "<div class='meta'>timeout " + esc(String(d.timeout)) +
        "s -> last option (deny-safe)</div>";
    h += opts.map(function (o, i) {
      var def = i === deny;
      return "<button data-dec='" + esc(d.id) + "' data-idx='" + i + "'" +
        (def ? " class='denydef' title='deny-safe default on timeout'"
             : "") + ">" + esc(o) + (def ? " *" : "") + "</button>";
    }).join("") + "</div>";
    return h;
  }

  function noteEvent(ev) {
    // last-event camera jump target: the unit the event most plausibly owns
    var w = state.world;
    if (w && ev.type === "hook.posttooluse") {
      var u = w.units.filter(function (x) { return x.kind === "hero"; })[0];
      if (u) state.lastEventPos = unitPos(u, state.map);
    }
  }

  // ---- demo world (offline only) --------------------------------------

  function demoWorld(nUnits, nBld) {
    var regs = [];
    ["scripts", "skills", "extensions", "agents", "docs",
     "tests", "data", ".devin"].forEach(function (id, i) {
      regs.push({ id: id, revealed: i < 5, activity: i,
                  contested: i === 2 ? 2 : 0 });
    });
    var classes = ["Knight", "Ranger", "Cleric", "Spellbreaker", "Far Seer",
      "Archmage", "Runesmith", "Herald", "Marshal", "Enchanter", "Bard",
      "Inquisitor", "Shadowblade"];
    var units = [];
    for (var i = 0; i < nUnits; i++) {
      var cls = classes[i % classes.length];
      units.push({ id: "demo-" + i, kind: "hero", cls: cls,
        name: cls + "-" + (1 + (i / classes.length | 0)),
        lane: regs[i % regs.length].id, hp: 30 + (i * 37 % 70),
        mana: i % 4 === 0 ? 45 + (i % 60) : null,
        status_live: i % 11 === 0 ? "failed" : "running",
        gate_fail: i % 11 === 0 });
    }
    var blds = [];
    ["town-hall", "barracks", "tavern", "library", "watchtower", "runeforge",
     "vault", "portal", "marketplace", "altar", "trophy-hall"]
      .forEach(function (b, i) {
        for (var k = 0; k < (nBld > 11 ? 2 : 1); k++)
          blds.push({ id: b + (k ? "-" + k : ""), activity: i + k });
      });
    return { now: Date.now() / 1000,
      started: Date.now() / 1000 - 400,   // demo day/night anchor (#136)
      units: units, buildings: blds,
      breaches: [],
      resources: { gold: 0, lumber_pct: 0, supply_used: nUnits,
                   supply_heroes: nUnits, supply_minions: 0,
                   supply_cap: 8, upkeep: "low", income_min: 0,
                   income_last5: [],
                   thresholds: { warn: 60, crit: 75, clear: 80 },
                   window: 0 },
      quests: [], map: { regions: regs, workers_active: 4 } };
  }

  function demoMode() {
    if (state.demo) return;
    state.demo = true;
    setConn("OFFLINE DEMO", false);
    var n = BENCH ? 200 : 60, nb = BENCH ? 20 : 11;
    state.snap = { demo: true };
    state.world = demoWorld(n, nb);
    state.map = buildMap(state.world.map.regions);
    state.mapKey = "demo";
    var c0 = state.map.caps[Object.keys(state.map.caps)[0]];
    eng.centerOn(c0.cx * TILE, c0.cy * TILE);
    state._camInit = true;
    syncRenderables(); renderPanels();
    logFeed("demo world: no daemon at " + location.host +
            " - start rtsd.py to go live");
  }

  // ---- HUD ------------------------------------------------------------

  function renderPanels() {
    var w = state.world || { units: [], quests: [], resources: {} };
    var th = Theme.get(), r = w.resources || {};
    el("res").textContent = w.resources
      ? ("GOLD ~" + (r.gold | 0) + " +" + (r.income_min | 0) + "/m" +
         "  LUMBER " + (r.lumber_pct | 0) +
         "%  SUPPLY " + r.supply_used + "/" + r.supply_cap +
         (r.supply_minions ? "+" + r.supply_minions : "") +
         "  UPKEEP " + (r.upkeep || "-"))
      : "";
    el("res").title = w.resources
      ? ("est tokens spent this session; +" + (r.income_min | 0) +
         " tok/min last 60s\ncontext window " + (r.window | 0) +
         " tokens, thresholds " + (r.thresholds ?
           r.thresholds.warn + "/" + r.thresholds.crit + "/" +
           r.thresholds.clear + "%" : "-") +
         "\nsupply: " + (r.supply_heroes | 0) + " heroes + " +
         (r.supply_minions | 0) + " minions vs cap " + r.supply_cap)
      : "";
    // economy pane (#131): every figure comes from the snapshot, which
    // is itself derived from events.jsonl + data/context-budget.json +
    // data/model-context-windows.json - nothing fabricated
    if (el("econbody")) {
      var th2 = r.thresholds || {};
      var mx = Math.max.apply(null, (r.income_last5 || [1]).concat([1]));
      el("econbody").innerHTML =
        "<div class='meta'>gold ~" + (r.gold | 0) + " est tokens " +
        "(+" + (r.income_min | 0) + "/min)</div>" +
        "<div class='ebars'>" + (r.income_last5 || []).map(function (v) {
          return "<span class='ebar' style='height:" +
            Math.max(1, Math.round(12 * v / mx)) + "px' title='~" +
            (v | 0) + " tok'></span>";
        }).join("") + "</div>" +
        "<div class='meta'>lumber " + (r.lumber_pct | 0) + "% of " +
        (r.window | 0) + "-tok window (warn " + (th2.warn | 0) +
        " / crit " + (th2.crit | 0) + " / clear " + (th2.clear | 0) +
        "%)</div>" +
        "<div class='meta'>supply " + (r.supply_heroes | 0) +
        " heroes + " + (r.supply_minions | 0) + " minions / cap " +
        (r.supply_cap | 0) + "</div>" +
        "<div class='meta'>upkeep " + esc(r.upkeep || "-") + "</div>";
    }
    // quest log (#130): WC3-style main/side split; every row maps to a
    // real .devin/scratch issue (Status/Blocked by) plus its ledger gates
    var qs2 = w.quests || (state.snap || {}).tasks || [];
    var main = qs2.filter(function (t) {
      return t.kind === "main" || t.id === "main-quest"; });
    var side = qs2.filter(function (t) {
      return main.indexOf(t) < 0; });
    var qrow = function (t) {
      var g = t.gates;
      var prog = g ? " gates " + g.pass + "/" + g.total +
        (g.fail ? " (" + g.fail + " fail)" : "") : "";
      var who = (t.assignees || []).map(function (id) {
        var uu = (w.units || []).filter(function (x) {
          return x.id === id; })[0];
        return uu ? (uu.name || id) : id;
      });
      return "<div class='task " +
        (t.blocked ? "blocked" : "") + (t.done ? " done" : "") +
        (t.failed ? " failed" : "") +
        "' draggable='true' data-quest='" + esc(t.id) + "'>" +
        "<span class='id'>" + esc(t.effort) + "/" + esc(t.id) + "</span> " +
        "<b>" + esc(t.title) + "</b>" +
        (t.done ? " <span class='qstamp'>*</span>" : "") +
        "<br><span class='meta'>" + esc(t.status) + prog +
        (t.deps && t.deps.length ?
          " / needs " + esc(t.deps.join(" <- ")) : "") +
        (t.blocked_by && !t.deps.length ?
          " / blocked_by: " + esc(t.blocked_by) : "") +
        (who.length ? " / assigned: " + esc(who.join(",")) : "") +
        "</span></div>";
    };
    el("tlist").innerHTML =
      (main.length
        ? "<div class='qhead'>MAIN QUEST</div>" + main.map(qrow).join("")
        : "<span class='meta'>no main quest - type a goal below</span>") +
      "<div class='qhead'>SIDE QUESTS</div>" +
      (side.map(qrow).join("") || "<span class='meta'>no quests</span>") +
      "<div class='meta qhint'>drag a quest onto a hero to assign</div>";
    // portrait / selection (unit or building inspector); multi-select
    // shows a combined strip of the selected heroes (#126)
    var u = (w.units || []).filter(function (x) {
      return x.id === state.sel; })[0];
    if (state.selAll.length > 1) {
      var selUnits = state.units.filter(function (x) {
        return state.selAll.indexOf(x.id) >= 0; });
      el("portrait").innerHTML =
        "<b>" + selUnits.length + " units selected</b>" +
        " <span class='meta'>(shared orders: move/stop - " +
        "Tab cycles)</span><br>" + selUnits.map(function (x) {
          return "<span class='slot" +
            (x.id === state.sel ? " pri" : "") + "' title='" +
            esc(x.id) + "'>" + esc(x.name || x.id) +
            " <span class='meta'>" + esc(x.cls) + " " +
            (x.hp == null ? "-" : x.hp) + "hp</span></span>";
        }).join(" ");
    } else {
      el("portrait").innerHTML = u ? portraitHtml(u) :
        (state.bDetail ? buildingHtml(state.bDetail) :
         (state.selB ? "<b>" + esc(state.selB) + "</b>" :
          "<span class='meta'>nothing selected</span>"));
    }
    renderCard(u);
    // #159 Live Weather HUD button (city + temp + condition + wind)
    if (el("wxBtn")) {
      var wx = state.weather;
      if (wx && wx.city) {
        var mTag = wx.mode && wx.mode !== "live" ? " [" + wx.mode + "]" : "";
        el("wxBtn").textContent = wx.city + " " +
          (typeof wx.temp_c === "number" ? wx.temp_c.toFixed(1) : "18") +
          "C " + (wx.label || wx.condition || "Clear") + " " +
          Math.round(wx.wind_kph || 12) + "km/h " +
          (wx.wind_cardinal || "") + mTag;
        var hrs = (wx.hourly || []).map(function (h) {
          return h.time + " " + h.temp_c + "C " + h.condition +
            " (" + h.pop + "% rain, " + h.wind_kph + "km/h)";
        }).join("\n");
        el("wxBtn").title = "Location: " + wx.city + ", " +
          (wx.region || "") + " (" + wx.lat + ", " + wx.lon + ")\n" +
          "Condition: " + (wx.label || wx.condition) +
          " | Humidity: " + (wx.humidity || 70) + "% | Clouds: " +
          (wx.cloud_pct || 0) + "%\nWind: " + (wx.wind_kph || 0) +
          " km/h (gusts " + (wx.wind_gust_kph || 0) + " km/h) " +
          (wx.wind_cardinal || "") + " (" + (wx.wind_deg || 0) + " deg)\n" +
          (hrs ? "Forecast:\n" + hrs + "\n" : "") +
          "Click to cycle weather mode (live/rain/storm/snow/fog/clear/windy)";
      }
    }
    // #159 WC3 Top-Left Hero Roster Bar
    if (el("herobar")) {
      var heroes = state.units.filter(function (x) {
        return x.kind === "hero"; });
      el("herobar").innerHTML = heroes.slice(0, 8).map(function (h) {
        var ue = (th.units && th.units[h.cls]) || { bg: "#3a5a40", glyph: "H" };
        var hp = typeof h.hp === "number" ? h.hp : 100;
        var mp = typeof h.mana === "number" ? h.mana : 100;
        var hcol = hp > 50 ? "#3fb950" : hp > 25 ? "#d29922" : "#f85149";
        return "<div class='hcard" + (h.sel ? " sel" : "") +
          "' data-hid='" + esc(h.id) + "' title='" +
          esc((h.name || h.id) + " (" + h.cls + " Lv" + (h.level || 1) +
              ") - click select, dbl-click center") + "'>" +
          "<div class='hico' style='background:" + esc(ue.bg) + "'>" +
          esc(ue.glyph || h.cls[0]) +
          "<span class='hlv'>" + (h.level || 1) + "</span></div>" +
          "<div class='hinfo'><div class='hname'>" +
          esc(h.name || h.id) + "</div>" +
          "<div class='hbar'><span style='width:" + hp + "%;background:" +
          hcol + "'></span></div>" +
          "<div class='hbar'><span style='width:" + mp +
          "%;background:#58a6ff'></span></div></div></div>";
      }).join("");
    }
    // #159 AoE3 Top-Right Building Quick-Select Strip
    if (el("bldbar")) {
      el("bldbar").innerHTML = state.buildings.map(function (b) {
        var be = (th.buildings && th.buildings[b.bid]) || { glyph: "B" };
        var shortName = (b.name || b.id).replace("Trophy Hall", "Trophy")
          .replace("Marketplace", "Market").replace("Watchtower", "Tower");
        return "<div class='bchip" + (state.selB === b.id ? " sel" : "") +
          "' data-bid='" + esc(b.id) + "' title='" +
          esc((b.name || b.id) + " (used " + (b.activity || 0) +
              "x) - click inspect, dbl-click center") + "'><b>" +
          esc(be.glyph || "B") + "</b>" + esc(shortName) + "</div>";
      }).join("");
    }
    // control-group pips: only non-empty groups are shown (#126)
    el("grps").innerHTML = Object.keys(state.groups).sort().map(
      function (n) {
        var alive = state.groups[n].filter(function (id) {
          return state.selAll.indexOf(id) >= 0 ||
            state.units.some(function (x) { return x.id === id; }); });
        if (!alive.length) return "";
        var on = alive.length &&
          alive.every(function (id) {
            return state.selAll.indexOf(id) >= 0; });
        return "<button class='gpip" + (on ? " on" : "") +
          "' data-grp='" + n + "' title='group " + n + " (" +
          alive.length + ")'>" + n + "</button>";
      }).join("");
    // war council (#129/#159): only auto-open when a LIVE (non-expired)
    // decision is pending and not manually closed; expired decisions stay
    // accessible via the header alert chips without blocking the map!
    var decs = pendingDecs();
    var hasLiveDec = decs.some(function (d) { return !d._expired; });
    el("council").classList.toggle(
      "on", decs.length > 0 && (hasLiveDec || state._forceCouncil) &&
            !state.councilClosed);
    if (!decs.some(function (d) { return d.id === state.decActive; }))
      state.decActive = decs.length ? decs[0].id : null;
    var act = decs.filter(function (d) {
      return d.id === state.decActive; })[0];
    el("decs").innerHTML = act ? decHtml(act, true) : "";
    el("decsStack").innerHTML = decs.filter(function (d) {
      return d !== act; }).map(function (d) {
        return decHtml(d, false); }).join("");
    // #133 alert stack severity order: active wall breaches (gate fails)
    // outrank pending council decisions; both outrank info pings
    var br = w.breaches || [];
    el("alerts").innerHTML = (decs.length + br.length) ?
      "<span class='abadge'>alerts:" + (decs.length + br.length) +
      "</span>" +
      br.map(function (b) {
        return "<span class='achip brc' data-breg='" + esc(b.region) +
          "' title='breach: " + esc(b.ledger) + " gates " +
          esc(b.gates.join(", ")) + " - glows until green'>!" +
          esc(b.region) + "</span>";
      }).join("") +
      decs.map(function (d) {
        var u = reqUnit(d);
        var label = u ? (u.name || u.id)
                      : (d.requester || d.kind || d.id);
        return "<span class='achip" + (d._expired ? " exp" : "") +
          (d.id === state.decActive ? " on" : "") + "' data-dec='" +
          esc(d.id) + "' title='" + esc(d.prompt || "") + "'>" +
          esc(label) + "</span>";
      }).join("") : "";
    // idle-worker button (#127): real count from world.idle
    var nIdle = (w.idle || []).length;
    el("idleBtn").textContent = "idle:" + nIdle;
    el("idleBtn").disabled = !nIdle;
    el("themeBtn").textContent = "theme: " + th.name;
    // #164 Beveled Portrait HP/MP/XP Bars + WC3 6-Slot Runed Inventory Grid
    var rawU = u && u.unit ? u.unit : u;
    if (el("pbarHp")) {
      var hpV = rawU && typeof rawU.hp === "number" ? rawU.hp : 100;
      var mpV = rawU && typeof rawU.mana === "number" ? rawU.mana : 100;
      var lvV = rawU ? (rawU.level || 1) : 1;
      var xpV = rawU ? Math.min(100, ((rawU.xp || 20) % 100)) : 0;
      el("pbarHp").innerHTML = "<span style='width:" + hpV +
        "%;background:" + (hpV > 50 ? "#3fb950" : hpV > 25 ? "#d29922" : "#f85149") +
        "'></span><b>HP " + hpV + "/100</b>";
      el("pbarMp").innerHTML = "<span style='width:" + mpV +
        "%;background:#58a6ff'></span><b>MP " + mpV + "/100</b>";
      el("pbarXp").innerHTML = "<span style='width:" + xpV +
        "%;background:#d4a72c'></span><b>Lv" + lvV + " (" +
        (rawU ? (rawU.xp || 0) : 0) + "xp)</b>";
    }
    if (el("invgrid")) {
      var invItems = (rawU && rawU.inventory) || [];
      var invHtml = "";
      for (var is = 0; is < 6; is++) {
        var itm = invItems[is];
        if (itm) {
          var tip = (itm.ledger || "gate") + "/" + (itm.gate || "?") +
            (itm.quest ? " [quest " + itm.quest + "]" : "") + " - " +
            (itm.evidence || "verified");
          invHtml += "<div class='islot filled" +
            (itm.quest ? " qloot" : "") + "' data-tip='" + esc(tip) +
            "' title='" + esc(tip) + "'><span class='inum'>" +
            (is + 1) + "</span><b>" +
            esc(String(itm.gate || "G").slice(0, 3)) + "</b></div>";
        } else {
          invHtml += "<div class='islot' data-tip='Empty Runed Slot " +
            (is + 1) + " (populated by verified ledger gate loot)'><span class='inum'>" +
            (is + 1) + "</span><span>-</span></div>";
        }
      }
      el("invgrid").innerHTML = invHtml;
    }
    renderTech(u);
    renderGameMenu();
  }

  function renderGameMenu() {
    var box = el("gmBox");
    if (!box || !el("gamemenu").classList.contains("on")) return;
    var wx = state.weather || {};
    var curMode = wx.mode || "live";
    var modes = ["live", "clear", "overcast", "rain", "storm", "snow", "fog", "windy"];
    var h = "<h2><span>GAME MENU &amp; WEATHER FORECAST (F10)</span>" +
      "<button id='gmClose'>Resume (ESC)</button></h2>" +
      "<div class='meta'><b>Local Forecast:</b> " + esc(wx.city || "Local") +
      ", " + esc(wx.region || "") + " (" + (wx.temp_c || 18) + "C, " +
      esc(wx.label || wx.condition || "Clear") + ", Wind " +
      (wx.wind_kph || 12) + " km/h " + esc(wx.wind_cardinal || "") +
      ", Gusts " + (wx.wind_gust_kph || 18) + " km/h, Clouds " +
      (wx.cloud_pct || 0) + "%)</div>" +
      "<div class='qhead'>WEATHER MODE OVERRIDE</div><div class='gmgrid'>" +
      modes.map(function (m) {
        return "<button data-wxm='" + m + "'" +
          (curMode === m ? " class='on'" : "") + ">" + m + "</button>";
      }).join("") + "</div>";
    if (wx.hourly && wx.hourly.length) {
      h += "<div class='qhead'>HOURLY FORECAST (" + esc(wx.city || "") + ")</div>" +
        "<div style='display:flex;gap:6px;overflow-x:auto;padding:4px 0'>" +
        wx.hourly.map(function (hr) {
          return "<div style='border:1px solid #3b5038;border-radius:4px;padding:3px 6px;font-size:10px'>" +
            "<b>" + esc(hr.time) + "</b><br>" + hr.temp_c + "C " +
            esc(hr.condition) + "<br><span class='meta'>" + hr.wind_kph +
            "km/h " + hr.pop + "%</span></div>";
        }).join("") + "</div>";
    }
    h += "<div class='qhead'>AUDIO, DISPLAY &amp; OVERLAYS</div>" +
      "<div class='gmgrid'>" +
      "<button data-gma='mute'>Sound: " + (snd.on ? "ON" : "OFF") + "</button>" +
      "<button data-gma='voldown'>Vol - (" + Math.round(snd.vol * 100) + "%)</button>" +
      "<button data-gma='volup'>Vol +</button>" +
      "<button data-gma='theme'>Theme: " + esc(Theme.get().name) + "</button>" +
      "<button data-gma='dn'>Day/Night: " + (state.dn ? "ON" : "OFF") + "</button>" +
      "<button data-gma='tech'>Tech Tree (K)</button>" +
      "<button data-gma='score'>Victory / History</button>" +
      "<button data-gma='help'>Guide (?)</button>" +
      "</div>";
    box.innerHTML = h;
  }

  // ---- tech tree / spellbook overlay (#132) ----------------------------
  // Every row is a real skill dir under skills/; cast state comes from
  // world.tech (event-sourced skill_casts). Grey = known but never cast,
  // glow = cast this session. Spells a selected hero knows (its profile
  // sheet names them) are castable: click posts a real order intent
  // {order:"cast", skill} that suggests the skill in the next order text.

  function renderTech(u) {
    var box = el("techtree");
    if (!box.classList.contains("on")) return;
    var tech = (state.world || {}).tech;
    if (!tech) {
      box.innerHTML = "<h2>TECH TREE</h2><span class='meta'>" +
        "no daemon data</span>";
      return;
    }
    var raw = u && u.unit ? u.unit : u;
    var book = (raw && raw.spellbook || []).map(function (s) {
      return s.name; });
    var h = "<h2>TECH TREE <span class='meta'>K closes" +
      (raw ? " - casting for " + esc(raw.name || raw.id) :
       " - select a hero to cast") + "</span></h2>";
    h += "<div class='tcols'>";
    (tech.schools || []).forEach(function (sc) {
      h += "<div class='tschool'><h3>" + esc(sc.id) + " (" +
        sc.spells.length + ")</h3>";
      sc.spells.forEach(function (sp) {
        var known = book.indexOf(sp.name) >= 0;
        h += "<div class='spell" + (sp.casts ? " cast" : "") +
          (known ? " known" : "") + "'" +
          (known ? " data-cast='" + esc(sp.name) + "'" : "") +
          " title='" + esc(sp.path) +
          (sp.casts ? " - cast " + sp.casts + "x" : " - unresearched") +
          (known ? " - click to suggest cast" : "") + "'>" +
          esc(sp.name) +
          (sp.casts ? " <b>" + sp.casts + "</b>" : "") + "</div>";
      });
      h += "</div>";
    });
    h += "</div>";
    var a = tech.armory || {};
    h += "<div class='tsect'><h3>ARMORY</h3>" +
      "<span class='meta'>subagent pin: " + esc(a.subagent_model || "-") +
      " (" + esc(a.pin || "") + ")</span>" +
      (a.tiers || []).map(function (t) {
        return "<div class='spell" +
          (t.id === a.subagent_model ? " cast" : "") + "'>" +
          esc(t.name || t.id) + " <span class='meta'>" +
          esc(t.effort || "") + " " + esc(t.role || "") + " " +
          (t.window | 0) + "tok</span></div>";
      }).join("") + "</div>";
    h += "<div class='tsect'><h3>LIBRARY DOCTRINES</h3>" +
      (tech.doctrines || []).map(function (d) {
        return "<div class='spell" + (d.in_use ? " cast" : "") +
          "' title='" + esc((d.evidence || []).join(", ")) + "'>" +
          esc(d.label) + " <span class='meta'>" +
          (d.in_use ? "researched" : "not in use") + "</span></div>";
      }).join("") + "</div>";
    box.innerHTML = h;
  }

  function rows(list, fmt) {
    return (list || []).map(fmt).join("") ||
           "<span class='meta'>none</span>";
  }

  // Inspector for a selected building - every field is live data from
  // GET /buildings/<id> (issue #123: no fake actions).
  function buildingHtml(d) {
    var tb = (Theme.get().buildings || {})[d.id];
    var lbl = tb && tb.label ? " (" + esc(tb.label) + ")" : "";
    var h = "<b>" + esc(d.name) + lbl + "</b> <span class='meta'>" +
      (d.pos ? esc(d.pos.region) + " plot " + d.pos.plot : "") +
      " | used " + (d.activity || 0) + "x</span><br>";
    if (d.rally)   // #127: right-click on map while building selected
      h += "<div class='meta'>rally: " +
        esc(d.rally.region || "?") + " (" + d.rally.x + "," + d.rally.y +
        ")" + (d.rally.channel ? " -> " + esc(d.rally.channel) : "") +
        "</div>";
    if (d.id === "town-hall") {
      h += "<div class='meta'>main quest: " +
        esc((d.goal && d.goal.text) || "-") + "</div>" +
        "<div class='meta'>quests " + d.quests.done + "/" +
        d.quests.total + " done, " + d.quests.blocked + " blocked" +
        " | workers " + d.workers.active + "/" + d.workers.total +
        " | pending calls " + d.decisions_pending + "</div>";
    } else if (d.id === "barracks") {
      h += "<div class='meta'>production queue: " + d.queue.length +
        " pending spawn intents</div>" +
        rows(d.classes, function (c) {
          return "<button data-cls='" + esc(c.profile) + "'>" +
            esc(c.cls) + "</button>";
        }) + "<div class='meta'>pick a class, type task, Enter</div>";
    } else if (d.id === "tavern") {
      h += rows(d.roster, function (r) {
        return "<div>" + esc(r.profile) + " <span class='meta'>" +
          esc(r.cls) + " | " + esc(r.tier) + " | " + esc(r.scope) +
          "</span></div>";
      });
    } else if (d.id === "library") {
      h += rows(d.entries, function (e) {
        return "<div>" + esc(e.file) + " <span class='meta'>" +
          e.size + "b</span></div>";
      });
      // #132: tech tree summary + doctrines (K opens the full overlay)
      var nsp = 0, ncast = 0;
      (d.spellbook || []).forEach(function (sc) {
        sc.spells.forEach(function (sp) { nsp++;
          if (sp.casts) ncast++; }); });
      h += "<div class='meta'>spellbook: " + ncast + "/" + nsp +
        " spells cast this session (K for tech tree)</div>";
      h += rows(d.doctrines, function (x) {
        return "<div>" + esc(x.label) + " <span class='meta'>" +
          (x.in_use ? "researched: " + esc(x.evidence.join(", "))
                    : "not in use") + "</span></div>";
      });
      var a = d.armory || {};
      h += "<div class='meta'>armory: " + esc(a.subagent_model || "-") +
        " (" + esc(a.pin || "") + ")</div>";
    } else if (d.id === "watchtower") {
      h += rows(d.ledgers, function (l) {
        return "<div>" + esc(l.id) + " <span class='meta'>" + l.pass +
          " pass / " + l.fail + " fail / " + l.pending +
          " pending</span></div>";
      }) + "<div class='meta'>heartbeats: " + d.heartbeats + "</div>";
    } else if (d.id === "runeforge") {
      h += rows(d.artifacts, function (a) {
        return "<div>" + esc(a) + "</div>"; });
    } else if (d.id === "vault") {
      h += rows(d.deposits, function (l) {
        return "<div class='meta'>" + esc(l) + "</div>"; });
    } else if (d.id === "portal") {
      var r = d.remote || {};
      h += r.port
        ? "<div class='meta'>listening :" + r.port + " | ttl " +
          (r.ttl_left_s == null ? "-" : r.ttl_left_s) + "s | token " +
          (r.token ? "set" : "off") + "</div>"
        : "<span class='meta'>remote link closed (rtsd --remote MIN)</span>";
    } else if (d.id === "marketplace") {
      h += rows(d.servers, function (s) {
        return "<div>" + esc(s.name) + " <span class='meta'>" +
          esc(s.transport) + " | " + (s.tools | 0) + " tools | " +
          (s.enabled ? "enabled" : "disabled") +
          "</span></div>";
      });
    } else if (d.id === "altar") {
      h += rows(d.fallen, function (f) {
        return "<div>" + esc(f.name || f.id) +
          " <button data-revive='" + esc(f.profile) + "' data-task='" +
          esc(f.task || "") + "'>revive</button></div>";
      });
    } else if (d.id === "trophy-hall") {
      h += rows(d.loot, function (l) {
        return "<div>" + esc(l.ledger + "/" + l.gate) +
          " <span class='meta'>" + esc(l.evidence) + "</span></div>";
      });
    }
    return h;
  }

  function selectBuilding(b) {
    state.selB = b ? b.id : null;
    state.bDetail = null;
    if (!b || state.demo) { renderPanels(); return; }
    fetch("/buildings/" + b.id, { headers: TOK ? { "X-RTS-Token": TOK }
                                               : {} })
      .then(function (r) { return r.ok ? r.json() : null; })
      .then(function (d) {
        if (state.selB === (d && d.id)) { state.bDetail = d; }
        renderPanels();
      }).catch(renderPanels);
  }

  function portraitHtml(u) {
    var inv = (u.inventory || []).map(function (it) {
      return "<span class='inv" + (it.quest ? " qloot" : "") +
        "' title='" + esc((it.ledger || "") + "/" + it.gate +
        (it.quest ? " [quest " + it.quest + "]" : "") + " " +
        (it.evidence || "")) + "'>o</span>";
    }).join("");
    var kit = (u.kit || []).map(function (k) {
      return "<span class='inv' title='" + esc(k) + "'>" +
        esc(k[0]) + "</span>";
    }).join("");
    var bark = u.bark ||
      (state.acks[u.id] ? state.acks[u.id].text : barkLine(u.cls, 0));
    var h = "<b>" + esc(u.name || u.id) + "</b> " +
      "<span class='lvbadge'>Lv" + (u.level || 1) + "</span> " +
      "<span class='meta'>" + esc(u.cls || "") + " " + esc(u.profile || "") +
      " " + esc(u.tier || "") + " " + esc(u.model || "") + "</span><br>" +
      "<span class='meta'>HP " + (u.hp == null ? "-" : u.hp) +
      "  MP " + (u.mana == null ? "-" : u.mana) +
      "  " + esc(u.status_live || u.status || "") + "</span>" +
      // #131 economy: per-hero context burn + est turns left in window
      (u.kind === "hero"
        ? "<div class='meta'>burn ~" + (u.burn | 0) + " tok" +
          (u.turns_left == null ? "" :
            "  |  ~" + u.turns_left + " turns left") + "</div>"
        : "") +
      // #132 spellbook: skills named in the profile sheet
      ((u.spellbook || []).length
        ? "<div class='meta'>spells: " + u.spellbook.map(function (s) {
            return esc(s.name) + (s.casts ? "(" + s.casts + ")" : "");
          }).join(", ") + "</div>"
        : "") +
      (kit ? " <span class='meta'>kit:</span>" + kit : "") +
      (u.quest ? "<div class='meta'>quest: " + esc(u.quest) + "</div>"
               : "") +
      "<br><i>&quot;" + esc(bark) + "&quot;</i>" +
      (inv ? "<div class='meta'>loot: " + inv + "</div>" : "");
    // order queue (#127): numbered pending orders for this hero
    var ords = ((u.unit && u.unit.orders) || u.orders || []).filter(
      function (o) { return o.state !== "consumed"; });
    if (ords.length)
      h += "<div class='meta'>orders: " + ords.map(function (o, i) {
        return (i + 1) + " " + esc(o.order || "?") +
          (typeof o.x === "number" ? "(" + o.x + "," + o.y + ")" : "") +
          " <i>" + esc(o.state || "queued") + "</i>";
      }).join("; ") + "</div>";
    return h;
  }

  // ---- command card (#126) ---------------------------------------------
  // The card is generated, not hardcoded: ability slots come from the
  // hero's real kit (derived server-side from the profile's allowed-tools
  // in agents/*.md), specials from the GDD per-class table. Every enabled
  // button issues a real `order` intent via POST /intent; nothing is fake.

  // GDD kit vocabulary, fixed slot order. March and Verify share the exec
  // slot: the label follows whichever the profile's kit actually carries.
  var KIT_SLOTS = ["Cartography", "Write", "March", "Farsight", "Envoy",
                   "Parley", "Camp"];
  var ABILITY_HINT = {
    Cartography: "scout files (read/grep/glob/find)",
    Write: "write/edit a file",
    March: "run a shell command",
    Verify: "re-run gates (read-only exec)",
    Farsight: "web_search / webfetch",
    Envoy: "call an MCP emissary",
    Parley: "ask the commander (ask_user_question)",
    Camp: "update the war map (todo_write)"
  };
  // Per-class specials from the issue spec (single-select only).
  var SPECIALS = {
    "Far Seer":  { id: "reveal_area", label: "Reveal", target: true },
    "Knight":    { id: "build",       label: "Build" },
    "Cleric":    { id: "verify_gate", label: "Verify" },
    "Ranger":    { id: "track",       label: "Track" }
  };

  function selUnits() {
    return state.units.filter(function (u) {
      return state.selAll.indexOf(u.id) >= 0; });
  }

  // One intent per selected unit: the daemon writes each to
  // .devin/rts/intents/ for rts-intents.py; nothing auto-executes.
  // #159: also wires active client-side gameplay loops (patrol, gather,
  // combat engagement, AoE spell visuals, and immediate movement glide).
  function issueOrder(order, extra) {
    var now = performance.now();
    state.selAll.forEach(function (id) {
      var it = { kind: "order", to: id, order: order };
      if (extra) for (var k in extra) it[k] = extra[k];
      RTS.intent(it);
      var u = state.units.filter(function (x) { return x.id === id; })[0];
      var mo = state.motion[id];
      if (!u || !mo) return;
      if (order === "stop" || order === "hold") {
        mo.patrol = null; mo.gather = null; mo.acting = false;
        mo.tx = u.x; mo.ty = u.y;
      } else if (order === "patrol") {
        // Patrol between current pos and region capital / quest POI
        var tx = (extra && typeof extra.x === "number")
          ? (extra.x + 0.5) * TILE : u.x + TILE * 5;
        var ty = (extra && typeof extra.y === "number")
          ? (extra.y + 0.5) * TILE : u.y - TILE * 3;
        mo.patrol = [{ x: u.x, y: u.y }, { x: tx, y: ty }];
        mo.pi = 1; mo.gather = null; mo.acting = false;
        pushFx("text", u.x, u.y - 12, "Patrolling", "#58a6ff", 1.6);
      } else if (order === "gather") {
        // Find nearest Gold Mine POI or forest tree + Town Hall dropoff
        var gx = u.x + TILE * 4, gy = u.y;
        var bestD = 1e9;
        ((state.map && state.map.pois) || []).forEach(function (p) {
          if (p.kind !== "gold") return;
          var px = (p.x + 0.5) * TILE, py = (p.y + 0.5) * TILE;
          var d = Math.hypot(px - u.x, py - u.y);
          if (d < bestD) { bestD = d; gx = px; gy = py; }
        });
        var th = state.buildings.filter(function (b) {
          return b.bid === "town-hall"; })[0] || state.buildings[0];
        var kx = th ? th.x : u.x, ky = th ? th.y : u.y;
        mo.gather = { gx: gx, gy: gy, kx: kx, ky: ky, phase: 0, wait: 0 };
        mo.patrol = null;
        tone("gather");
        pushFx("text", u.x, u.y - 12, "Gathering Gold", "#ffd54a", 1.8);
      } else if (order === "attack") {
        mo.patrol = null; mo.gather = null;
        mo.combat = { x: (extra && typeof extra.x === "number")
          ? (extra.x + 0.5) * TILE : u.x,
          y: (extra && typeof extra.y === "number")
          ? (extra.y + 0.5) * TILE : u.y,
          lastHit: 0 };
        tone("attack");
      } else if (order === "ability" || order === "cast" ||
                 order === "reveal_area" || order === "build" ||
                 order === "verify_gate" || order === "track") {
        var sx = (extra && typeof extra.x === "number")
          ? (extra.x + 0.5) * TILE : u.x;
        var sy = (extra && typeof extra.y === "number")
          ? (extra.y + 0.5) * TILE : u.y;
        var sname = (extra && (extra.skill || extra.ability)) || order;
        tone("spell");
        pushFx("spell", sx, sy, sname, "#58a6ff", 2.4);
        pushFx("text", sx, sy - 16, "*" + sname + "*", "#bc8cff", 2.2);
      }
    });
    selUnits().forEach(function (u) {
      state.acks[u.id] = { text: barkLine(u.cls, 1), t0: now };
    });
  }

  var ICON_SVG = {
    move: "<path d='M5 12h14M13 6l6 6-6 6'/>",
    stop: "<rect x='6' y='6' width='12' height='12' rx='2'/>",
    hold: "<path d='M12 3l8 4v5c0 5-3.5 8.5-8 10-4.5-1.5-8-5-8-10V7l8-4z'/>",
    patrol: "<path d='M17 2l4 4-4 4M3 11V9a4 4 0 0 1 4-4h14M7 22l-4-4 4-4M21 13v2a4 4 0 0 1-4 4H3'/>",
    attack: "<path d='M14.5 17.5L3 6V3h3l11.5 11.5M13 19l6-6M16 16l4 4M19 21l2-2'/>",
    gather: "<path d='M14 4l6 6M4 20l9-9M15 3a6 6 0 0 1 6 6M11 15l-4 4'/>",
    special: "<polygon points='12 2 15 9 22 9 16.5 14 18.5 21 12 17 5.5 21 7.5 14 2 9 9 9'/>",
    Cartography: "<polygon points='1 6 1 22 8 18 16 22 23 18 23 2 16 6 8 2 1 6'/>",
    Write: "<path d='M12 19l7-7 3 3-7 7-3-3zM18 13l-1.5-7.5L2 2l3.5 14.5L13 18l5-5z'/>",
    March: "<path d='M4 15s1-1 4-1 5 2 8 2 4-1 4-1V3s-1 1-4 1-5-2-8-2-4 1-4 1zM4 22v-7'/>",
    Verify: "<path d='M9 12l2 2 4-4M12 3l8 4v5c0 5-3.5 8.5-8 10-4.5-1.5-8-5-8-10V7l8-4z'/>",
    Farsight: "<circle cx='12' cy='12' r='3'/><path d='M2 12s4-7 10-7 10 7 10 7-4 7-10 7-10-7-10-7z'/>",
    Envoy: "<path d='M22 2L11 13M22 2l-7 20-4-9-9-4 20-7z'/>",
    Parley: "<path d='M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z'/>",
    Camp: "<path d='M3 20L12 4l9 16H3zM12 12v8'/>",
    cast: "<path d='M4 19.5A2.5 2.5 0 0 1 6.5 17H20M6.5 2H20v20H6.5A2.5 2.5 0 0 1 4 19.5v-15A2.5 2.5 0 0 1 6.5 2z'/>",
    train: "<path d='M16 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2'/><circle cx='8.5' cy='7' r='4'/><path d='M20 8v6M23 11h-6'/>",
    bell: "<path d='M18 8A6 6 0 0 0 6 8c0 7-3 9-3 9h18s-3-2-3-9M13.73 21a2 2 0 0 1-3.46 0'/>",
    tech: "<circle cx='12' cy='12' r='3'/><path d='M12 2v4M12 18v4M4.93 4.93l2.83 2.83M16.24 16.24l2.83 2.83M2 12h4M18 12h4'/>",
    score: "<path d='M6 9H4.5a2.5 2.5 0 0 1 0-5H6M18 9h1.5a2.5 2.5 0 0 0 0-5H18M4 22h16M10 14.66V17c0 .55-.47.98-.97 1.21C7.85 18.75 7 20.24 7 22M14 14.66V17c0 .55.47.98.97 1.21C16.15 18.75 17 20.24 17 22M18 2H6v7a6 6 0 0 0 12 0V2z'/>",
    rally: "<path d='M4 15s1-1 4-1 5 2 8 2 4-1 4-1V3s-1 1-4 1-5-2-8-2-4 1-4 1zM4 22v-7'/>",
    center: "<circle cx='12' cy='12' r='8'/><path d='M12 2v4M12 18v4M2 12h4M18 12h4'/>"
  };

  function cardBtn(act, label, enabled, title, armed, icoKey, hk) {
    var svg = ICON_SVG[icoKey] || ICON_SVG[act] || ICON_SVG.special;
    return "<button data-act='" + esc(act) + "'" +
      (enabled ? "" : " disabled") +
      (armed ? " class='armed'" : "") +
      " data-tip='" + esc((label || act) + (hk ? " [" + hk + "]" : "") +
                          " - " + (title || "")) + "'" +
      " title='" + esc(title || "") + "'>" +
      (hk ? "<span class='hk'>" + esc(hk) + "</span>" : "") +
      "<svg class='csvg' viewBox='0 0 24 24'>" + svg + "</svg>" +
      "<span>" + esc(label) + "</span></button>";
  }

  function renderCard(u) {
    var card = el("cmdcard"), multi = state.selAll.length > 1;
    var raw = u && u.unit ? u.unit : u;   // renderable vs raw world unit
    var kit = (raw && raw.kit) || [];
    var armed = state.pending ? state.pending.order : null;
    var h = "";
    if (state.pending)
      h += "<span class='meta tgt'>click target: " +
        esc(state.pending.order) + " (ESC cancels)</span>";
    // #159 Building Command Card when a structure is selected!
    if (!state.selAll.length && state.selB) {
      var bid = state.selB;
      if (bid === "barracks" || bid === "tavern") {
        var roster = [
          ["implementer", "Knight", "train", "Q"],
          ["researcher", "Far Seer", "Farsight", "W"],
          ["architect", "Archmage", "cast", "E"],
          ["debugger", "Ranger", "attack", "R"],
          ["qa-ci", "Cleric", "Verify", "A"],
          ["tech-lead", "Runesmith", "Write", "S"],
          ["reviewer", "Spellbrkr", "special", "D"],
          ["scrum-master", "Marshal", "March", "F"]
        ];
        roster.forEach(function (r) {
          h += cardBtn("train:" + r[0], r[1], true,
                       "Summon/Train " + r[1] + " (" + r[0] + " intent)",
                       false, r[2], r[3]);
        });
        h += cardBtn("bact:rally", "Rally", true,
                     "Right-click map to set Rally Point", false, "rally", "Z");
        h += cardBtn("bact:center", "Center", true,
                     "Center camera on this structure", false, "center", "X");
        h += cardBtn("bact:tech", "Tech Tree", true,
                     "Open Skill & Doctrine Tech Tree (K)", false, "tech", "C");
        h += cardBtn("bact:score", "Victory", true,
                     "Open Session Score & Match History", false, "score", "V");
      } else if (bid === "town-hall") {
        h += cardBtn("train:implementer", "Recruit", true,
                     "Deploy Knight hero from the Keep", false, "train", "Q");
        h += cardBtn("bact:bell", "Town Bell", true,
                     "Call idle heroes to the Keep courtyard", false, "bell", "W");
        h += cardBtn("bact:tech", "Tech Tree", true,
                     "Open Skill & Doctrine Tech Tree (K)", false, "tech", "E");
        h += cardBtn("bact:score", "Victory", true,
                     "Open Session Score & Match History", false, "score", "R");
        h += cardBtn("bact:rally", "Rally", true,
                     "Right-click map to set Keep Rally Point", false, "rally", "A");
        h += cardBtn("bact:center", "Center", true,
                     "Center camera on the Keep", false, "center", "S");
      } else {
        h += cardBtn("bact:use", "Activate", true,
                     "Trigger structure special action / pulse", false, "special", "Q");
        h += cardBtn("bact:tech", "Tech Tree", true,
                     "Open Tech Tree & Doctrines (K)", false, "tech", "W");
        h += cardBtn("bact:center", "Center", true,
                     "Center camera on this structure", false, "center", "E");
        h += cardBtn("bact:rally", "Rally", true,
                     "Right-click map to set Rally Point", false, "rally", "R");
      }
      card.innerHTML = h; return;
    }
    if (!state.selAll.length) {
      h += "<span class='meta tgt'>select a hero or structure</span>";
      for (var i = 0; i < 12; i++) h += "<button disabled>-</button>";
      card.innerHTML = h; return;
    }
    // 4x3 Grid Command Card (#164): Row 1 (Q W E R) = Move, Stop, Hold, Patrol
    // Row 2 (A S D F) = Attack, Gather, Class Special, Primary Kit Ability
    // Row 3 (Z X C V) = Remaining Kit Abilities & Spellbook Casts
    h += cardBtn("move", "Move", true,
                 "click map target (lane/dir reassignment)",
                 armed === "move", "move", "Q");
    h += cardBtn("stop", "Stop", true, "halt current order",
                 false, "stop", "W");
    h += cardBtn("hold", "Hold", !multi, "park: take no new orders",
                 false, "hold", "E");
    h += cardBtn("patrol", "Patrol", !multi,
                 "patrol back and forth scouting fog",
                 false, "patrol", "R");
    h += cardBtn("attack", "Attack", !multi,
                 "click a quest marker / camp to assault",
                 armed === "attack", "attack", "A");
    h += cardBtn("gather", "Gather", true,
                 "harvest gold/lumber between nearest vein and Keep",
                 false, "gather", "S");
    var sp = raw && SPECIALS[raw.cls];
    h += cardBtn("special", sp ? sp.label : "-", !!(sp && !multi),
                 sp ? "class special: " + sp.id : "no class special",
                 !!(sp && armed === sp.id), "special", "D");
    // ability slots: full kit vocabulary, disabled where the profile
    // lacks the backing tools (verified vs agents/*.md via world.py kit)
    var aKeys = ["F", "Z", "X", "C", "V", "", ""];
    KIT_SLOTS.forEach(function (name, idx) {
      var label = name === "March" && kit.indexOf("Verify") >= 0
        ? "Verify" : name;
      var has = kit.indexOf(name) >= 0 || kit.indexOf(label) >= 0;
      if (label === "Verify") has = kit.indexOf("Verify") >= 0;
      h += cardBtn("ability:" + (label === "Verify" ? "Verify" : name),
                   label, has && !multi,
                   ABILITY_HINT[label] || name, false,
                   label, aKeys[idx] || "");
    });
    // #132 hero spellbook: skills the profile sheet names, as cast
    // buttons; clicking posts an order intent {order:"cast", skill} that
    // suggests invoking the skill in the next order text
    ((raw && raw.spellbook) || []).forEach(function (s) {
      h += cardBtn("cast:" + s.name, "*" + s.name.slice(0, 8), !multi,
                   "cast " + s.name + " (skills/" + s.name + "/SKILL.md)" +
                   (s.casts ? " - cast " + s.casts + "x" : ""),
                   false, "cast", "");
    });
    card.innerHTML = h;
  }

  // ---- intents / decisions --------------------------------------------

  function post(path, body) {
    var h = { "Content-Type": "application/json" };
    if (TOK) h["X-RTS-Token"] = TOK;
    return fetch(path, { method: "POST", headers: h,
      body: JSON.stringify(body) }).catch(function () {});
  }

  g.RTS = {
    intent: function (it) { return post("/intent", it).then(refresh); },
    answer: function (id, i) {
      return post("/decisions/" + id + "/answer", { choice: i })
        .then(refresh);
    },
    replay: function (b) { return post("/replay", b); }
  };

  // #135 victory screen: aggregates arrive via WS at end of replay or
  // are fetched on demand from GET /score + GET /sessions (match history)
  function showScore(sc, ss) {
    var h = "<h2>VICTORY SCREEN</h2>" +
      "<div class='meta'>quests " + sc.quests_done + "/" +
      sc.quests_total + " complete &nbsp; gates " + sc.gates_pass + "/" +
      sc.gates_total + " pass (" + sc.gates_fail + " fail) &nbsp; " +
      "tokens " + sc.gold + " &nbsp; calls " + sc.calls +
      " &nbsp; duration " + sc.duration_s + "s</div>";
    if (sc.goal) h += "<div class='meta'>main quest: " +
      esc(sc.goal) + "</div>";
    h += "<table><tr><th>hero</th><th>class</th><th>lvl</th>" +
      "<th>xp</th><th>burn</th><th>status</th></tr>";
    (sc.heroes || []).forEach(function (u) {
      h += "<tr><td>" + esc(u.id) + "</td><td>" + esc(u.cls || "?") +
        "</td><td>" + (u.level || 1) + "</td><td>" + (u.xp || 0) +
        "</td><td>" + (u.burn || 0) + "</td><td>" +
        esc(u.status || "?") + "</td></tr>";
    });
    h += "</table>";
    if (ss && ss.length) {
      h += "<div class='qhead'>MATCH HISTORY</div>" +
        "<table><tr><th>session</th><th>events</th><th>agents</th>" +
        "<th>quests</th><th>tokens</th><th>dur</th></tr>";
      ss.forEach(function (s) {
        h += "<tr><td>" + esc(s.id) + "</td><td>" + (s.events | 0) +
          "</td><td>" + (s.agents | 0) + "</td><td>" +
          (s.quests_done | 0) + "/" + (s.quests_total | 0) + "</td><td>" +
          (s.tokens | 0) + "</td><td>" + (s.duration_s | 0) + "s</td></tr>";
      });
      h += "</table>";
    }
    h += "<div class='meta' style='margin-top:8px'>" +
      "click anywhere to close</div>";
    var b = el("scorebox"); b.innerHTML = h; b.className = "on";
  }

  function fetchScore() {
    var h = TOK ? { "X-RTS-Token": TOK } : {};
    Promise.all([
      fetch("/score", { headers: h }).then(function (r) { return r.json(); }),
      fetch("/sessions", { headers: h })
        .then(function (r) { return r.json(); })
        .catch(function () { return []; })
    ]).then(function (res) {
      if (res[0] && !res[0].error) showScore(res[0], res[1]);
    }).catch(function () {});
  }

  // ---- boot ------------------------------------------------------------

  var eng = Engine.create(el("cv"));

  // #134: battlefield<->office is a pure reskin - state, selection and
  // camera focus carry over; we re-center on the same world point so
  // the view does not jump when the projection changes
  function toggleTheme() {
    var c = eng.toWorld(eng.cv.width / 2, eng.cv.height / 2);
    Theme.toggle();
    eng.iso = !!Theme.get().iso;
    eng.centerOn(c.x, c.y);
    renderPanels();
  }

  // pending council decision -> heroes converge on the meeting room
  // (town-hall plot). Pure presentation state; world data untouched.
  function meetingCall() {
    var pd = pendingDecs().filter(function (d) { return !d._expired; });
    if (!pd.length) { state.decT0 = 0; return null; }
    var th = state.buildings.filter(function (b) {
      return b.bid === "town-hall"; })[0];
    if (!th) return null;
    if (!state.decT0) state.decT0 = performance.now();
    return { x: th.x, y: th.y, t0: state.decT0 };
  }

  // Targeted orders (move/attack/reveal_area): the next map click is the
  // payload. Attack snaps to a quest POI within 1.5 tiles and carries its
  // issue ref so the intent file names the real quest (#126 acceptance).
  function resolveOrderTarget(pt) {
    var tx = Math.floor(pt.x / TILE), ty = Math.floor(pt.y / TILE);
    var ord = state.pending; state.pending = null;
    var extra = { x: tx, y: ty };
    if (ord.order === "attack" && state.map && state.map.pois) {
      var best = null, bd = 1.5;
      state.map.pois.forEach(function (p) {
        if (p.kind !== "quest") return;
        var d = Math.hypot(p.x - tx, p.y - ty);
        if (d <= bd) { bd = d; best = p; }
      });
      if (best) extra.quest = best.ref;
    }
    issueOrder(ord.order, extra);
    state.pings.push({ x: (tx + .5) * TILE, y: (ty + .5) * TILE,
                       kind: "order", t0: performance.now() });
    logFeed("order: " + ord.order + " " + state.selAll.join(",") +
            " -> " + tx + "," + ty + (extra.quest ? " (" +
            extra.quest + ")" : ""));
    syncRenderables(); renderPanels();
  }

  eng.onPick = function (u, pt, ev) {
    if (state.pending) { resolveOrderTarget(pt); return; }
    if (u) {
      if (ev.shiftKey) {                       // shift-click: toggle-add
        var i = state.selAll.indexOf(u.id);
        if (i >= 0) state.selAll.splice(i, 1); else state.selAll.push(u.id);
      } else state.selAll = [u.id];
      state.sel = u.id; state.selB = null; state.bDetail = null;
      tone("select_hero", u.cls);
      if (!u.bark)   // no heartbeat note -> class "selected" line
        state.acks[u.id] = { text: barkLine(u.cls, 0),
                             t0: performance.now() };
    } else {
      if (!ev.shiftKey) { state.selAll = []; state.sel = null; }
      var pb = eng.pickBuilding(ev.offsetX, ev.offsetY);
      if (pb) tone("select_bld", pb.id);
      selectBuilding(pb);
    }
    syncRenderables(); renderPanels();
  };
  // box-drag multi-select (#126); shift unions with the current set
  eng.onBox = function (rect, ev) {
    var ids = eng.unitsInBox(rect).map(function (u) { return u.id; });
    if (ev.shiftKey) {
      ids.forEach(function (id) {
        if (state.selAll.indexOf(id) < 0) state.selAll.push(id); });
    } else state.selAll = ids;
    state.sel = state.selAll[0] || null;
    if (ids.length) { state.selB = null; state.bDetail = null; }
    syncRenderables(); renderPanels();
  };
  // double-click: select every same-class unit on screen (WC3 rule)
  eng.onDblPick = function (u) {
    if (!u) return;
    state.selAll = eng.unitsInView().filter(function (x) {
      return x.cls === u.cls; }).map(function (x) { return x.id; });
    if (state.selAll.indexOf(u.id) < 0) state.selAll.push(u.id);
    state.sel = u.id; state.selB = null; state.bDetail = null;
    syncRenderables(); renderPanels();
  };
  // command card clicks: targeted orders arm `state.pending`, the rest
  // issue intents immediately (#126/#159)
  el("cmdcard").addEventListener("click", function (e) {
    var b = e.target.closest("button[data-act]");
    if (!b || b.disabled) return;
    var act = b.dataset.act;
    // Building Command Card actions (#159)
    if (act.indexOf("train:") === 0) {
      var prof = act.slice(6);
      RTS.intent({ kind: "spawn", profile: prof,
                   task: "recruited at " + (state.selB || "keep") });
      var sb = state.buildings.filter(function (x) {
        return x.id === state.selB; })[0];
      if (sb) {
        pushFx("spell", sb.x, sb.y, prof, "#3fb950", 2.0);
        pushFx("text", sb.x, sb.y - 18, "+Recruit " + prof, "#3fb950", 2.0);
      }
      tone("spawn");
      logFeed("recruit: " + prof + " queued at " + (state.selB || "keep"));
      return;
    }
    if (act.indexOf("bact:") === 0) {
      var sub = act.slice(5);
      var bld = state.buildings.filter(function (x) {
        return x.id === state.selB; })[0];
      if (sub === "tech") { el("techtree").classList.toggle("on"); }
      else if (sub === "score") { fetchScore(); }
      else if (sub === "center" && bld) { eng.centerOn(bld.x, bld.y); }
      else if (sub === "bell" && bld) {
        tone("decision");
        pushFx("spell", bld.x, bld.y, "Town Bell", "#ffd54a", 2.2);
        pushFx("text", bld.x, bld.y - 18, "Call to Arms!", "#ffd54a", 2.2);
        logFeed("town-hall: Call to Arms rung");
      } else if (sub === "use" && bld) {
        tone("spell");
        pushFx("spell", bld.x, bld.y, bld.name, "#58a6ff", 2.2);
        pushFx("text", bld.x, bld.y - 18, bld.name + " Active", "#58a6ff", 2.0);
      } else if (sub === "rally") {
        logFeed("right-click anywhere on the map to set " +
                (state.selB || "building") + " rally point");
      }
      renderPanels();
      return;
    }
    if (!state.selAll.length) return;
    var u = state.units.filter(function (x) {
      return x.id === state.sel; })[0];
    var raw = u && u.unit ? u.unit : u;
    if (act === "move" || act === "attack") {
      state.pending = { order: act };
    } else if (act === "special") {
      var sp = raw && SPECIALS[raw.cls];
      if (!sp) return;
      if (sp.target) state.pending = { order: sp.id };
      else issueOrder(sp.id, {});
    } else if (act.indexOf("ability:") === 0) {
      issueOrder("ability", { ability: act.slice(8) });
    } else if (act.indexOf("cast:") === 0) {       // #132 spell cast
      issueOrder("cast", { skill: act.slice(5) });
    } else if (act === "patrol") {
      issueOrder("patrol", { lane: (raw && raw.lane) || "" });
    } else {
      issueOrder(act, {});                     // stop / hold / gather
    }
    renderPanels();
  });
  // group pips: click = recall (same as pressing the digit)
  el("grps").addEventListener("click", function (e) {
    var b = e.target.closest("button[data-grp]");
    if (b) recallGroup(parseInt(b.dataset.grp, 10));
  });
  function recallGroup(n) {
    var ids = (state.groups[n] || []).filter(function (id) {
      return state.units.some(function (x) { return x.id === id; }); });
    if (!ids.length) return;
    var now = performance.now();
    var dbl = state.gtap.n === n && now - state.gtap.t < 450;
    state.gtap = { n: n, t: now };
    state.selAll = ids; state.sel = ids[0];
    if (dbl) {                                 // double-tap = center
      var us = selUnits();
      var cx = us.reduce(function (s, x) { return s + x.x; }, 0) /
               us.length;
      var cy = us.reduce(function (s, x) { return s + x.y; }, 0) /
               us.length;
      eng.centerOn(cx, cy);
    }
    syncRenderables(); renderPanels();
  }
  // building inspector actions: hero-class picker + altar revive
  el("portrait").addEventListener("click", function (e) {
    var b = e.target.closest("button"); if (!b) return;
    if (b.dataset.cls) {
      el("msg").value = "/spawn " + b.dataset.cls + " ";
      el("msg").focus();
    } else if (b.dataset.revive) {
      RTS.intent({ kind: "spawn", profile: b.dataset.revive,
                   task: b.dataset.task || "revive" });
    }
  });

  function mmPos(e) {
    var r = e.target.getBoundingClientRect();
    return { sx: e.clientX - r.left, sy: e.clientY - r.top, r: r };
  }
  // click: a ping under the cursor wins (jump to alert), else move camera
  el("mm").addEventListener("click", function (e) {
    var m = mmPos(e), mm = e.target;
    var hit = null;
    livePings().forEach(function (p) {
      var px = p.x / TILE / state.map.w * m.r.width;
      var py = p.y / TILE / state.map.h * m.r.height;
      if (Math.hypot(px - m.sx, py - m.sy) < 10) hit = p;
    });
    if (hit) { eng.centerOn(hit.x, hit.y); return; }
    var p = eng.mmToWorld(mm, { tiles: state.map }, m.sx, m.sy);
    eng.centerOn(p.x, p.y);
  });
  // right-click: move-intent for the whole selection (real /intent order)
  el("mm").addEventListener("contextmenu", function (e) {
    e.preventDefault();
    if (!state.selAll.length) return;
    var m = mmPos(e);
    var p = eng.mmToWorld(e.target, { tiles: state.map }, m.sx, m.sy);
    var tx = Math.floor(p.x / TILE), ty = Math.floor(p.y / TILE);
    issueOrder("move", { x: tx, y: ty });
    state.pings.push({ x: (tx + .5) * TILE, y: (ty + .5) * TILE,
                       kind: "order", t0: performance.now() });
    logFeed("order: move " + state.selAll.join(",") +
            " -> " + tx + "," + ty);
    renderPanels();
  });

  // right-click on the world canvas (#127): building selected = set that
  // building's rally point; units selected = context order (quest POI ->
  // attack with issue ref, building -> garrison/report, ground -> move).
  // Shift enqueues (appends to the unit's order queue instead of a lone
  // order); all land as real intent files via POST /intent.
  el("cv").addEventListener("contextmenu", function (e) {
    e.preventDefault();
    if (state.demo) return;
    var pt = eng.toWorld(e.offsetX, e.offsetY);
    var tx = Math.floor(pt.x / TILE), ty = Math.floor(pt.y / TILE);
    if (tx < 0 || ty < 0 || !state.map ||
        tx >= state.map.w || ty >= state.map.h) return;
    if (state.selB) {                          // per-building rally point
      var it = { kind: "order", to: state.selB, order: "set_rally",
                 x: tx, y: ty };
      if (state.selB === "watchtower" && state.map.tileRegion)
        it.channel = state.map.regionIds[
          state.map.tileRegion[ty * state.map.w + tx]] || "alerts";
      RTS.intent(it).then(function () { selectBuilding({id: state.selB}); });
      state.pings.push({ x: (tx + .5) * TILE, y: (ty + .5) * TILE,
                         kind: "order", t0: performance.now() });
      logFeed("rally: " + state.selB + " -> " + tx + "," + ty +
              (it.channel ? " (" + it.channel + ")" : ""));
      return;
    }
    if (!state.selAll.length) return;
    var ord = "move", extra = { x: tx, y: ty };
    if (e.shiftKey) extra.queue = true;        // shift-queue (#127)
    var bd = eng.pickBuilding(e.offsetX, e.offsetY);
    var best = null, bestGold = null, qq = 1.6, gq = 1.6;
    (state.map.pois || []).forEach(function (p) {
      var d = Math.hypot(p.x - tx, p.y - ty);
      if (p.kind === "quest" && d <= qq) { qq = d; best = p; }
      else if (p.kind === "gold" && d <= gq) { gq = d; bestGold = p; }
    });
    if (bd) { ord = "garrison"; extra.building = bd.id; }
    else if (best) { ord = "attack"; extra.quest = best.ref; }
    else if (bestGold) { ord = "gather"; extra.gold = bestGold.ref; }
    issueOrder(ord, extra);
    state.pings.push({ x: (tx + .5) * TILE, y: (ty + .5) * TILE,
                       kind: "order", t0: performance.now() });
    logFeed("order: " + ord + " " + state.selAll.join(",") +
            " -> " + tx + "," + ty +
            (extra.queue ? " [queued]" : "") +
            (extra.quest ? " (" + extra.quest + ")" : "") +
            (extra.building ? " (" + extra.building + ")" : ""));
    renderPanels();
  });

  // #130 quest assignment: drag a quest row onto a hero on the map (or
  // use the command-card Attack on a quest marker - same intent shape).
  // The drop resolves to the unit under the cursor and posts a real
  // order intent carrying the issue ref; nothing auto-executes.
  el("tlist").addEventListener("dragstart", function (e) {
    var d = e.target.closest("[data-quest]");
    if (d && e.dataTransfer)
      e.dataTransfer.setData("text/quest", d.dataset.quest);
  });
  el("cv").addEventListener("dragover", function (e) {
    if (e.dataTransfer &&
        e.dataTransfer.types.indexOf("text/quest") >= 0)
      e.preventDefault();
  });
  el("cv").addEventListener("drop", function (e) {
    var qid = e.dataTransfer && e.dataTransfer.getData("text/quest");
    if (!qid) return;
    e.preventDefault();
    var u = eng.pickUnit(e.offsetX, e.offsetY);
    if (!u || u.kind !== "hero") {
      logFeed("assign: drop on a hero to accept quest " + qid);
      return;
    }
    var it = { kind: "order", to: u.id, order: "attack", quest: qid };
    RTS.intent(it);
    logFeed("assign: quest " + qid + " -> " + (u.name || u.id));
  });
  // click a quest row: center the camera on its map marker (#130)
  el("tlist").addEventListener("click", function (e) {
    var d = e.target.closest("[data-quest]");
    if (!d || !state.map) return;
    var qid = d.dataset.quest, poi = null;
    (state.map.pois || []).forEach(function (p) {
      if (p.kind === "quest" && p.ref === qid) poi = p; });
    if (poi) eng.centerOn((poi.x + .5) * TILE, (poi.y + .5) * TILE);
  });

  // tech tree (#132): clicking a spell the selected hero knows posts the
  // same {order:"cast", skill} intent as its command-card spell slot
  el("techtree").addEventListener("click", function (e) {
    var d = e.target.closest("[data-cast]");
    if (!d || !state.selAll.length) return;
    issueOrder("cast", { skill: d.dataset.cast });
    logFeed("cast: " + d.dataset.cast + " -> " + state.selAll.join(","));
    renderPanels();
  });

  // idle-worker button (#127): count from the world snapshot's idle list
  // (heroes idle/stale with no active order); click cycles + centers each.
  var idleIdx = 0;
  el("idleBtn").addEventListener("click", function () {
    var ids = (state.world && state.world.idle) || [];
    if (!ids.length) return;
    var id = ids[idleIdx++ % ids.length];
    state.selAll = [id]; state.sel = id;
    state.selB = null; state.bDetail = null;
    var u = state.units.filter(function (x) { return x.id === id; })[0];
    if (u) eng.centerOn(u.x, u.y);
    syncRenderables(); renderPanels();
  });

  window.addEventListener("keydown", function (e) {
    if (e.target && e.target.tagName === "INPUT") return;
    var k = e.key.toLowerCase();
    if (k === "escape" && state.pending) {     // cancel targeted order
      state.pending = null; renderPanels(); return; }
    if (k === "escape" && el("gamemenu") &&
        el("gamemenu").classList.contains("on")) {
      el("gamemenu").classList.remove("on"); return; }
    if (k === "escape" && el("techtree").classList.contains("on")) {
      el("techtree").classList.remove("on"); return; }
    if (k === "f10") {
      e.preventDefault();
      if (el("gamemenu")) {
        el("gamemenu").classList.toggle("on");
        renderGameMenu();
      }
      return;
    }
    if (k === "tab" && state.selAll.length > 1) {  // subgroup cycle
      e.preventDefault();
      var i = state.selAll.indexOf(state.sel);
      state.sel = state.selAll[(i + 1) % state.selAll.length];
      renderPanels(); return;
    }
    if (/^[0-9]$/.test(k)) {                   // control groups (#126)
      var n = parseInt(k, 10);
      e.preventDefault();
      if (e.ctrlKey || e.metaKey) {
        if (state.selAll.length) {
          state.groups[n] = state.selAll.slice();
          logFeed("group " + n + " = " + state.selAll.join(","));
          renderPanels();
        }
      } else recallGroup(n);
      return;
    }
    if (k === "k") {                       // #132 tech tree overlay
      el("techtree").classList.toggle("on");
      renderPanels(); return;
    }
    // #136 hotkey audit (WC3 set): A attack-target, H hold, P patrol,
    // . idle-worker cycle, F1-F4 camera bookmarks (Ctrl+Fn saves)
    if (/^f[1-4]$/.test(k)) {
      e.preventDefault();
      var cn = parseInt(k[1], 10);
      if (e.ctrlKey || e.metaKey) {
        state.cams[cn] = eng.toWorld(eng.cv.width / 2, eng.cv.height / 2);
        logFeed("camera " + cn + " saved");
      } else if (state.cams[cn]) {
        eng.centerOn(state.cams[cn].x, state.cams[cn].y);
      }
      return;
    }
    if (k === "a" && state.selAll.length && !e.ctrlKey && !e.metaKey) {
      state.pending = { order: "attack" }; renderPanels(); return;
    }
    if (k === "g" && state.selAll.length && !e.ctrlKey && !e.metaKey) {
      issueOrder("gather", {}); renderPanels(); return;
    }
    if (k === "h" && state.selAll.length && !e.ctrlKey && !e.metaKey) {
      issueOrder("hold", {}); renderPanels(); return;
    }
    if (k === "p" && state.selAll.length && !e.ctrlKey && !e.metaKey) {
      var pu = state.units.filter(function (x) {
        return x.id === state.sel; })[0];
      var praw = pu && pu.unit ? pu.unit : pu;
      issueOrder("patrol", { lane: (praw && praw.lane) || "" });
      renderPanels(); return;
    }
    if (k === ".") { el("idleBtn").click(); return; }  // idle worker
    if (k === "n") {                       // day/night toggle (#136)
      state.dn = !state.dn;
      localStorage.setItem("rtsd.daynight", state.dn ? "1" : "0");
      dnUi(); return;
    }
    if (k === "m") { setMute(!snd.on); return; }    // #133 mute toggle
    if (k === "-" || k === "_") { setVol(snd.vol - 0.1); return; }
    if (k === "=" || k === "+") { setVol(snd.vol + 0.1); return; }
    if (k === "t") { toggleTheme(); }
    if (k === " ") {               // last-alert: cycle recent pings
      e.preventDefault();
      var ps = livePings();
      if (ps.length) {
        var p = ps[state.pingIdx % ps.length];
        state.pingIdx++;
        eng.centerOn(p.x, p.y);
      } else if (state.lastEventPos) {
        eng.centerOn(state.lastEventPos.x, state.lastEventPos.y);
      }
    }
    if (k === "?") el("help").classList.toggle("on");
  });
  el("themeBtn").onclick = toggleTheme;
  // day/night toggle (#136): cosmetic dim cycle anchored to the session;
  // persisted like the theme choice, zero render cost while off
  function dnUi() {
    el("dnBtn").textContent = "day/night:" + (state.dn ? "on" : "off");
  }
  el("dnBtn").onclick = function () {
    state.dn = !state.dn;
    localStorage.setItem("rtsd.daynight", state.dn ? "1" : "0");
    dnUi();
  };
  dnUi();
  el("sndBtn").onclick = function () { setMute(!snd.on); };
  sndUi();
  // Notification opt-in (#133): click grants/denies via the platform
  // prompt; choice persists; denied shows its state and stays quiet
  el("ntfBtn").onclick = function () {
    if (!("Notification" in window)) return;
    if (ntfOn()) { localStorage.setItem(NTFKEY, "0"); ntfUi(); return; }
    try {
      var p = Notification.requestPermission(function (r) {
        localStorage.setItem(NTFKEY, r === "granted" ? "1" : "0");
        ntfUi();
      });
      if (p && p.then) p.then(function (r) {
        localStorage.setItem(NTFKEY, r === "granted" ? "1" : "0");
        ntfUi();
      });
    } catch (e) { ntfUi(); }
  };
  ntfUi();

  // feed entry click -> select the speaking unit + camera jump (#128)
  el("feed").addEventListener("click", function (e) {
    var d = e.target.closest("[data-uid]");
    if (!d || !state.map) return;
    var id = d.dataset.uid;
    var u = state.units.filter(function (x) { return x.id === id; })[0];
    if (!u) return;
    state.selAll = [id]; state.sel = id;
    state.selB = null; state.bDetail = null;
    eng.centerOn(u.x, u.y);
    syncRenderables(); renderPanels();
  });
  // filter chips: kind / class toggles (click again or 'all' to clear)
  el("ffilter").addEventListener("click", function (e) {
    var b = e.target.closest("button[data-fk]");
    if (!b) return;
    var key = b.dataset.fk, val = b.dataset.fv || null;
    state.feedFilter[key] = state.feedFilter[key] === val ? null : val;
    renderFeed();
  });
  document.getElementById("decs").addEventListener("click", function (e) {
    var b = e.target.closest("button[data-dec]");
    if (b) RTS.answer(b.dataset.dec, parseInt(b.dataset.idx, 10));
  });
  // stacked pending decisions: option buttons answer in place; clicking
  // the card pulls it into the council chamber (#129)
  el("decsStack").addEventListener("click", function (e) {
    var b = e.target.closest("button[data-dec]");
    if (b) {
      RTS.answer(b.dataset.dec, parseInt(b.dataset.idx, 10));
      return;
    }
    var d = e.target.closest("[data-decid]");
    if (d) { state.decActive = d.dataset.decid; renderPanels(); }
  });
  // alert-stack chips: breach chip jumps to the breached territory's
  // capital; decision chip brings its call to the chamber front (#133/#159)
  el("alerts").addEventListener("click", function (e) {
    var c = e.target.closest("[data-dec]");
    if (c) {
      state.decActive = c.dataset.dec;
      state.councilClosed = false;
      state._forceCouncil = true;
      renderPanels();
      return;
    }
    var b = e.target.closest("[data-breg]");
    if (b && state.map && state.map.caps[b.dataset.breg])
      eng.centerOn(state.map.caps[b.dataset.breg].cx * TILE,
                   state.map.caps[b.dataset.breg].cy * TILE);
  });
  if (el("councilClose")) {
    el("councilClose").onclick = function () {
      state.councilClosed = true;
      state._forceCouncil = false;
      el("council").classList.remove("on");
    };
  }
  if (el("togFeed")) {
    el("togFeed").onclick = function () {
      document.body.classList.toggle("hide-feed");
    };
  }
  if (el("togSide")) {
    el("togSide").onclick = function () {
      document.body.classList.toggle("hide-side");
    };
  }
  if (el("wxBtn")) {
    el("wxBtn").onclick = function () {
      state.wxIdx = (state.wxIdx + 1) % state.wxModes.length;
      var mode = state.wxModes[state.wxIdx];
      post("/weather", { mode: mode }).then(function (r) {
        return r && r.json ? r.json() : null;
      }).then(function (wx) {
        if (wx && wx.ok) { state.weather = wx; renderPanels(); }
      });
    };
  }
  // #159 Hero Roster Bar (click = select, dblclick = center camera)
  if (el("herobar")) {
    el("herobar").addEventListener("click", function (e) {
      var card = e.target.closest("[data-hid]");
      if (!card) return;
      var id = card.dataset.hid;
      state.selAll = [id]; state.sel = id;
      state.selB = null; state.bDetail = null;
      tone("select_hero");
      syncRenderables(); renderPanels();
    });
    el("herobar").addEventListener("dblclick", function (e) {
      var card = e.target.closest("[data-hid]");
      if (!card) return;
      var u = state.units.filter(function (x) {
        return x.id === card.dataset.hid; })[0];
      if (u) eng.centerOn(u.x, u.y);
    });
  }
  // #159 Building Quick-Select Strip (click = inspect, dblclick = center)
  if (el("bldbar")) {
    el("bldbar").addEventListener("click", function (e) {
      var chip = e.target.closest("[data-bid]");
      if (!chip) return;
      var bid = chip.dataset.bid;
      state.selAll = []; state.sel = null;
      var b = state.buildings.filter(function (x) {
        return x.id === bid; })[0];
      tone("select_bld", bid);
      selectBuilding(b || { id: bid });
      syncRenderables(); renderPanels();
    });
    el("bldbar").addEventListener("dblclick", function (e) {
      var chip = e.target.closest("[data-bid]");
      if (!chip) return;
      var b = state.buildings.filter(function (x) {
        return x.id === chip.dataset.bid; })[0];
      if (b) eng.centerOn(b.x, b.y);
    });
  }
  // #159 Portrait canvas click -> center camera on selected entity
  if (el("portcv")) {
    el("portcv").onclick = function () {
      var u = state.units.filter(function (x) {
        return x.id === state.sel; })[0];
      if (u) { eng.centerOn(u.x, u.y); return; }
      var b = state.buildings.filter(function (x) {
        return x.id === state.selB; })[0];
      if (b) eng.centerOn(b.x, b.y);
    };
  }
  // #159 Hover Tooltip on map canvas
  if (el("tooltip")) {
    el("cv").addEventListener("mousemove", function (e) {
      var tt = el("tooltip");
      var u = eng.pickUnit(e.offsetX, e.offsetY);
      var b = !u ? eng.pickBuilding(e.offsetX, e.offsetY) : null;
      if (u) {
        tt.innerHTML = "<b>" + esc(u.name || u.id) + "</b> " +
          "<span class='lvbadge'>Lv" + (u.level || 1) + "</span><br>" +
          "<span class='meta'>" + esc(u.cls) + " | HP " +
          (u.hp == null ? 100 : u.hp) + " | MP " +
          (u.mana == null ? 100 : u.mana) + " | " +
          esc(u.status_live || "ready") + "</span>";
        tt.style.left = (e.clientX + 14) + "px";
        tt.style.top = (e.clientY + 14) + "px";
        tt.className = "on";
      } else if (b) {
        tt.innerHTML = "<b>" + esc(b.name || b.id) + "</b><br>" +
          "<span class='meta'>Territory: " + esc(b.region || "root") +
          " | Activity: " + (b.activity || 0) +
          "x<br>Click to inspect & open production commands</span>";
        tt.style.left = (e.clientX + 14) + "px";
        tt.style.top = (e.clientY + 14) + "px";
        tt.className = "on";
      } else {
        tt.className = "";
      }
    });
    el("cv").addEventListener("mouseleave", function () {
      el("tooltip").className = "";
    });
  }
  // #164 Anchored WC3 Command & Inventory Tooltip (#cardtip)
  if (el("cardtip")) {
    var showCardTip = function (e) {
      var tEl = e.target.closest("[data-tip]");
      var ct = el("cardtip");
      if (!tEl) { ct.className = ""; return; }
      ct.innerHTML = "<b>" + esc(tEl.dataset.tip) + "</b>";
      ct.className = "on";
    };
    var hideCardTip = function () { el("cardtip").className = ""; };
    el("cmdcard").addEventListener("mouseover", showCardTip);
    el("cmdcard").addEventListener("mouseout", hideCardTip);
    if (el("invgrid")) {
      el("invgrid").addEventListener("mouseover", showCardTip);
      el("invgrid").addEventListener("mouseout", hideCardTip);
    }
  }
  // #164 Minimap filter buttons (all / units / bld)
  if (el("mmbar")) {
    el("mmbar").addEventListener("click", function (e) {
      var b = e.target.closest("button[data-mmf]");
      if (!b) return;
      state.mmFilter = b.dataset.mmf;
      el("mmbar").querySelectorAll("button[data-mmf]").forEach(function (x) {
        x.className = x === b ? "on" : "";
      });
    });
  }
  // #164 F10 Game Menu modal & Weather Forecast controls
  if (el("menuBtn") && el("gamemenu")) {
    el("menuBtn").onclick = function () {
      el("gamemenu").classList.toggle("on");
      renderGameMenu();
    };
    el("gamemenu").addEventListener("click", function (e) {
      if (e.target === el("gamemenu") || e.target.id === "gmClose") {
        el("gamemenu").classList.remove("on");
        return;
      }
      var wm = e.target.closest("button[data-wxm]");
      if (wm) {
        post("/weather", { mode: wm.dataset.wxm }).then(function (r) {
          return r && r.json ? r.json() : null;
        }).then(function (wx) {
          if (wx && wx.ok) { state.weather = wx; renderPanels(); }
        });
        return;
      }
      var gma = e.target.closest("button[data-gma]");
      if (gma) {
        var a = gma.dataset.gma;
        if (a === "mute") setMute(!snd.on);
        else if (a === "voldown") setVol(snd.vol - 0.1);
        else if (a === "volup") setVol(snd.vol + 0.1);
        else if (a === "theme") toggleTheme();
        else if (a === "dn") el("dnBtn").click();
        else if (a === "tech") {
          el("gamemenu").classList.remove("on");
          el("techtree").classList.add("on");
        } else if (a === "score") {
          el("gamemenu").classList.remove("on");
          fetchScore();
        } else if (a === "help") {
          el("gamemenu").classList.remove("on");
          el("help").classList.toggle("on");
        }
        renderPanels();
      }
    });
  }
  // #135 replay transport + victory screen
  el("scoreBtn").onclick = fetchScore;
  if (el("mtabs")) {
    el("mtabs").addEventListener("click", function (e) {
      var b = e.target.closest("button[data-mtab]");
      if (!b) return;
      document.body.dataset.mtab = b.dataset.mtab;
      el("mtabs").querySelectorAll("button").forEach(function (x) {
        x.className = x === b ? "on" : "";
      });
    });
  }
  el("scorebox").addEventListener("click", function () {
    el("scorebox").className = ""; });
  el("rpp").onclick = function () {
    RTS.replay({ action: state.rp && state.rp.playing ?
      "pause" : "play" }); };
  document.querySelectorAll(".rpsp").forEach(function (b) {
    b.onclick = function () { RTS.replay({ speed: +b.dataset.s }); }; });
  el("rpscrub").addEventListener("change", function (e) {
    RTS.replay({ action: "seek", index: +e.target.value }); });
  // steering (#128): resolve unit names (Knight-4) to the real
  // agent id the mailbox / rts-intents.py path expects
  function resolveUnit(to) {
    var uid = null;
    (state.world && state.world.units || []).forEach(function (u) {
      if (uid) return;
      if (u.id === to || (u.name &&
          u.name.toLowerCase() === to.toLowerCase())) uid = u.id;
    });
    return uid;
  }

  function sendMsg() {
    var v = el("msg").value.trim(); if (!v) return;
    el("msg").value = ""; acClose();
    var m = v.match(/^\/spawn\s+(\S+)\s+(.+)/);
    if (m) return RTS.intent({ kind: "spawn", profile: m[1], task: m[2] });
    var g = v.match(/^\/goal\s+(.+)/);
    if (g) return RTS.intent({ kind: "goal", text: g[1] });
    var ms = v.match(/^\/msg\s+@?(\S+)\s+(.+)/) ||
             v.match(/^@(\S+)\s+(.+)/);
    if (ms) {
      var to = ms[1], uid = resolveUnit(to);
      if (!uid) logFeed("@" + to + " not a known unit - message queued raw");
      return RTS.intent({ kind: "message", to: uid || to, text: ms[2] });
    }
    RTS.intent({ kind: "goal", text: v });
  }
  document.getElementById("send").onclick = sendMsg;

  // ---- input helpers: '/' command palette, '@' unit + /spawn profile
  // completion (mirrors the devin-cli input facilitators).
  var AC_CMDS = [
    { cmd: "/spawn", usage: "/spawn <profile> <task>",
      desc: "spawn a hero unit (runs a subagent)" },
    { cmd: "/goal", usage: "/goal <text>",
      desc: "set the main quest" },
    { cmd: "/msg", usage: "/msg @<unit> <text>",
      desc: "steering message to a unit" }];
  var acItems = [], acSel = 0, acProfiles = null, acProfReq = false;

  function acOpen() { return el("ac").classList.contains("on"); }
  function acClose() { el("ac").className = ""; acItems = []; acSel = 0; }

  function acToken() {
    var inp = el("msg"), v = inp.value;
    var caret = inp.selectionStart == null ? v.length : inp.selectionStart;
    var m = v.slice(0, caret).match(/(\S*)$/);
    return { start: caret - m[1].length, tok: m[1], caret: caret };
  }

  function acCompute() {
    var inp = el("msg"), v = inp.value, t = acToken(), out = [];
    if (t.start === 0 && t.tok.charAt(0) === "/") {
      AC_CMDS.forEach(function (c) {
        if (c.cmd.indexOf(t.tok) === 0)
          out.push({ k: c.usage, d: c.desc, ins: c.cmd + " " });
      });
    } else if (t.tok.charAt(0) === "@") {
      var pref = t.tok.slice(1).toLowerCase();
      (state.world && state.world.units || []).forEach(function (u) {
        var nm = u.name || u.id;
        if (nm.toLowerCase().indexOf(pref) < 0 &&
            String(u.id).toLowerCase().indexOf(pref) < 0) return;
        out.push({ k: "@" + nm,
          d: [u.cls, u.profile, u.status].filter(Boolean).join(" | "),
          ins: "@" + nm + " " });
      });
    } else {
      var mg = v.match(/^\/msg\s+(\S*)$/);
      if (mg && t.tok === mg[1]) {
        var mp = mg[1].toLowerCase();
        (state.world && state.world.units || []).forEach(function (u) {
          var nm = u.name || u.id;
          if (nm.toLowerCase().indexOf(mp) < 0 &&
              String(u.id).toLowerCase().indexOf(mp) < 0) return;
          out.push({ k: "@" + nm,
            d: [u.cls, u.profile, u.status].filter(Boolean).join(" | "),
            ins: "@" + nm + " " });
        });
      }
      var sp = v.match(/^\/spawn\s+(\S*)$/);
      if (sp && t.tok === sp[1]) {
        if (!acProfiles && !acProfReq) {
          acProfReq = true;
          fetch("/buildings/barracks",
                { headers: TOK ? { "X-RTS-Token": TOK } : {} })
            .then(function (r) { return r.json(); })
            .then(function (d) {
              acProfiles = (d.classes || []).map(function (c) {
                return { profile: c.profile, cls: c.cls, model: c.model };
              });
              acProfReq = false; acRender();
            }).catch(function () { acProfReq = false; });
        }
        (acProfiles || []).forEach(function (p) {
          if (p.profile.toLowerCase().indexOf(sp[1].toLowerCase()) < 0)
            return;
          out.push({ k: p.profile,
            d: [p.cls, p.model].filter(Boolean).join(" | "),
            ins: p.profile + " " });
        });
      }
    }
    return out;
  }

  function acRender() {
    var box = el("ac");
    if (document.activeElement !== el("msg")) { acClose(); return; }
    acItems = acCompute();
    if (!acItems.length) { acClose(); return; }
    acSel = Math.max(0, Math.min(acSel, acItems.length - 1));
    box.innerHTML = acItems.map(function (it, i) {
      return "<div class='it" + (i === acSel ? " sel" : "") +
             "' data-i='" + i + "'><span class='k'>" + esc(it.k) +
             "</span><span class='d'>" + esc(it.d) + "</span></div>";
    }).join("");
    box.className = "on";
    box.querySelectorAll(".it").forEach(function (n) {
      n.addEventListener("mousedown", function (e) {
        e.preventDefault(); acAccept(+n.dataset.i); });
    });
    var sel = box.querySelector(".it.sel");
    if (sel) sel.scrollIntoView({ block: "nearest" });
  }

  function acMove(d) {
    if (!acItems.length) return;
    acSel = (acSel + d + acItems.length) % acItems.length;
    acRender();
  }

  function acAccept(i) {
    var inp = el("msg"), it = acItems[i]; if (!it) return;
    var t = acToken();
    inp.value = inp.value.slice(0, t.start) + it.ins +
                inp.value.slice(t.caret);
    var pos = t.start + it.ins.length;
    inp.setSelectionRange(pos, pos);
    inp.focus(); acRender();
  }

  el("msg").addEventListener("input", function () { acSel = 0; acRender(); });
  el("msg").addEventListener("keydown", function (e) {
    if (acOpen()) {
      if (e.key === "ArrowDown") { e.preventDefault(); acMove(1); return; }
      if (e.key === "ArrowUp") { e.preventDefault(); acMove(-1); return; }
      if (e.key === "Tab" || e.key === "Enter") {
        e.preventDefault(); acAccept(acSel); return; }
      if (e.key === "Escape") { e.preventDefault(); acClose(); return; }
    }
    if (e.key === "Enter") sendMsg();
  });
  document.addEventListener("click", function (e) {
    if (acOpen() && !el("ac").contains(e.target) &&
        e.target !== el("msg")) acClose();
  });

  // #136 unit glide: display position eases toward the unit's target
  // (latest live order coordinate, else its home tile) so ordered units
  // visibly path across the map instead of teleporting. Speed is a
  // fixed world-px/s capped by a fraction of the remaining distance, so
  // far orders march and close orders settle without overshoot.
  var WALK_PX_S = 110;
  function stepMotion(dt) {
    var now = performance.now();
    state.units.forEach(function (u) {
      var mo = state.motion[u.id];
      if (mo) {
        // Active Patrol loop (#159)
        if (mo.patrol && mo.patrol.length >= 2) {
          var pt = mo.patrol[mo.pi || 0];
          u.tx = pt.x; u.ty = pt.y;
          if (Math.hypot(u.tx - u.x, u.ty - u.y) < 3) {
            mo.pi = ((mo.pi || 0) + 1) % mo.patrol.length;
            u.tx = mo.patrol[mo.pi].x; u.ty = mo.patrol[mo.pi].y;
          }
        } else if (mo.gather) {
          // Active Gather / Harvest loop between Gold Vein and Keep (#159)
          var g = mo.gather;
          u.tx = g.phase === 0 ? g.gx : g.kx;
          u.ty = g.phase === 0 ? g.gy : g.ky;
          if (Math.hypot(u.tx - u.x, u.ty - u.y) < 4) {
            mo.acting = true;
            g.wait = (g.wait || 0) + dt;
            if (g.wait >= 1.5) {
              g.wait = 0;
              mo.acting = false;
              if (g.phase === 0) {
                g.phase = 1;
                pushFx("text", u.x, u.y - 10, "Mining...", "#ffd54a", 1.2);
              } else {
                g.phase = 0;
                tone("gather");
                pushFx("text", u.x, u.y - 14, "+25 Gold", "#ffd54a", 1.8);
              }
            }
          }
        } else if (mo.combat) {
          // Active Combat / Quest Assault loop (#159)
          u.tx = mo.combat.x; u.ty = mo.combat.y;
          if (Math.hypot(u.tx - u.x, u.ty - u.y) < 6) {
            mo.acting = true;
            u.acting = true;
            if (now - (mo.combat.lastHit || 0) > 1600) {
              mo.combat.lastHit = now;
              pushFx("text", u.x + (Math.random() - 0.5) * 16,
                     u.y - 16, "Strike!", "#f85149", 1.2);
            }
          }
        }
      }
      var dx = u.tx - u.x, dy = u.ty - u.y;
      var d = Math.hypot(dx, dy);
      if (d < 1.5) {
        u.x = u.tx; u.y = u.ty;
        if (mo && u.pts && mo.wi < u.pts.length - 1) {
          mo.wi++; u.tx = u.pts[mo.wi].x; u.ty = u.pts[mo.wi].y;
          u.moving = true;
        } else u.moving = false;
      } else {
        var v = Math.max(WALK_PX_S, d * 2.2) * dt;
        if (v >= d) {
          u.x = u.tx; u.y = u.ty;
          if (mo && u.pts && mo.wi < u.pts.length - 1) {
            mo.wi++; u.tx = u.pts[mo.wi].x; u.ty = u.pts[mo.wi].y;
            u.moving = true;
          } else u.moving = false;
        } else { u.x += dx / d * v; u.y += dy / d * v; u.moving = true; }
      }
      if (mo) { mo.x = u.x; mo.y = u.y; u.acting = !!mo.acting; }
    });
  }

  // #136 day/night: WC3-style cycle anchored to the session's first
  // event (world.started), so replay + live agree. 600s period:
  // day 0-50%, dusk ramp 50-60%, night 60-90%, dawn ramp 90-100%.
  // Purely cosmetic; returns 0 when the toggle is off (zero cost).
  function nightFactor() {
    if (!state.dn) return 0;
    var now = state.srvClock
      ? state.srvClock.srv + (performance.now() - state.srvClock.perf)/1000
      : Date.now() / 1000;
    var t0 = (state.world && (state.world.started || state.world.now)) ||
             now;
    var ph = (((now - t0) % 600) + 600) % 600 / 600;
    return ph < 0.5 ? 0 : ph < 0.6 ? (ph - 0.5) / 0.1
         : ph < 0.9 ? 1 : (1 - ph) / 0.1;
  }

  var last = performance.now(), frames = 0, ft = 0, lastAmb = 0;
  function loop(t) {
    var dt = Math.min(0.1, (t - last) / 1000); last = t;
    eng.step(dt);
    stepMotion(dt);
    var th = Theme.get();
    eng.render({ tiles: state.map, fog: state.map && state.map.fog,
      pois: state.map && state.map.pois, pings: livePings(),
      workers: state.workers, fades: state.fades,
      waypoints: state.waypoints, ravens: state.ravens,
      srvClock: state.srvClock, decision: meetingCall(),
      weather: state.weather, fx: state.fx,
      night: nightFactor(),
      units: state.units, buildings: state.buildings }, th);
    eng.minimap(el("mm"), { tiles: state.map,
      fog: state.map && state.map.fog, units: state.units,
      buildings: state.buildings, pings: state.pings,
      mmFilter: state.mmFilter }, th);
    // #159 Animated Live 3D-style Portrait in bottom console
    var pcv = el("portcv");
    if (pcv && Theme.drawPortrait) {
      var pItem = state.units.filter(function (x) {
        return x.id === state.sel; })[0] ||
        state.buildings.filter(function (x) {
          return x.id === state.selB; })[0] ||
        state.units[0] || state.buildings[0];
      Theme.drawPortrait(pcv.getContext("2d"), pItem,
                         pcv.width, pcv.height, t);
    }
    // #159 Ambient weather/nature sound cues (storm thunder / meadow birds)
    if (snd.on && _ac && t - lastAmb > 9000) {
      lastAmb = t;
      var cond = state.weather && state.weather.condition;
      if (cond === "storm") tone("thunder");
      else if (cond === "clear" && !nightFactor()) tone("bird");
    }
    frames++; ft += dt;
    if (frames >= 60) {
      el("fps").textContent = Math.round(frames / ft) + "fps" +
        (BENCH ? " (bench)" : "");
      frames = 0; ft = 0;
    }
    requestAnimationFrame(loop);
  }

  if ("serviceWorker" in navigator && location.protocol !== "file:")
    navigator.serviceWorker.register("/sw.js").catch(function () {});
  connect();
  requestAnimationFrame(loop);
})(window);
