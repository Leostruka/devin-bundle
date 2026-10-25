/* main.js - agent-rts client orchestrator (DevinCraft v3).
   net -> state store -> entity sync -> per-frame ECS update.
   The client renders and relays; the server owns truth (GDD canon). */
import * as THREE from "three";
import { Scene3D } from "./scene.js";
import { RTSCamera } from "./camera.js";
import { Selection } from "./selection.js";
import { Particles } from "./particles.js";
import { Net } from "./net.js";
import { HUD } from "./hud.js";
import { Tour } from "./tour.js";
import { Audio3 } from "./audio.js";
import { FX } from "./fx.js";
import { buildBuilding } from "./buildings.js";
import { buildUnit, updateUnit, setWind, setAlt,
         bindParticles } from "./units.js";
import { Grid } from "./pathing.js";

const MAP_W = 72, MAP_H = 54;
const TZ_OFF = -new Date().getTimezoneOffset() * 60;   // local tz secs

/* persisted client prefs (localStorage rts.*) */
const LS = {
  get(k, d) {
    try { const v = JSON.parse(localStorage.getItem("rts." + k));
          return v ?? d; } catch { return d; }
  },
  set(k, v) {
    try { localStorage.setItem("rts." + k, JSON.stringify(v)); } catch {}
  },
};

const canvas = document.getElementById("gl");
const s3 = new Scene3D(canvas);
const cam = new RTSCamera(s3.camera, canvas);
const net = new Net();
const parts = new Particles(s3.fx);
bindParticles(parts);                        // unit impact sparks -> pool
const audio = new Audio3();
const grid = new Grid();

const state = {
  theme: LS.get("theme", "medieval"),
  world: null, repo: null, decisions: [], feed: [],
  units: new Map(),        // id -> {mesh, data}
  buildings: new Map(),    // id -> {mesh, data}
  workers: new Map(),      // id -> {mesh, from, to, t}
};
const unitMeshes = new Map(), bldMeshes = new Map();

/* WC3 "!" quest markers: billboarded exclamations over discovered POIs */
function syncPOIs(pois) {
  if (!state._poiTex) {
    const cv = document.createElement("canvas");
    cv.width = cv.height = 64;
    const c = cv.getContext("2d");
    c.font = "bold 52px sans-serif"; c.textAlign = "center";
    c.textBaseline = "middle";
    c.shadowColor = "rgba(0,0,0,.9)"; c.shadowBlur = 5;
    c.fillStyle = "#ffd54a"; c.fillText("!", 32, 36);
    state._poiTex = new THREE.CanvasTexture(cv);
    state._pois = new Map();
  }
  const seen = new Set();
  for (const p of pois || []) {
    const k = p.x + "," + p.y;
    seen.add(k);
    if (!state._pois.has(k)) {
      const s = new THREE.Sprite(new THREE.SpriteMaterial({
        map: state._poiTex, transparent: true, depthWrite: false }));
      s.position.set(p.x + 0.5, 2.1, p.y + 0.5);
      s.scale.setScalar(1.15);
      s.userData.t = Math.random() * 6.28;
      s3.fx.add(s);
      state._pois.set(k, s);
    }
  }
  for (const [k, s] of [...(state._pois || new Map())])
    if (!seen.has(k)) { s3.fx.remove(s); state._pois.delete(k); }
}

/* ---------- theme ---------- */
function applyTheme(name) {
  state.theme = name;
  LS.set("theme", name);
  s3.setTheme(name);
  audio.theme = name;
  hud.setThemeIcon(name);
  for (const [id, e] of state.buildings) rebuildBuilding(id, e.data);
  for (const [id, e] of state.units) rebuildUnit(id, e.data);
}
function rebuildBuilding(id, b) {
  const old = bldMeshes.get(id);
  const pos = old ? old.position.clone() : null;
  if (old) s3.world.remove(old);
  const g = buildBuilding(id, state.theme);
  g.position.copy(pos || new THREE.Vector3(...siteOf(b)));
  g.userData.bid = id;
  bldMeshes.set(id, g);
  s3.world.add(g);
}
function rebuildUnit(id, u) {
  const old = unitMeshes.get(id);
  const pos = old ? old.position.clone() : null;
  const ud = old ? old.userData : null;
  if (old) s3.world.remove(old);
  const g = buildUnit(u, state.theme);
  if (pos) g.position.copy(pos);
  if (ud) { g.userData.home = ud.home; g.userData.state = ud.state;
            g.userData.path = ud.path; }
  unitMeshes.set(id, g);
  s3.world.add(g);
}
function siteOf(b) {
  const xy = b.pos?.xy || [36, 27];
  return [xy[0], 0, xy[1]];
}

/* ---------- entity sync ---------- */
function syncBuildings(list) {
  const seen = new Set();
  grid.blocked.clear();
  for (const b of list || []) {
    seen.add(b.id);
    const xy = b.pos?.xy || [36, 27];
    grid.block(xy[0], xy[1], 1);
    if (!bldMeshes.has(b.id)) {
      parts.bubble(b.pos?.xy?.[0] ?? 36, b.pos?.xy?.[1] ?? 27, "gold");
      const g = buildBuilding(b.id, state.theme);
      g.position.set(...siteOf(b));
      g.userData.bid = b.id;
      bldMeshes.set(b.id, g);
      s3.world.add(g);
    }
    state.buildings.set(b.id, { data: b });
    const g = bldMeshes.get(b.id);
    g.userData.activity = b.activity || 0;
    if (g.userData.fire)                        // forge fire scales w/ work
      g.userData.fire.intensity = 8 + Math.min(40, b.activity * 2);
  }
  for (const id of [...bldMeshes.keys()])
    if (!seen.has(id)) { s3.world.remove(bldMeshes.get(id));
                         bldMeshes.delete(id); state.buildings.delete(id); }
}

