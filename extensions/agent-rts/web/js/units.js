/* units.js - articulated low-poly unit rigs + FSM animation.
   Rig: pelvis -> torso(+pauldrons) -> head -> 2 legs, 2 arms (+weapon by
   kit/tier). States: idle | move | work | attack | gate_wait | error |
   dead, driven by the world snapshot (status/orders). See GDD 4. */
import * as THREE from "three";
import { themeOf } from "./themes.js";
import { arrive } from "./pathing.js";

const TIER_SCALE = { Footman: 0.95, Knight: 1.1, Commander: 1.28 };
/* WC3 status glyph: floating state icon over the unit head */
const GLYPHS = { work: "⚒", attack: "⚔", error: "✖", gate_wait: "⏸" };
const GLYPH_COL = { work: "#ffd54a", attack: "#ff6a4a",
                    error: "#ff5040", gate_wait: "#8fd0ff" };
const _gtex = {};
function glyphTex(st) {
  if (_gtex[st]) return _gtex[st];
  const cv = document.createElement("canvas");
  cv.width = cv.height = 48;
  const c = cv.getContext("2d");
  c.font = "bold 36px sans-serif"; c.textAlign = "center";
  c.textBaseline = "middle";
  c.shadowColor = "rgba(0,0,0,.9)"; c.shadowBlur = 4;
  c.fillStyle = GLYPH_COL[st]; c.fillText(GLYPHS[st], 24, 26);
  return _gtex[st] = new THREE.CanvasTexture(cv);
}
const KIT_GEAR = {
  Write: "hammer", March: "boots", Cartography: "map",
  Verify: "scale", Farsight: "spyglass", Envoy: "seal",
  Parley: "horn", Camp: "tent", Track: "bow", Scouting: "spyglass",
};

/* shared wind vector for cloth sim (set by main.js per frame) */
export const WIND = { x: 0.8, z: 0.3 };
export function setWind(x, z) { WIND.x = x; WIND.z = z; }

/* particle system handle (bound by main.js) for impact sparks */
let _parts = null;
export function bindParticles(p) { _parts = p; }

/* WC3 Alt-hold: shows all overhead plates while Alt is held */
let _alt = false;
export function setAlt(v) { _alt = v; }

/* fading blade-trail line behind the weapon tip (attack/work swings) */
const TRAIL_N = 7;
function buildTrail() {
  const geo = new THREE.BufferGeometry();
  geo.setAttribute("position",
    new THREE.BufferAttribute(new Float32Array(TRAIL_N * 3), 3));
  const m = new THREE.Line(geo, new THREE.LineBasicMaterial({
    color: 0xcfe0ff, transparent: true, opacity: 0 }));
  m.frustumCulled = false;
  return m;
}

function std(c, o = {}) {
  return new THREE.MeshStandardMaterial(
    Object.assign({ color: c, roughness: 0.7, metalness: 0.15 }, o));
}

/* HP/mana overhead plates (skill: battlefield overlay plates). */
function buildPlates() {
  const grp = new THREE.Group();
  const bg = new THREE.Mesh(
    new THREE.PlaneGeometry(0.94, 0.18),
    new THREE.MeshBasicMaterial({ color: 0x0a0d10, transparent: true,
                                  opacity: 0.72, depthWrite: false }));
  const hp = new THREE.Mesh(
    new THREE.PlaneGeometry(0.86, 0.055),
    new THREE.MeshBasicMaterial({ color: 0x6fe39a, depthWrite: false }));
  const mp = new THREE.Mesh(
    new THREE.PlaneGeometry(0.86, 0.045),
    new THREE.MeshBasicMaterial({ color: 0x4a9fd8, depthWrite: false }));
  hp.position.set(0, 0.035, 0.001);
  mp.position.set(0, -0.045, 0.001);
  grp.add(bg, hp, mp);
  grp.position.y = 1.95;
  grp.rotation.order = "YXZ";               // yaw first, then pitch
  grp.renderOrder = 5;
  return { grp, hp, mp };
}

