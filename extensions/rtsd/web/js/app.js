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
    feed: [],                // raw recent events (comms feed lands in #128)
    barks: {}
  };

  function esc(s) {
    return (s || "").replace(/[&<>"']/g,
      function (c) { return { "&": "&amp;", "<": "&lt;", ">": "&gt;",
        '"': "&quot;", "'": "&#39;" }[c]; });
  }
  function el(id) { return document.getElementById(id); }
  function logFeed(m) {
    state.feed.unshift(m);
    if (state.feed.length > 200) state.feed.pop();
    el("feed").innerHTML = state.feed.map(function (f) {
      return "<div>" + esc(f) + "</div>";
    }).join("");
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
    // unit stands in its lane's region, or wanders around its class capital
    var ids = Object.keys(map.caps);
    var reg = map.caps[u.lane] ? u.lane
      : ids[Engine.hash(String(u.id)) % ids.length];
    var c = map.caps[reg];
    var h = Engine.hash(String(u.id));
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
    state.units = (w.units || []).map(function (u) {
      var p = unitPos(u, state.map);
      var ack = state.acks[u.id];
      if (ack && now - ack.t0 > 4000) { delete state.acks[u.id]; ack = 0; }
      var live = u.status_live || u.status;
      // death animation: a hero that just failed gets a fade marker (#125)
      if (prev[u.id] && prev[u.id].status_live !== "failed" &&
          live === "failed") pushFade(p.x, p.y, u.cls);
      return { id: u.id, x: p.x, y: p.y, cls: u.cls || "Squire",
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
    // worker peasants carry from/to + server ts; engine lerps per frame
    // via the snapshot's server->client clock offset
    state.srvClock = { srv: w.now || 0, perf: performance.now() };
    state.workers = w.workers || [];
    // queued waypoints (#127): every order intent with x/y on a hero's
    // queue is a numbered flag; state comes from the intent file
    // (queued = ghost, acknowledged = solid, consumed = hidden)
    state.waypoints = [];
    state.units.forEach(function (u) {
      var ords = (u.unit && u.unit.orders) || [];
      ords.forEach(function (o, i) {
        if (o.state === "consumed" ||
            typeof o.x !== "number" || typeof o.y !== "number") return;
        state.waypoints.push({ x: (o.x + .5) * TILE, y: (o.y + .5) * TILE,
          n: i + 1, state: o.state, order: o.order,
          ux: u.x, uy: u.y });
      });
    });
    // buildings sit on their fixed server-assigned plots (#123)
    var regs = Object.keys(state.map.caps);
    state.buildings = (w.buildings || []).map(function (b, i) {
      var out = { id: b.id, bid: b.id, activity: b.activity,
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

  function applySnapshot(snap) {
    state.snap = snap;
    state.world = snap.world || null;
    var m2 = state.world ? state.world.map : null;
    if (m2 && m2.tile_region) {          // authoritative server map (#122)
      if (!state.map || state.map.sig !== m2.sig) state.map = serverMap(m2);
      state.map.fog = new Uint8Array(m2.fog || []);
      state.map.mark = new Uint8Array(m2.mark || []);
      state.map.pois = m2.pois || [];
      state.map.tint = laneTint(m2);
    } else {
      var regs = m2 ? m2.regions : [];
      var key = regs.map(function (r) { return r.id; }).join(",");
      if (!state.map || state.mapKey !== key) {
        state.map = buildMap(regs); state.mapKey = key;
      }
    }
    if (!state._camInit && state.map) {
      var c0 = state.map.caps[Object.keys(state.map.caps)[0]];
      eng.centerOn(c0.cx * TILE, c0.cy * TILE); state._camInit = true;
    }
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
        } else if (m.type === "tick") { got = true; applyTick(m); }
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

  function noteEvent(ev) {
    var t = new Date((ev.ts || 0) * 1000).toLocaleTimeString();
    logFeed(t + " " + ev.type + (ev.tool ? " " + ev.tool : ""));
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
    return { now: Date.now() / 1000, units: units, buildings: blds,
      resources: { gold: 0, lumber_pct: 0, supply_used: nUnits,
                   supply_cap: 8, upkeep: "low" },
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
      ? ("GOLD ~" + (r.gold | 0) + "  LUMBER " + (r.lumber_pct | 0) +
         "%  SUPPLY " + r.supply_used + "/" + r.supply_cap +
         "  UPKEEP " + (r.upkeep || "-"))
      : "";
    // quest log
    var qs2 = w.quests || (state.snap || {}).tasks || [];
    el("tlist").innerHTML = qs2.map(function (t) {
      return "<div class='task " + (t.blocked ? "blocked" : "") + "'>" +
        "<span class='id'>" + esc(t.effort) + "/" + esc(t.id) + "</span> " +
        "<b>" + esc(t.title) + "</b><br><span class='meta'>" +
        esc(t.status) + (t.deps && t.deps.length ?
          " / needs " + esc(t.deps.join(",")) : "") +
        "</span></div>";
    }).join("") || "<span class='meta'>no quests</span>";
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
    // decisions (war council content until #129 restyles it)
    var decs = (state.snap || {}).decisions || [];
    el("council").classList.toggle("on", decs.length > 0);
    el("decs").innerHTML = decs.map(function (d) {
      return "<div class='dec'><b>" + esc(d.kind || "decision") + "</b>" +
        "<div class='meta'>" + esc(d.prompt || d.summary || "") + "</div>" +
        (d.options || ["allow", "deny"]).map(function (o, i) {
          return "<button data-dec='" + esc(d.id) + "' data-idx='" + i +
            "'>" + esc(o) + "</button>";
        }).join("") + "</div>";
    }).join("");
    // idle-worker button (#127): real count from world.idle
    var nIdle = (w.idle || []).length;
    el("idleBtn").textContent = "idle:" + nIdle;
    el("idleBtn").disabled = !nIdle;
    el("themeBtn").textContent = "theme: " + th.name;
  }

  function rows(list, fmt) {
    return (list || []).map(fmt).join("") ||
           "<span class='meta'>none</span>";
  }

  // Inspector for a selected building - every field is live data from
  // GET /buildings/<id> (issue #123: no fake actions).
  function buildingHtml(d) {
    var h = "<b>" + esc(d.name) + "</b> <span class='meta'>" +
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
          esc(s.transport) + " | " + (s.enabled ? "enabled" : "disabled") +
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
      return "<span class='inv' title='" + esc(it.gate + " " +
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
      (kit ? " <span class='meta'>kit:</span>" + kit : "") +
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
  function issueOrder(order, extra) {
    state.selAll.forEach(function (id) {
      var it = { kind: "order", to: id, order: order };
      if (extra) for (var k in extra) it[k] = extra[k];
      RTS.intent(it);
    });
    selUnits().forEach(function (u) {
      state.acks[u.id] = { text: barkLine(u.cls, 1),
                           t0: performance.now() };
    });
  }

  function cardBtn(act, label, enabled, title, armed) {
    return "<button data-act='" + esc(act) + "'" +
      (enabled ? "" : " disabled") +
      (armed ? " class='armed'" : "") +
      " title='" + esc(title || "") + "'>" + esc(label) + "</button>";
  }

  function renderCard(u) {
    var card = el("cmdcard"), multi = state.selAll.length > 1;
    var raw = u && u.unit ? u.unit : u;   // renderable vs raw world unit
    var kit = (raw && raw.kit) || [];
    var armed = state.pending ? state.pending.order : null;
    var h = "";
    if (state.pending)
      h += "<span class='meta tgt'>click target: " +
        esc(state.pending.order) + "</span>";
    if (!state.selAll.length) {
      h += "<span class='meta tgt'>select a unit</span>";
      for (var i = 0; i < 9; i++) h += "<button disabled>-</button>";
      card.innerHTML = h; return;
    }
    // shared orders: move/stop work for the whole selection; the rest is
    // single-unit only (issue: multi-select = shared actions only)
    h += cardBtn("move", "Move", true,
                 "click map target (lane/dir reassignment)",
                 armed === "move");
    h += cardBtn("stop", "Stop", true, "halt current order");
    h += cardBtn("hold", "Hold", !multi, "park: take no new orders");
    h += cardBtn("patrol", "Patrol", !multi,
                 "afk-loop the unit's lane between quest markers");
    h += cardBtn("attack", "Attack", !multi,
                 "click a quest marker / tile to target",
                 armed === "attack");
    var sp = raw && SPECIALS[raw.cls];
    h += cardBtn("special", sp ? sp.label : "-", !!(sp && !multi),
                 sp ? "class special: " + sp.id : "no class special",
                 !!(sp && armed === sp.id));
    // ability slots: full kit vocabulary, disabled where the profile
    // lacks the backing tools (verified vs agents/*.md via world.py kit)
    KIT_SLOTS.forEach(function (name) {
      var label = name === "March" && kit.indexOf("Verify") >= 0
        ? "Verify" : name;
      var has = kit.indexOf(name) >= 0 || kit.indexOf(label) >= 0;
      if (label === "Verify") has = kit.indexOf("Verify") >= 0;
      h += cardBtn("ability:" + (label === "Verify" ? "Verify" : name),
                   label, has && !multi,
                   ABILITY_HINT[label] || name);
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
    }
  };

  // ---- boot ------------------------------------------------------------

  var eng = Engine.create(el("cv"));

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
      if (!u.bark)   // no heartbeat note -> class "selected" line
        state.acks[u.id] = { text: barkLine(u.cls, 0),
                             t0: performance.now() };
    } else {
      if (!ev.shiftKey) { state.selAll = []; state.sel = null; }
      selectBuilding(eng.pickBuilding(ev.offsetX, ev.offsetY));
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
  // issue intents immediately (#126)
  el("cmdcard").addEventListener("click", function (e) {
    var b = e.target.closest("button[data-act]");
    if (!b || b.disabled || !state.selAll.length) return;
    var act = b.dataset.act;
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
    } else if (act === "patrol") {
      issueOrder("patrol", { lane: (raw && raw.lane) || "" });
    } else {
      issueOrder(act, {});                     // stop / hold
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
    var best = null, qq = 1.5;
    (state.map.pois || []).forEach(function (p) {
      if (p.kind !== "quest") return;
      var d = Math.hypot(p.x - tx, p.y - ty);
      if (d <= qq) { qq = d; best = p; }
    });
    if (bd) { ord = "garrison"; extra.building = bd.id; }
    else if (best) { ord = "attack"; extra.quest = best.ref; }
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
    if (k === "t") { Theme.toggle(); renderPanels(); }
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
  el("themeBtn").onclick = function () { Theme.toggle(); renderPanels(); };

  document.getElementById("decs").addEventListener("click", function (e) {
    var b = e.target.closest("button[data-dec]");
    if (b) RTS.answer(b.dataset.dec, parseInt(b.dataset.idx, 10));
  });
  document.getElementById("send").onclick = function () {
    var v = el("msg").value.trim(); if (!v) return;
    el("msg").value = "";
    var m = v.match(/^\/spawn\s+(\S+)\s+(.+)/);
    if (m) return RTS.intent({ kind: "spawn", profile: m[1], task: m[2] });
    var at = v.match(/^@(\S+)\s+(.+)/);
    if (at) return RTS.intent({ kind: "message", to: at[1], text: at[2] });
    RTS.intent({ kind: "goal", text: v });
  };
  el("msg").addEventListener("keydown", function (e) {
    if (e.key === "Enter") el("send").click();
  });

  var last = performance.now(), frames = 0, ft = 0;
  function loop(t) {
    var dt = Math.min(0.1, (t - last) / 1000); last = t;
    eng.step(dt);
    var th = Theme.get();
    eng.render({ tiles: state.map, fog: state.map && state.map.fog,
      pois: state.map && state.map.pois, pings: livePings(),
      workers: state.workers, fades: state.fades,
      waypoints: state.waypoints,
      srvClock: state.srvClock,
      units: state.units, buildings: state.buildings }, th);
    eng.minimap(el("mm"), { tiles: state.map,
      fog: state.map && state.map.fog, units: state.units,
      buildings: state.buildings, pings: state.pings }, th);
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