function unitHome(id, idx) {
  /* stable ring slot: hash unit id so reordered snapshots don't shuffle
     home positions; idx only disambiguates rare hash collisions */
  const th = state.world?.buildings?.find(b => b.id === "town-hall");
  const xy = th?.pos?.xy || [36, 27];
  let h = 0;
  for (const c of String(id)) h = (h * 31 + c.charCodeAt(0)) | 0;
  const a = ((h >>> 0) % 360) * Math.PI / 180 + idx * 0.02;
  return [xy[0] + Math.cos(a) * 3.2, xy[1] + Math.sin(a) * 3.2];
}

function mapStatus(u) {
  const s = String(u.status_live || u.status || "").toLowerCase();
  if (/dead|gone|stale|expired/.test(s)) return "dead";
  if (/error|fail/.test(s)) return "error";
  if (/wait|gate|block|permission/.test(s)) return "gate_wait";
  if (/attack|combat/.test(s)) return "attack";
  if (/work|run|active|busy|write|exec/.test(s)) return "work";
  return "idle";
}

function syncUnits(list) {
  const seen = new Set();
  let i = 0;
  for (const u of list || []) {
    seen.add(u.id);
    let g = unitMeshes.get(u.id);
    if (!g) {
      g = buildUnit(u, state.theme);
      const h = unitHome(u.id, i);
      parts.confetti(h[0], h[1]);                  // WC3 spawn poof
      g.position.set(h[0], 0, h[1]);
      g.userData.home = h;
      unitMeshes.set(u.id, g);
      s3.world.add(g);
    }
    const D = g.userData;
    /* WC3 hit flash: hp drop or fresh error state = damage tint */
    const prevHp = D.info?.hp ?? 100, wasErr = D._prevSt === "error";
    const nSt = mapStatus(u);
    if ((u.hp ?? 100) < prevHp || (nSt === "error" && !wasErr)) {
      D.flash = 0.22;
      /* WC3 combat feedback: damage to a commanded unit pulses a
         red screen-edge vignette */
      if (sel.sel?.has(u.id)) {
        const dv = document.getElementById("dmgvig");
        dv.style.opacity = "1";
        clearTimeout(dv._t);
        dv._t = setTimeout(() => dv.style.opacity = "0", 130);
      }
      /* WC3 "under attack": auto minimap ping + horn, throttled 4s */
      const nowP = performance.now();
      if (!state._lastAtkPing || nowP - state._lastAtkPing > 4000) {
        state._lastAtkPing = nowP;
        hud._pings.push({ x: g.position.x, y: g.position.z, t: nowP });
        audio.warn();
      }
    }
    /* WC3 kill feedback: fresh corpse -> xp floater + death thud;
       suppressed while the tile sits under unexplored shroud */
    if (nSt === "dead" && D._prevSt !== "dead") {
      const dm = state.world?.map;
      const di = dm?.fog?.length ?
        Math.round(g.position.z) * dm.w + Math.round(g.position.x) : -1;
      const dSeen = di < 0 || (dm.fog[di] ?? 0) >= 1 ||
                    !!dm.reveal?.has(di);
      if (dSeen) {
        fx.floatText(g.position.x, g.position.z, "+xp", "gold");
        parts.puff(g.position.x, 0.5, g.position.z);
      }
      audio.die();
      /* WC3 corpse decal: dark pool under the fallen unit, fades out */
      if (dSeen) {
      const pool = new THREE.Mesh(
        new THREE.CircleGeometry(0.55, 14),
        new THREE.MeshBasicMaterial({ color: 0x3a1210,
          transparent: true, opacity: 0.6, depthWrite: false }));
      pool.rotation.x = -Math.PI / 2;
      pool.position.set(g.position.x, 0.06, g.position.z);
      s3.fx.add(pool);
      state._pools = state._pools || [];
      state._pools.push({ m: pool, t: 0 });
      }
      if (sel.sel?.has(u.id)) cam.shake(0.55); // WC3: losing a unit kicks
      /* WC3 hero death: always announced + heavier blast */
      if ((u.level ?? 0) >= 4) {
        cam.shake(0.8);
        hud.alert("crit", "war",
          (u.name || u.id) + " has fallen");
        if (dSeen)
          parts.spark(g.position.x, 1.2, g.position.z, 40);
      }
    }
    D._prevSt = nSt;
    /* WC3 hero aura: level>=4 units carry a gold underglow ring */
    if ((u.level ?? 0) >= 4 && !D.heroRing) {
      D.heroRing = new THREE.Mesh(
        new THREE.RingGeometry(0.62, 0.86, 28),
        new THREE.MeshBasicMaterial({ color: 0xffd54a,
          transparent: true, opacity: 0.3, side: THREE.DoubleSide,
          depthWrite: false }));
      D.heroRing.rotation.x = -Math.PI / 2;
      D.heroRing.position.y = 0.045;
      g.add(D.heroRing);
    }
    /* WC3 level-up: gold flash + rising fanfare + spark column */
    if ((u.level ?? 0) > (D.info?.level ?? u.level ?? 0)) {
      D.gflash = 0.9;
      parts.spark(g.position.x, 1.5, g.position.z, 30);
      fx.floatText(g.position.x, g.position.z, "LEVEL " + u.level,
                   "gold");
      audio.levelup();
    }
    D.info = u;
    /* order -> waypoint path (latest order with x/y wins) */
    const ord = (u.orders || []).filter(o =>
      o.x !== undefined && o.y !== undefined &&
      o.status !== "done").slice(-1)[0];
    if (ord && (!D._lastOrd || D._lastOrd !== ord.id)) {
      D._lastOrd = ord.id;
      /* WC3 waypoint flag color follows the order verb */
      if (D.pathLine) D.pathLine.material.color.setHex(
        { attack: 0xff5040, patrol: 0x66aaff, guard: 0xbf8bff,
          set_rally: 0xe8c86a }[ord.order] || 0x6fe39a);
      const p = grid.path(
        Math.round(g.position.x), Math.round(g.position.z),
        ord.x, ord.y);
      if (p && p.length > 1) {
        D.path = p.slice(1); D.state = "move";
        /* WC3 waypoint post: mini flag at the destination while the
           unit travels, cleared on arrival */
        const wp = p[p.length - 1];
        const fl = new THREE.Mesh(new THREE.ConeGeometry(0.16, 0.5, 6),
          new THREE.MeshBasicMaterial({ color:
            ord.order === "attack" ? 0xff5040 : 0x6fe39a,
            transparent: true, opacity: 0.85, depthWrite: false }));
        fl.position.set(wp[0] + 0.5, 0.3, wp[1] + 0.5);
        s3.fx.add(fl);
        state._wflags = state._wflags || [];
        state._wflags.push({ m: fl, uid: u.id, t: 0 });
      }
    }
    if (D.state !== "move") D.state = mapStatus(u);
    u._pos = { x: g.position.x, y: g.position.z };
    state.units.set(u.id, { data: u });
    i++;
  }
  for (const [id, g] of [...unitMeshes]) {
    if (!seen.has(id)) {
      const rm = state.world?.map;
      const ri = rm?.fog?.length ?
        Math.round(g.position.z) * rm.w + Math.round(g.position.x) : -1;
      if (ri < 0 || (rm.fog[ri] ?? 0) >= 1 || rm.reveal?.has(ri))
        parts.puff(g.position.x, g.position.y + 0.8, g.position.z);
      s3.world.remove(g); unitMeshes.delete(id);
      state.units.delete(id);
    }
  }
}