/* 4-node Verlet cape ribbon (skill: spring-damper cloth + wind).
   Nodes live in WORLD space; the strip renders in unit-local space. */
const CAPE_N = 4, CAPE_SEG = 0.3, CAPE_W = 0.34;
function buildCape(color) {
  const pts = [], prev = [];
  for (let i = 0; i < CAPE_N; i++) {
    pts.push(new THREE.Vector3());
    prev.push(new THREE.Vector3());
  }
  const geo = new THREE.BufferGeometry();
  geo.setAttribute("position",
    new THREE.BufferAttribute(new Float32Array(CAPE_N * 2 * 3), 3));
  const idx = [];
  for (let i = 0; i < CAPE_N - 1; i++) {
    const a = i * 2;
    idx.push(a, a + 1, a + 2, a + 1, a + 3, a + 2);
  }
  geo.setIndex(idx);
  const mesh = new THREE.Mesh(geo, new THREE.MeshStandardMaterial({
    color, side: THREE.DoubleSide, roughness: 0.92, metalness: 0 }));
  mesh.castShadow = true;
  mesh.frustumCulled = false;
  return { mesh, pts, prev, seeded: false };
}

export function buildUnit(u, themeName) {
  const T = themeOf(themeName);
  const g = new THREE.Group();
  const s = TIER_SCALE[u.tier] || 1.0;
  const body = std(T.unitBody), trim = std(T.unitTrim, { metalness: 0.5,
                                                          roughness: 0.4 });
  const dark = std(0x2a2f38);

  const pelvis = new THREE.Group();
  pelvis.position.y = 0.62 * s;
  const torso = new THREE.Mesh(new THREE.CapsuleGeometry(0.3, 0.5, 3, 8),
                               body);
  torso.position.y = 0.5; torso.castShadow = true;
  const belt = new THREE.Mesh(new THREE.TorusGeometry(0.3, 0.05, 6, 12),
                              trim);
  belt.rotation.x = Math.PI / 2; belt.position.y = 0.18;
  const head = new THREE.Mesh(new THREE.SphereGeometry(0.22, 10, 8), body);
  head.position.y = 1.05; head.castShadow = true;
  const helm = new THREE.Mesh(new THREE.ConeGeometry(0.24, 0.3, 8), trim);
  helm.position.y = 1.24;

  const mkArm = (side) => {
    const a = new THREE.Group();
    a.position.set(0.38 * side, 0.82, 0);
    const pad = new THREE.Mesh(new THREE.SphereGeometry(0.16, 8, 6), trim);
    pad.scale.set(1.2, 0.8, 1.1);
    const limb = new THREE.Mesh(new THREE.CapsuleGeometry(0.09, 0.42, 3, 6),
                                body);
    limb.position.y = -0.3;
    a.add(pad, limb);
    return a;
  };
  const armL = mkArm(-1), armR = mkArm(1);

  const mkLeg = (side) => {
    const l = new THREE.Group();
    l.position.set(0.16 * side, 0.1, 0);
    const limb = new THREE.Mesh(new THREE.CapsuleGeometry(0.1, 0.5, 3, 6),
                                dark);
    limb.position.y = -0.35;
    l.add(limb);
    return l;
  };
  const legL = mkLeg(-1), legR = mkLeg(1);

  /* class gear on the right arm */
  const gearKind = (u.kit || []).map(k => KIT_GEAR[k])[0] || "sword";
  let gear = null;
  if (gearKind === "hammer" || u.cls === "Runesmith") {
    gear = new THREE.Group();
    const hd = new THREE.Mesh(new THREE.BoxGeometry(0.28, 0.16, 0.16),
                              std(0x555f6e, { metalness: 0.7 }));
    const st = new THREE.Mesh(new THREE.CylinderGeometry(0.03, 0.03, 0.5),
                              dark);
    st.position.y = -0.25; gear.add(hd, st);
  } else if (gearKind === "spyglass" || u.cls === "Far Seer") {
    gear = new THREE.Mesh(new THREE.CylinderGeometry(0.06, 0.08, 0.4),
                          trim);
    gear.rotation.z = Math.PI / 2;
  } else if (gearKind === "bow") {
    gear = new THREE.Mesh(new THREE.TorusGeometry(0.35, 0.03, 6, 12,
                                                  Math.PI), dark);
    gear.rotation.z = -Math.PI / 2;
  } else {
    gear = new THREE.Group();
    const bl = new THREE.Mesh(new THREE.BoxGeometry(0.06, 0.7, 0.14),
                              std(0xd8e0ea, { metalness: 0.8,
                                              roughness: 0.25 }));
    bl.position.y = -0.4;
    gear.add(bl);
  }
  gear.position.y = -0.55;
  armR.add(gear);

  pelvis.add(torso, belt, head, helm, armL, armR);
  g.add(pelvis, legL, legR);

  /* overhead hp/mana plates */
  const plates = buildPlates();
  g.add(plates.grp);

  /* cape: medieval heroes only (Knight/Commander silhouettes) */
  let cape = null;
  if (themeName === "medieval" && s >= 1.1) {
    cape = buildCape(0x8a3030);
    g.add(cape.mesh);
  }

  /* blade trail (fades in during attack/work swings) */
  const trail = buildTrail();
  g.add(trail);

  /* waypoint line: shows the queued path while moving (WC3 flag line) */
  const plGeo = new THREE.BufferGeometry();
  plGeo.setAttribute("position",
    new THREE.BufferAttribute(new Float32Array(16 * 3), 3));
  const pathLine = new THREE.Line(plGeo, new THREE.LineBasicMaterial({
    color: 0x6fe39a, transparent: true, opacity: 0.85 }));
  pathLine.frustumCulled = false;
  pathLine.visible = false;
  g.add(pathLine);

  /* hero aura rune: rotating emissive ring under Commanders (WC3) */
  let aura = null;
  if (u.tier === "Commander") {
    aura = new THREE.Mesh(
      new THREE.RingGeometry(0.78, 0.95, 28, 1, 0, Math.PI * 1.55),
      new THREE.MeshBasicMaterial({ color: T.accent, transparent: true,
                                    opacity: 0.5, side: THREE.DoubleSide,
                                    depthWrite: false }));
    aura.rotation.x = -Math.PI / 2;
    aura.position.y = 0.04;
    g.add(aura);
  }

  const ring = new THREE.Mesh(
    new THREE.RingGeometry(0.55, 0.7, 24),
    new THREE.MeshBasicMaterial({ color: 0x7fc9ff,
                                  side: THREE.DoubleSide }));
  ring.rotation.x = -Math.PI / 2; ring.position.y = 0.03;
  ring.visible = false;
  g.add(ring);

  /* overhead state glyph (⚒ work / ⚔ attack / ✖ error / ⏸ gate) */
  const glyph = new THREE.Sprite(new THREE.SpriteMaterial({
    transparent: true, depthWrite: false, opacity: 0.95 }));
  glyph.position.y = 2.45;
  glyph.scale.setScalar(0.55);
  glyph.visible = false;
  g.add(glyph);

  g.scale.setScalar(s);
  g.userData = {
    kind: "unit", id: u.id, info: u, ring, plates, cape, aura, trail,
    pathLine,
    rig: { legL, legR, pelvis, torso, armL, armR, head },
    mats: [body, trim],                        // hit-flash tint targets
    glyph,
    flash: 0, gflash: 0, dieT: 0,
    phase: Math.random() * 6.28, speed: 0,
    state: "idle", path: null, target: null, home: null,
  };
  return g;
}

