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
import { Audio3 } from "./audio.js";
import { FX } from "./fx.js";
import { buildBuilding } from "./buildings.js";
import { buildUnit, updateUnit } from "./units.js";
import { Grid } from "./pathing.js";

const MAP_W = 72, MAP_H = 54;

const canvas = document.getElementById("gl");
const s3 = new Scene3D(canvas);
const cam = new RTSCamera(s3.camera, canvas);
const net = new Net();
const parts = new Particles(s3.fx);
const audio = new Audio3();
const grid = new Grid();

const state = {
  theme: "medieval",
  world: null, repo: null, decisions: [], feed: [],
  units: new Map(),        // id -> {mesh, data}
  buildings: new Map(),    // id -> {mesh, data}
  workers: new Map(),      // id -> {mesh, from, to, t}
};
const unitMeshes = new Map(), bldMeshes = new Map();

/* ---------- theme ---------- */
function applyTheme(name) {
  state.theme = name;
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

function unitHome(idx) {
  const th = state.world?.buildings?.find(b => b.id === "town-hall");
  const xy = th?.pos?.xy || [36, 27];
  const a = idx * 2.4;
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
      const h = unitHome(i);
      g.position.set(h[0], 0, h[1]);
      g.userData.home = h;
      unitMeshes.set(u.id, g);
      s3.world.add(g);
    }
    const D = g.userData;
    D.info = u;
    /* order -> waypoint path (latest order with x/y wins) */
    const ord = (u.orders || []).filter(o =>
      o.x !== undefined && o.y !== undefined &&
      o.status !== "done").slice(-1)[0];
    if (ord && (!D._lastOrd || D._lastOrd !== ord.id)) {
      D._lastOrd = ord.id;
      const p = grid.path(
        Math.round(g.position.x), Math.round(g.position.z),
        ord.x, ord.y);
      if (p && p.length > 1) { D.path = p.slice(1); D.state = "move"; }
    }
    if (D.state !== "move") D.state = mapStatus(u);
    u._pos = { x: g.position.x, y: g.position.z };
    state.units.set(u.id, { data: u });
    i++;
  }
  for (const [id, g] of [...unitMeshes]) {
    if (!seen.has(id)) { s3.world.remove(g); unitMeshes.delete(id);
                         state.units.delete(id); }
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
  theme: () => {
    const next = state.theme === "medieval" ? "office" : "medieval";
    applyTheme(next);
    net.send({ type: "set", key: "theme", value: next });
  },
  ssao: () => { if (s3.ssao) s3.ssao.enabled = !s3.ssao.enabled; },
  audio: () => { audio.enabled = !audio.enabled; },
  score: async () => {
    const r = await fetch("/score");
    if (r.ok) hud.score(await r.json());
  },
  idlePing: () => {
    const u = [...unitMeshes.values()].find(g => g.userData.state === "idle");
    if (u) cam.focus(u.position.x, u.position.z, 26);
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
  gateAnswer: (id, choice) =>
    net.send({ type: "gate_answer", id, choice }),
});

const sel = new Selection(s3.camera, canvas, net, {
  scene: s3.scene,
  getUnits: () => unitMeshes,
  getBuildings: () => bldMeshes,
});
sel.onchange = () => {
  const first = [...sel.sel][0];
  const u = state.units.get(first)?.data ||
            state.buildings.get(first)?.data;
  hud.portrait(u);
};
sel.onorder = () => audio.order();

const fx = new FX(parts, audio, hud);

net.on("open", () => hud.alert("warn", "net", "connected to the Workshop"));
net.on("snapshot", (m) => {
  state.world = m.world; state.repo = m.repo;
  state.decisions = m.decisions || [];
  if (m.prefs?.theme && m.prefs.theme !== state.theme)
    applyTheme(m.prefs.theme);
  const h = (location.hash.match(/theme=(\w+)/) || [])[1];
  if (h && h !== state.theme) applyTheme(h);
  if (m.world?.map) s3.bakeTerrain(m.world.map);
  syncBuildings(m.world?.buildings);
  syncUnits(m.world?.units);
  syncWorkers(m.world?.workers);
  hud.topbar(m.world, m.repo);
  hud.roster(m.world?.units);
  hud.bldstrip(m.world?.buildings);
  hud.tickets(m.repo?.issues);
  hud.feed(m.world?.feed);
  hud.decision(state.decisions);
  document.getElementById("minimap").onclick = (e) => {
    const r = e.target.getBoundingClientRect();
    const mx = (e.clientX - r.left) / r.width * MAP_W;
    const my = (e.clientY - r.top) / r.height * MAP_H;
    cam.focus(mx, my);
  };
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
net.on("fx", (m) => fx.handle(m));
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
  if (m.feed) { state.feed.push(m.feed); hud.feed(state.feed); }
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
    if (state.world?.map) s3.bakeTerrain(state.world.map);
  }, 800);
}

/* ---------- command card ---------- */
function command(id) {
  audio.resume();
  const armed = { move: "move", patrol: "patrol", attack: "attack",
                  rally: "set_rally" }[id];
  if (armed) { sel.arm(armed); return; }
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
    if (!hud.ticket) { hud.alert("warn", "forge",
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
function frame() {
  requestAnimationFrame(frame);
  const dt = Math.min(clock.getDelta(), 0.1);
  const t = clock.elapsedTime;
  cam.update(dt);
  for (const g of unitMeshes.values()) updateUnit(g, dt, t);
  for (const e of state.workers.values()) {
    e.t = Math.min(1, e.t + dt * 0.25);
    const k = e.t;
    e.mesh.position.set(
      (e.from?.[0] ?? 36) + ((e.to?.[0] ?? 36) - (e.from?.[0] ?? 36)) * k + 0.5,
      0.4 + Math.sin(k * Math.PI) * 0.8,
      (e.from?.[1] ?? 27) + ((e.to?.[1] ?? 27) - (e.from?.[1] ?? 27)) * k + 0.5);
    if (e.t >= 1) e.t = 0;
  }
  parts.step(dt, s3.camera);
  if (sel.marker.visible) {
    sel.marker.userData.t += dt;
    sel.marker.material.opacity = Math.max(0, 0.9 - sel.marker.userData.t);
    if (sel.marker.userData.t > 0.9) sel.marker.visible = false;
  }
  for (const g of bldMeshes.values()) {
    if (g.userData.portal) g.userData.portal.rotation.z += dt * 0.8;
    if (g.userData.scan) g.userData.scan.material.opacity =
      0.12 + Math.sin(t * 3) * 0.08;
    if (g.userData.fire) g.userData.fire.intensity =
      (g.userData.fire.intensity * 0.9) + Math.random() * 4;
  }
  hud.minimap(state.world?.map, state.world?.units,
              state.world?.buildings, cam);
  s3.tilt.uniforms.uFocus.value = 0.5;
  s3.tilt.uniforms.uMaxBlur.value = 3 + cam.dist.x * 0.06;
  s3.render();
}
frame();