function syncWorkers(list) {
  const seen = new Set();
  for (const w of list || []) {
    seen.add(w.id);
    if (!state.workers.has(w.id)) {
      const m = new THREE.Mesh(
        new THREE.CapsuleGeometry(0.16, 0.3, 2, 6),
        new THREE.MeshStandardMaterial({ color: 0xc9b896 }));
      m.castShadow = true;
      state.workers.set(w.id, { mesh: m, from: w.from, to: w.to,
                                t: Math.random() });
      s3.fx.add(m);
    } else {
      const e = state.workers.get(w.id);
      e.from = w.from; e.to = w.to;
    }
  }
  for (const [id, e] of [...state.workers])
    if (!seen.has(id)) { s3.fx.remove(e.mesh); state.workers.delete(id); }
}

/* ---------- net wiring ---------- */
const hud = new HUD({
  command: (id) => command(id),
  tour: () => tour.start(),
  ticketSel: (n) => LS.set("ticket", n),
  theme: () => {
    const next = state.theme === "medieval" ? "office" : "medieval";
    applyTheme(next);
    net.send({ type: "set", key: "theme", value: next });
  },
  ssao: () => { if (s3.ssao) s3.ssao.enabled = !s3.ssao.enabled; },
  audio: () => { LS.set("audio", audio.toggle()); },
  score: async () => {
    const r = await fetch("/score");
    if (r.ok) hud.score(await r.json());
  },
  idlePing: () => {
    /* WC3 idle-worker button/`~`: each press cycles to the next idle
       unit and selects it (deny buzz when nobody is idle) */
    const idle = [...unitMeshes.values()]
      .filter(g => g.userData.state === "idle");
    if (!idle.length) { audio.deny(); return; }
    state._idleN = ((state._idleN ?? -1) + 1) % idle.length;
    const u = idle[state._idleN];
    hud.act.select(u.userData.id, true);
  },
  select: (id, center) => {
    const g = unitMeshes.get(id);
    if (!g) return;
    sel.clear(); sel.add(g); sel.onchange();
    if (center) cam.focus(g.position.x, g.position.z, 26);
  },
  focusHero: (i) => {
    const ids = [...unitMeshes.keys()];
    if (ids[i]) hud.act.select(ids[i], true);
  },
  center: (xy) => cam.focus(xy[0], xy[1], 30),
  jumpAlert: () => {                     // WC3 Space -> last alert spot
    const p = hud.lastAlert;
    if (p) cam.focus(p[0] + 0.5, p[1] + 0.5, 24);
    else audio.deny();
  },
  gateAnswer: (id, choice) =>
    net.send({ type: "gate_answer", id, choice }),
});