/* Per-frame FSM: position lerp via path, limb articulation by state. */
export function updateUnit(g, dt, t, cam) {
  const D = g.userData, R = D.rig;
  const st = D.state;
  /* locomotion along the queued path */
  if (st === "move" && D.path && D.path.length) {
    const wp = D.path[0];
    const v = arrive(g.position, wp[0] + 0.5, wp[1] + 0.5, 4.2, 1.4, dt);
    g.position.x += v.vx * dt; g.position.z += v.vy * dt;
    D.speed = Math.hypot(v.vx, v.vy);
    if (D.speed > 0.2) {
      const want = Math.atan2(v.vx, v.vy);
      let dyaw = (want - g.rotation.y) % (Math.PI * 2);
      if (dyaw > Math.PI) dyaw -= Math.PI * 2;
      if (dyaw < -Math.PI) dyaw += Math.PI * 2;
      g.rotation.y += dyaw * Math.min(1, dt * 10);
    }
    if (v.done) D.path.shift();
    if (!D.path.length) { D.state = "idle"; }
  } else {
    D.speed = 0;
    if (st === "work" || st === "attack") { /* stay in place */ }
    else if (st === "idle" && D.home &&
             (Math.abs(g.position.x - D.home[0]) > 0.4 ||
              Math.abs(g.position.z - D.home[1]) > 0.4)) {
      const v = arrive(g.position, D.home[0], D.home[1], 1.4, 1.0, dt);
      g.position.x += v.vx * dt; g.position.z += v.vy * dt;
      D.speed = Math.hypot(v.vx, v.vy);
    }
  }
  D.phase += dt * (2.2 + D.speed * 2.4);
  /* WC3 march dust: footfalls kick soft puffs while moving.
     fog-gated: dust must not leak a unit marching under shroud */
  if (D.speed > 0.8 && _parts && g.visible !== false) {
    D._dustT = (D._dustT || 0) - dt;
    if (D._dustT <= 0) {
      D._dustT = 0.34;
      _parts.puff(g.position.x, 0.12, g.position.z);
    }
  }
  const ph = D.phase;
  const walk = Math.min(1, D.speed / 2.5);
  /* legs: stride; pelvis: bounce; torso: lean */
  R.legL.rotation.x = Math.sin(ph) * 0.7 * walk;
  R.legR.rotation.x = -Math.sin(ph) * 0.7 * walk;
  R.pelvis.position.y = 0.62 + Math.abs(Math.cos(ph)) * 0.06 * walk +
    Math.sin(t * 1.4 + ph) * 0.012;
  R.torso.rotation.x = 0.08 * walk;
  /* arms by state */
  if (st === "work" || st === "attack") {
    const sw = Math.sin(ph * 2.2);
    R.armR.rotation.x = -1.2 + sw * 0.9;
    R.armL.rotation.x = Math.sin(ph * 2.2 + 1) * 0.3;
  } else if (st === "gate_wait") {
    R.armR.rotation.x = -0.2; R.armL.rotation.x = -0.2;
    R.pelvis.position.y = 0.5;              // crouch
  } else if (st === "error") {
    g.position.x += (Math.random() - 0.5) * 0.02;
    R.armR.rotation.z = Math.sin(t * 18) * 0.2;
  } else {
    R.armL.rotation.x = Math.sin(ph) * 0.35 * walk +
      Math.sin(t * 1.1 + ph) * 0.06;
    R.armR.rotation.x = -Math.sin(ph) * 0.35 * walk -
      Math.sin(t * 1.1 + ph) * 0.06;
  }
  R.head.rotation.y = st === "idle" ? Math.sin(t * 0.5 + ph) * 0.4 : 0;
  /* WC3 tint flashes: red = damage (220ms), gold = level-up (900ms) */
  if (D._ringPop > 0) {                    // select ring punch
    D._ringPop = Math.max(0, D._ringPop - dt * 3.2);
    if (D.ring) D.ring.scale.setScalar(1 + D._ringPop * 0.55);
  }
  if (D.flash > 0) D.flash = Math.max(0, D.flash - dt);
  if (D.gflash > 0) D.gflash = Math.max(0, D.gflash - dt);
  const ef = D.flash > 0 ? [D.flash / 0.22, 0xff2410] :
             D.gflash > 0 ? [D.gflash / 0.9, 0xffcf5e] : null;
  if (ef) {
    D._flashed = true;
    for (const m of D.mats || []) {
      m.emissive.setHex(ef[1]);
      m.emissiveIntensity = ef[0] * 2.2;
    }
  } else if (D._flashed) {
    D._flashed = false;
    for (const m of D.mats || []) {
      m.emissive.setHex(0x000000);
      m.emissiveIntensity = 1;
    }
  }
  /* dead: sink + WC3 corpse dissolve (fade after a short linger) */
  if (st === "dead") {
    D.dieT = (D.dieT || 0) + dt;
    g.position.y -= dt * 0.6;
    g.rotation.z = Math.min(Math.PI / 2, g.rotation.z + dt * 1.5);
    if (D.dieT > 0.6) {
      const k = Math.max(0, 1 - (D.dieT - 0.6) / 1.4);
      g.traverse(o => {
        const m = o.material;
        if (!m || m.opacity === undefined) return;
        if (o.userData._o === undefined) o.userData._o = m.opacity;
        m.transparent = true;
        m.opacity = o.userData._o * k;
      });
    }
  }
  /* overhead plates: face camera yaw, fill by hp/mana */
  if (D.plates && cam) {
    const P = D.plates.grp;
    P.rotation.y = Math.atan2(cam.position.x - g.position.x,
                              cam.position.z - g.position.z) - g.rotation.y;
    P.rotation.x = -0.35;                 // tilt up toward the camera
    const hp = Math.max(0, Math.min(1, (D.info?.hp ?? 100) / 100));
    const mp = Math.max(0, Math.min(1, (D.info?.mana ?? 0) / 100));
    D.plates.hp.scale.x = Math.max(0.02, hp);
    D.plates.hp.position.x = -0.43 * (1 - hp);
    D.plates.hp.material.color.setHSL(hp * 0.33, 0.75, 0.45);
    D.plates.mp.scale.x = Math.max(0.02, mp);
    D.plates.mp.position.x = -0.43 * (1 - mp);
    /* WC3 plate rule: Alt held, selected, hurt or flashing -> show */
    P.visible = st !== "dead" &&
      (_alt || D.ring?.visible || hp < 0.98 || D.flash > 0 ||
       D.gflash > 0 || st === "attack" || st === "error");
  }
  /* blade trail: sample weapon tip while swinging, fade out otherwise */
  if (D.trail) {
    const working = st === "attack" || st === "work";
    const tp = D.trail.geometry.attributes.position;
    if (working) {
      R.armR.updateWorldMatrix(true, false);
      _pv.set(0, -0.95, 0);
      R.armR.localToWorld(_pv);
      g.worldToLocal(_pv);
      for (let i = TRAIL_N - 1; i > 0; i--)
        tp.setXYZ(i, tp.getX(i - 1), tp.getY(i - 1), tp.getZ(i - 1));
      tp.setXYZ(0, _pv.x, _pv.y, _pv.z);
      tp.needsUpdate = true;
      D.trail.material.opacity = Math.min(0.75,
        D.trail.material.opacity + dt * 5);
      /* impact sparks on the swing apex, ~2x per second */
      D._sparkT = (D._sparkT || 0) - dt;
      if (_parts && g.visible !== false && D._sparkT <= 0 &&
          Math.sin(ph * 2.2) > 0.92) {
        D._sparkT = 0.45;
        _parts.spark(g.position.x + Math.sin(g.rotation.y) * 1.1, 0.7,
                     g.position.z + Math.cos(g.rotation.y) * 1.1, 5);
      }
    } else if (D.trail.material.opacity > 0) {
      D.trail.material.opacity = Math.max(0,
        D.trail.material.opacity - dt * 3);
    }
  }
  /* waypoint line while moving */
  if (D.pathLine) {
    const moving = st === "move" && D.path && D.path.length;
    D.pathLine.visible = !!moving;
    if (moving) {
      const pp = D.pathLine.geometry.attributes.position;
      /* pathLine is a child of g: counter-rotate so the world-space
         polyline does not spin with the unit's facing */
      D.pathLine.rotation.y = -g.rotation.y;
      pp.setXYZ(0, 0, 0.18, 0);
      const n = Math.min(15, D.path.length);
      for (let i = 0; i < n; i++)
        pp.setXYZ(i + 1, D.path[i][0] + 0.5 - g.position.x, 0.15,
                  D.path[i][1] + 0.5 - g.position.z);
      D.pathLine.geometry.setDrawRange(0, n + 1);
      pp.needsUpdate = true;
    }
  }
  /* status glyph over the head for actionable states */
  if (D.glyph) {
    const on = GLYPHS[st];
    D.glyph.visible = !!on && st !== "dead";
    if (on) D.glyph.material.map = glyphTex(st);
  }
  /* own troops never vanish under fog (WC3): they are the army, not
     intel. Server vision re-lights tiles around them; hiding them just
     telegraphs a render-sync gap as "troops disappear". */
  g.visible = true;
  /* hero aura: slow rune rotation + breathing glow */
  if (D.aura) {
    D.aura.rotation.z += dt * 1.1;
    D.aura.material.opacity = 0.38 + Math.sin(t * 2.4 + ph) * 0.14;
  }
  /* cape verlet: world-space nodes, local-space strip */
  if (D.cape) stepCape(D.cape, g, R.pelvis, dt, t);
}