const sel = new Selection(s3.camera, canvas, net, {
  scene: s3.scene,
  getUnits: () => unitMeshes,
  getBuildings: () => bldMeshes,
});
sel.onchange = () => {
  const first = sel.activeId && sel.sel.has(sel.activeId)
    ? sel.activeId : [...sel.sel][0];
  const u = state.units.get(first)?.data ||
            state.buildings.get(first)?.data;
  hud.portrait(u, sel.sel.size);
  hud.subgroups([...sel.sel].map(id =>
    state.units.get(id)?.data || state.buildings.get(id)?.data)
    .filter(Boolean), sel.activeId);
  updateRallyLineVis();
  audio.blip("blue");
  /* WC3 select bark: the active unit's class voice answers "yes?" */
  const au = state.units.get(sel.activeId ||
    [...sel.sel][0])?.data;
  if (au) audio.bark(au.cls, "select");
};
sel.onorder = (order, x, y) => {
  audio.order();
  /* WC3 order ack: active subgroup's class voice acknowledges */
  const ou = state.units.get(sel.activeId)?.data;
  if (ou) audio.bark(ou.cls, "order");
  if (order === "set_rally") setRallyFlag(x, y);
};
/* WC3 Tab: cycling the active subgroup updates portrait + chips
   without touching the actual selection set */
sel.ondisarm = () => hud.armCmd(null);
sel.onsubgroup = (id) => {
  const u = state.units.get(id)?.data;
  if (u) hud.portrait(u, sel.sel.size);
  hud.subgroups([...sel.sel].map(i =>
    state.units.get(i)?.data || state.buildings.get(i)?.data)
    .filter(Boolean), id);
  audio.blip("green");
};
/* WC3 rally flag: persistent marker at the last rally point */
function setRallyFlag(x, y) {
  if (!state._rally) {
    const g = new THREE.Group();
    const pole = new THREE.Mesh(
      new THREE.CylinderGeometry(0.04, 0.04, 2.2),
      new THREE.MeshStandardMaterial({ color: 0x6e5a41 }));
    pole.position.y = 1.1;
    const fl = new THREE.Mesh(
      new THREE.PlaneGeometry(0.9, 0.5),
      new THREE.MeshBasicMaterial({ color: 0x6fe39a,
                                    side: THREE.DoubleSide }));
    fl.position.set(0.45, 1.9, 0);
    g.add(pole, fl);
    g.userData.fl = fl;
    s3.fx.add(g);
    state._rally = g;
  }
  state._rally.position.set(x + 0.5, 0, y + 0.5);
  state._rally.visible = true;
  state.rally = { x, y };                    // minimap glyph
  /* WC3 rally line: thin gold tether from the rally-owning building
     (town hall) to the flag, shown while a building is selected */
  if (!state._rallyLine) {
    const g = new THREE.BufferGeometry();
    g.setAttribute("position",
      new THREE.BufferAttribute(new Float32Array(6), 3));
    state._rallyLine = new THREE.Line(g, new THREE.LineBasicMaterial({
      color: 0xe8c86a, transparent: true, opacity: 0.55 }));
    state._rallyLine.frustumCulled = false;
    s3.fx.add(state._rallyLine);
  }
  const th = [...(state.buildings.values())]
    .map(b => b.data).find(b => b.id === "town-hall") ||
    [...state.buildings.values()][0]?.data;
  const a = th?.pos?.xy || [36, 27];
  const lp = state._rallyLine.geometry.attributes.position;
  lp.setXYZ(0, a[0] + 0.5, 0.12, a[1] + 0.5);
  lp.setXYZ(1, x + 0.5, 0.12, y + 0.5);
  lp.needsUpdate = true;
  updateRallyLineVis();
}
/* rally tether renders only while a building is selected (WC3 rule) */
function updateRallyLineVis() {
  if (!state._rallyLine) return;
  const anyBld = [...sel.sel].some(id => bldMeshes.has(id));
  state._rallyLine.visible = !!(state._rally?.visible && anyBld);
}
sel.ongroup = (n) => hud.alert("warn", "grp", "control group " + n + " bound");
sel.onrecall = (n, center) => {
  if (!center) return;                       // double-tap N = center (WC3)
  const first = [...sel.sel][0];
  const g = unitMeshes.get(first) || bldMeshes.get(first);
  if (g) cam.focus(g.position.x, g.position.z, 26);
};

const fx = new FX(parts, audio, hud, s3.camera);
fx.fogFn = () => state.world?.map;   // world fx respect fog-of-war
parts.fogFn = fx.fogFn;              // meteor trails too
/* audio needs a user gesture: first pointerdown anywhere unlocks
   the AudioContext and starts the ambient wind loop (idempotent) */
addEventListener("pointerdown", () => audio.resume());
/* WC3 Alt-hold shows every overhead plate */
addEventListener("keydown", e => { if (e.code === "AltLeft" ||
  e.code === "AltRight") setAlt(true); });
addEventListener("keyup", e => { if (e.code === "AltLeft" ||
  e.code === "AltRight") setAlt(false); });
const tour = new Tour();
hud.ticket = LS.get("ticket", null);
audio.enabled = LS.get("audio", true);
const savedCam = LS.get("cam", null);
if (savedCam) cam.jump(savedCam.x, savedCam.z, savedCam.d);
window.__rts = { cam, state, sel, unitMeshes, bldMeshes };  // debug/CDP
applyTheme(state.theme);
let tourPrompted = false;

/* minimap click = camera jump; alt-click or Ping mode = WC3 ping */
document.getElementById("minimap").onclick = (e) => {
  const r = e.target.getBoundingClientRect();
  const mx = (e.clientX - r.left) / r.width * MAP_W,
        my = (e.clientY - r.top) / r.height * MAP_H;
  if (e.altKey || hud._mmf === "ping") {
    hud._pings.push({ x: mx, y: my, t: performance.now() });
    net.send({ type: "order", to: "all", order: "ping",
               x: Math.round(mx), y: Math.round(my) });
    audio.order();
    return;
  }
  cam.focus(mx, my);
};

net.on("open", () => hud.alert("warn", "net", "connected to the Workshop"));
net.on("snapshot", (m) => {
  state.world = m.world; state.repo = m.repo;
  if (m.world?.now) { state.worldNow = m.world.now;
                      state.nowT = clock.elapsedTime; }
  state.decisions = m.decisions || [];
  state.feed = [...(m.world?.feed || [])];
  if (m.prefs?.theme && m.prefs.theme !== state.theme)
    applyTheme(m.prefs.theme);
  const h = (location.hash.match(/theme=(\w+)/) || [])[1];
  if (h && h !== state.theme) applyTheme(h);
  if (m.world?.map) {
    /* WC3 vision: own base is always revealed: r=6 around buildings,
       r=4 around unit home slots (world fog stays canonical) */
    const mm = m.world.map;
    state.reveal = new Set();
    const rv = (cx, cy, r) => {
      for (let dy = -r; dy <= r; dy++)
        for (let dx = -r; dx <= r; dx++)
          if (dx * dx + dy * dy <= r * r) {
            const ix = Math.round(cx) + dx, iy = Math.round(cy) + dy;
            if (ix >= 0 && iy >= 0 && ix < mm.w && iy < mm.h)
              state.reveal.add(iy * mm.w + ix);
          }
    };
    for (const b of m.world.buildings || []) {
      const xy = b.pos?.xy;
      if (xy) rv(xy[0] + 0.5, xy[1] + 0.5, 6);
    }
    (m.world.units || []).forEach((u, i) => {
      const h = unitHome(u.id, i); rv(h[0], h[1], 4);
    });
    mm.reveal = state.reveal;
    /* WC3 reveal peel: expanding rings where the shroud just opened */
    if (state._prevReveal) {
      let spawned = 0;
      for (const idx of state.reveal) {
        if (state._prevReveal.has(idx) || spawned >= 10) continue;
        const fx0 = idx % mm.w, fz0 = Math.floor(idx / mm.w);
        const r = new THREE.Mesh(new THREE.RingGeometry(0.3, 0.45, 20),
          new THREE.MeshBasicMaterial({ color: 0x9fd8ff,
            transparent: true, opacity: 0.5, side: THREE.DoubleSide,
            depthWrite: false }));
        r.rotation.x = -Math.PI / 2;
        r.position.set(fx0 + 0.5, 0.07, fz0 + 0.5);
        s3.fx.add(r);
        state._revealRings = state._revealRings || [];
        state._revealRings.push({ m: r, t: 0 });
        spawned++;
      }
    }
    state._prevReveal = new Set(state.reveal);
    s3.bakeTerrain(mm, state.reveal);
    s3.clouds(mm);
    s3.critters(mm);
    /* one-time camera rescue: saved cam staring into shroud -> town hall */
    if (!state._camFix && mm.fog?.length) {
      state._camFix = true;
      const ci = Math.round(cam.target.z.t) * mm.w +
                 Math.round(cam.target.x.t);
      if ((mm.fog[ci] ?? 0) < 1 && !state.reveal.has(ci)) {
        const th = (m.world.buildings || [])
          .find(b => b.id === "town-hall") || (m.world.buildings || [])[0];
        if (th?.pos?.xy)
          cam.jump(th.pos.xy[0] + 0.5, th.pos.xy[1] + 0.5, 26);
      }
    }
  }
  syncBuildings(m.world?.buildings);
  syncUnits(m.world?.units);
  syncWorkers(m.world?.workers);
  syncPOIs(m.world?.map?.pois);
  /* idle-unit count on the `~` pill (WC3 shows how many are loafing) */
  const nIdle = [...unitMeshes.values()]
    .filter(g => g.userData.state === "idle").length;
  const ib = document.getElementById("b-idle");
  const iv = "[.]" + (nIdle || "");
  if (ib._v !== iv) { ib.innerHTML = iv; ib._v = iv; }
  hud.topbar(m.world, m.repo);
  /* WC3 age-up fanfare: when the world's age name changes, banner it */
  const ag = m.world?.age?.name;
  if (ag && state._age && state._age !== ag) {
    hud.banner(ag);
    audio.levelup();
  }
  state._age = ag;
  hud.roster(m.world?.units);
  hud.bldstrip(m.world?.buildings);
  hud.tickets(m.repo?.issues);
  hud.feed(state.feed);
  hud.decision(state.decisions);
  /* WC3 quest-giver beacon: a pulsing gold pillar over the town hall
     while a gate decision is waiting on the player */
  if (!state._decBeam) {
    state._decBeam = new THREE.Mesh(
      new THREE.CylinderGeometry(0.45, 0.85, 26, 12, 1, true),
      new THREE.MeshBasicMaterial({ color: 0xffd54a, transparent: true,
        opacity: 0.13, side: THREE.DoubleSide, depthWrite: false }));
    const th = [...state.buildings.values()].map(b => b.data)
      .find(b => b.id === "town-hall");
    const a = th?.pos?.xy || [36, 27];
    state._decBeam.position.set(a[0] + 0.5, 13, a[1] + 0.5);
    s3.fx.add(state._decBeam);
  }
  state._decBeam.visible = state.decisions.length > 0;
  if (!tourPrompted && !LS.get("tour.v1")) {
    tourPrompted = true;
    setTimeout(() => { if (!tour.active) tour.start(); }, 900);
  }
});
net.on("tick", (m) => {
  const d = m.deltas || {};
  let dirty = false;
  for (const [uid, dv] of Object.entries(d)) {
    if (uid === "_map") continue;
    const g = unitMeshes.get(uid);
    if (!g) continue;
    if (dv.expired) g.userData.state = "dead";
    else if (dv.status_live) {
      g.userData.info.status_live = dv.status_live;
      if (g.userData.state !== "move") g.userData.state =
        mapStatus(g.userData.info);
    }
    dirty = true;
  }
  if (d._map && state.world?.map) {
    for (const [t, v] of Object.entries(d._map.fog || {}))
      state.world.map.fog[+t] = v;
    scheduleBake();
  }
});
net.on("fx", (m) => {
  fx.handle(m);
  if (m.fx === "meteor") cam.shake(1.6);
});
net.on("alert", (m) => fx.alert(m));
net.on("repo", (m) => {
  state.repo = m.repo;
  hud.topbar(state.world, m.repo);
  hud.tickets(m.repo?.issues);
});
net.on("decision", (m) => {
  audio.decide();
  if (m.op === "created") {
    state.decisions.push({ id: m.id, prompt: m.prompt,
                           options: m.options, kind: "permission" });
  } else {
    state.decisions = state.decisions.filter(d => d.id !== m.id);
  }
  hud.decision(state.decisions);
});
net.on("feed", (m) => {
  if (m.feed) {
    state.feed.push(m.feed); hud.feed(state.feed);
    /* WC3 quest banner: completions announce big, not just feed lines */
    const txt = m.feed.text || m.feed.msg || "";
    if (/quest complete|objective complete/i.test(txt)) {
      hud.banner(txt.split(/[-–—]/)[0].trim());
      audio.levelup();
    }
  }
});
net.on("ack", (m) => {
  if (m.error) hud.alert("warn", "ack", m.error);
  else if (m.of === "cmd" && m.result && !m.result.ok)
    hud.alert("warn", String(m.cmd),
              m.result.error || JSON.stringify(m.result).slice(0, 120));
});
net.on("close", () => hud.alert("warn", "net", "link lost - retrying"));
net.connect();