const _pv = new THREE.Vector3(), _lv = new THREE.Vector3();
function stepCape(cape, g, pelvis, dt, t) {
  const { pts, prev } = cape;
  g.updateWorldMatrix(true, false);
  pelvis.updateWorldMatrix(true, false);
  pelvis.localToWorld(_pv.set(0, 0.55, -0.3));      // pin: upper back
  if (!cape.seeded) {
    for (let i = 0; i < CAPE_N; i++) {
      pts[i].set(_pv.x, _pv.y - i * CAPE_SEG, _pv.z);
      prev[i].copy(pts[i]);
    }
    cape.seeded = true;
  }
  pts[0].copy(_pv);
  const d2 = dt * dt;
  for (let i = 1; i < CAPE_N; i++) {
    const p = pts[i], pr = prev[i];
    const vx = (p.x - pr.x) * 0.94, vy = (p.y - pr.y) * 0.94,
          vz = (p.z - pr.z) * 0.94;
    pr.copy(p);
    p.x += vx + (WIND.x * 3 + Math.sin(t * 1.7 + i * 1.3) * 0.4) * d2 * 60;
    p.y += vy - 9.8 * d2;
    p.z += vz + (WIND.z * 3 + Math.cos(t * 1.3 + i) * 0.4) * d2 * 60;
    if (p.y < 0.06) p.y = 0.06;                     // floor
  }
  for (let k = 0; k < 3; k++)                       // distance constraints
    for (let i = 0; i < CAPE_N - 1; i++) {
      const a = pts[i], b = pts[i + 1];
      const dx = b.x - a.x, dy = b.y - a.y, dz = b.z - a.z;
      const d = Math.hypot(dx, dy, dz) || 1e-6;
      const f = (d - CAPE_SEG) / d;
      if (i === 0) { b.x -= dx * f; b.y -= dy * f; b.z -= dz * f; }
      else {
        a.x += dx * f * 0.5; a.y += dy * f * 0.5; a.z += dz * f * 0.5;
        b.x -= dx * f * 0.5; b.y -= dy * f * 0.5; b.z -= dz * f * 0.5;
      }
    }
  const pos = cape.mesh.geometry.attributes.position;
  for (let i = 0; i < CAPE_N; i++) {
    _lv.copy(pts[i]); g.worldToLocal(_lv);
    pos.setXYZ(i * 2, _lv.x - CAPE_W / 2, _lv.y, _lv.z);
    pos.setXYZ(i * 2 + 1, _lv.x + CAPE_W / 2, _lv.y, _lv.z);
  }
  pos.needsUpdate = true;
  cape.mesh.geometry.computeVertexNormals();
}