let bakeT = null;
function scheduleBake() {
  if (bakeT) return;
  bakeT = setTimeout(() => {
    bakeT = null;
    if (state.world?.map) { s3.bakeTerrain(state.world.map);
                            s3.clouds(state.world.map); }
  }, 800);
}

/* ---------- command card ---------- */
function command(id) {
  audio.resume();
  const armed = { move: "move", patrol: "patrol", attack: "attack",
                  rally: "set_rally" }[id];
  if (armed) {
    /* WC3: orders need a selection: deny buzz + red card flash */
    if (!sel.sel.size) {
      audio.deny(); hud.deny();
      hud.alert("crit", "cmd", "no units selected");
      return;
    }
    sel.arm(armed); hud.armCmd(id); return;
  }
  if (id === "stop" || id === "hold") {
    for (const to of sel.sel.size ? [...sel.sel] : ["all"])
      net.send({ type: "order", to, order: id });
    audio.order(); return;
  }
  if (id === "dispatch") {
    net.post("/intent", { kind: "spawn",
      note: "hero dispatch requested from HUD" });
    return;
  }
  if (id === "forge") {
    if (!hud.ticket) { audio.deny(); hud.deny();
      hud.alert("warn", "forge",
      "pick a ticket on the rail first"); return; }
    net.post("/cmd", { cmd: "forge_ticket", issue: hud.ticket })
      .then(r => hud.alert(r.code === 200 ? "warn" : "crit", "forge",
        r.body.path ? "optimized_ready.md written"
                    : (r.body.error || "forge failed")));
    return;
  }
  if (id === "guard") {
    const u = state.units.get([...sel.sel][0])?.data;
    const body = u?.title || u?.task || "state check";
    net.post("/cmd", { cmd: "laya_guard", state: { body } })
      .then(r => hud.alert("warn", "laya",
        JSON.stringify(r.body).slice(0, 140)));
    return;
  }
  if (id === "compact") { net.post("/cmd", { cmd: "compact_hint" });
                          return; }
  if (id === "power") { powerMenu(); return; }
  if (id === "menu") {
    document.getElementById("gamemenu").classList.toggle("hidden");
    return;
  }
}

function powerMenu() {
  const powers = state.world?.age?.powers || [];
  const el = document.getElementById("powermenu") || (() => {
    const d = document.createElement("div");
    d.id = "powermenu";
    document.getElementById("hud").appendChild(d);
    return d;
  })();
  el.innerHTML = (powers.map(p =>
    `<button data-p="${p.id}">${esc(p.name)} <i>${p.cost}f</i></button>`)
    .join("")) || "<i>no powers yet</i>";
  el.classList.toggle("hidden");
  el.querySelectorAll("button").forEach(b => b.onclick = () => {
    sel.arm({ order: "god_power", power: b.dataset.p });
    el.classList.add("hidden");
  });
}
const esc = (s) => String(s ?? "").replace(/[&<>]/g,
  c => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;" }[c]));

/* ---------- frame loop ---------- */
const clock = new THREE.Clock();
let camT = 0;
function frame() {
  requestAnimationFrame(frame);
  const dt = Math.min(clock.getDelta(), 0.1);
  const t = clock.elapsedTime;
  cam.update(dt);
  if (t - camT > 3) {                      // camera position persists
    camT = t;
    LS.set("cam", { x: cam.target.x.t, z: cam.target.z.t,
                    d: cam.dist.t });
  }
  /* wind: shared by cloth sim + audio soundscape + HUD orb */
  const wx = 0.8 + Math.sin(t * 0.3) * 0.7, wz = Math.cos(t * 0.21) * 0.6;
  setWind(wx, wz);
  const windKph = 4 + Math.hypot(wx, wz) * 10;
  /* day/night: world clock -> daylight fraction (dawn 6h, dusk 18h) */
  const nowS = state.worldNow ? state.worldNow + (t - state.nowT)
                              : Date.now() / 1000;
  const hour = (((nowS + TZ_OFF) % 86400) + 86400) % 86400 / 3600;
  const day = Math.max(0, Math.min(1, Math.sin((hour - 6) / 12 * Math.PI)));
  s3.setDayPhase(day);
  hud.dayOrb(day, windKph);
  if (t - camT > 3) audio.setWind(windKph);
  for (const g of unitMeshes.values()) {
    updateUnit(g, dt, t, s3.camera);
    if (g.userData.heroRing)               // hero aura breathes
      g.userData.heroRing.material.opacity =
        0.22 + Math.sin(t * 2.6) * 0.1;
  }
  /* WC3 army vision: own troops carry a sight halo, so shroud lifts
     around them between server fog updates */
  const avm = state.world?.map;
  if (avm?.fog?.length) {
    const tiles = [];
    for (const g of unitMeshes.values())
      tiles.push(Math.round(g.position.z) * avm.w +
                 Math.round(g.position.x));
    const key = tiles.join(",");
    if (key !== state._armyKey || state._armyMap !== avm) {
      state._armyKey = key; state._armyMap = avm;
      const army = new Set();
      for (const ti of tiles) {
        const ux = ti % avm.w, uz = (ti / avm.w) | 0;
        for (let dz = -2; dz <= 2; dz++)
          for (let dx = -2; dx <= 2; dx++) {
            if (dx * dx + dz * dz > 5) continue;   // round halo r~2.2
            const tx = ux + dx, tz = uz + dz;
            if (tx < 0 || tz < 0 || tx >= avm.w || tz >= avm.h) continue;
            army.add(tz * avm.w + tx);
          }
      }
      s3.paintFog(avm, army);
    }
  }
  /* dissolve finished -> retire corpse (WC3: body fades then clears) */
  for (const [id, g] of [...unitMeshes])
    if (g.userData.dieT > 2.4) {
      s3.world.remove(g); unitMeshes.delete(id); state.units.delete(id);
    }
  for (const e of state.workers.values()) {
    e.dir ||= 1;                                    // ping-pong, no teleport
    e.t = Math.max(0, Math.min(1, e.t + dt * 0.25 * e.dir));
    if (e.t === 1 || e.t === 0) e.dir = -e.dir;
    const k = e.t;
    e.mesh.position.set(
      (e.from?.[0] ?? 36) + ((e.to?.[0] ?? 36) - (e.from?.[0] ?? 36)) * k + 0.5,
      0.4 + Math.sin(k * Math.PI) * 0.8,
      (e.from?.[1] ?? 27) + ((e.to?.[1] ?? 27) - (e.from?.[1] ?? 27)) * k + 0.5);
    const wm = state.world?.map;          // workers vanish into shroud
    if (wm?.fog?.length) {
      const wi = Math.round(e.mesh.position.z) * wm.w +
                 Math.round(e.mesh.position.x);
      e.mesh.visible = (wm.fog[wi] ?? 0) >= 2 || !!wm.reveal?.has(wi);
    }
  }
  parts.step(dt, s3.camera);
  if (sel.reticle.visible)
    sel.reticle.userData.spin.rotation.z += dt * 1.4;   // armed reticle spin
  /* "!" POI markers: gentle bob; hidden inside unexplored shroud */
  const fmap = state.world?.map;
  for (const s of state._pois?.values() || []) {
    s.userData.t += dt;
    s.position.y = 2.1 + Math.sin(s.userData.t * 2) * 0.18;
    if (fmap?.fog?.length) {
      const i = Math.round(s.position.z) * fmap.w +
                Math.round(s.position.x);
      s.visible = (fmap.fog[i] ?? 0) >= 1 || !!fmap.reveal?.has(i);
    }
  }
  if (sel.marker.visible) {
    sel.marker.userData.t += dt;
    sel.marker.material.opacity = Math.max(0, 0.9 - sel.marker.userData.t);
    if (sel.marker.userData.t > 0.9) sel.marker.visible = false;
  }
  let bIdx = 0;
  const fm = state.world?.map;
  for (const g of bldMeshes.values()) {
    if (fm?.fog?.length) {              // unexplored tiles hide buildings
      const fx0 = Math.max(0, Math.min(fm.w - 1, Math.round(g.position.x)));
      const fz0 = Math.max(0, Math.min(fm.h - 1, Math.round(g.position.z)));
      g.visible = (fm.fog[fz0 * fm.w + fx0] ?? 0) >= 1 ||
                  !!fm.reveal?.has(fz0 * fm.w + fx0);
    }
    if (g.userData.portal) g.userData.portal.rotation.z += dt * 0.8;
    if (g.userData.scan) g.userData.scan.material.opacity =
      0.12 + Math.sin(t * 3) * 0.08;
    if (g.userData.fire) g.userData.fire.intensity =
      (g.userData.fire.intensity * 0.9) + Math.random() * 4;
    if (g.userData.flag) {                 // banner flutters with wind
      const k = t * (2.4 + windKph * 0.12) + (bIdx++) * 1.7;
      g.userData.flag.rotation.y = Math.sin(k) * 0.28;
      g.userData.flag.scale.x = 1 + Math.sin(k * 1.9) * 0.09;
    }
    /* WC3 production bar: gold fill floats over busy buildings */
    const P = g.userData.prog;
    if (P) {
      const act = state.buildings.get(g.userData.bid)?.data?.activity ?? 0;
      P.grp.visible = act > 0;
      if (P.grp.visible) {
        P.grp.rotation.y = Math.atan2(s3.camera.position.x - g.position.x,
          s3.camera.position.z - g.position.z);
        P.fill.scale.x = Math.min(1, act / 100);
        P.fill.position.x = -1.05 * (1 - P.fill.scale.x);
        /* WC3 build ticks: hammer sparks spit from busy buildings */
        if (((t * 2 + bIdx) % 1) < dt * 2 && g.visible !== false)
          parts.puff(g.position.x + (Math.random() - 0.5) * 1.6, 1.6,
                     g.position.z + (Math.random() - 0.5) * 1.6);
      }
    }
    /* WC3 contested territory: buildings on contested ground get a
       breathing red under-ring */
    const cm = state.world?.map;
    if (cm?.mark) {
      const ti = Math.round(g.position.z) * cm.w +
                 Math.round(g.position.x);
      if (cm.mark[ti] === 2 && !g.userData.cRing) {
        g.userData.cRing = new THREE.Mesh(
          new THREE.RingGeometry(1.6, 2.0, 26),
          new THREE.MeshBasicMaterial({ color: 0xd8322a,
            transparent: true, opacity: 0.3, side: THREE.DoubleSide,
            depthWrite: false }));
        g.userData.cRing.rotation.x = -Math.PI / 2;
        g.userData.cRing.position.y = 0.06;
        g.add(g.userData.cRing);
      }
      if (g.userData.cRing) {
        g.userData.cRing.visible = cm.mark[ti] === 2;
        g.userData.cRing.material.opacity =
          0.18 + Math.sin(t * 3.4) * 0.12;
      }
    }
    /* WC3 night windows: emissive mats ramp up as `day` fades */
    const nightK = Math.pow(1 - day, 2);
    for (const m of g.userData.wins || []) {
      const base = m.userData.ei ?? 0;
      m.emissiveIntensity = base > 0
        ? base * (0.55 + nightK * 1.1)
        : nightK * 1.7 + Math.sin(t * 7 + bIdx) * nightK * 0.25;
    }
  }
  hud.minimap(state.world?.map, state.world?.units,
              state.world?.buildings, cam, state.rally);
  s3.stepDecals(t);
  s3.stepClouds(dt, 0.4 + windKph * 0.05, 0.18 + windKph * 0.02);
  s3.stepCritters(dt, t);
  if (state._wflags?.length) {               // waypoint posts die on
    state._wflags = state._wflags.filter(w => {   // arrival or timeout
      w.t += dt;
      const D = unitMeshes.get(w.uid)?.userData;
      const arrived = !D || D.state !== "move" || w.t > 20;
      w.m.material.opacity = arrived ? w.m.material.opacity - dt * 3
                                     : Math.min(0.85, w.t * 2);
      if (w.m.material.opacity > 0) return true;
      s3.fx.remove(w.m); w.m.geometry.dispose(); return false;
    });
  }
  if (state._revealRings?.length) {          // reveal peel: grow+fade
    state._revealRings = state._revealRings.filter(r => {
      r.t += dt;
      r.m.scale.setScalar(1 + r.t * 4);
      r.m.material.opacity = Math.max(0, 0.5 * (1 - r.t / 1.1));
      if (r.t < 1.1) return true;
      s3.fx.remove(r.m); r.m.geometry.dispose(); return false;
    });
  }
  if (state._pools?.length) {                // corpse pools fade ~9s
    state._pools = state._pools.filter(p => {
      p.t += dt;
      p.m.material.opacity = Math.max(0, 0.6 * (1 - p.t / 9));
      if (p.t < 9) return true;
      s3.fx.remove(p.m); p.m.geometry.dispose(); return false;
    });
  }
  if (state._decBeam?.visible) {           // decision beacon breathe
    state._decBeam.rotation.y += dt * 0.7;
    state._decBeam.material.opacity = 0.1 + Math.sin(t * 2.4) * 0.05;
  }
  s3.tilt.uniforms.uFocus.value = 0.5;
  s3.tilt.uniforms.uMaxBlur.value = 3 + cam.dist.x * 0.06;
  s3.render();
}
frame();
