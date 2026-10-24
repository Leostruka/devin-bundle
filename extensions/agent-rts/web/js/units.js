/* units.js - articulated low-poly unit rigs + FSM animation.
   Rig: pelvis -> torso(+pauldrons) -> head -> 2 legs, 2 arms (+weapon by
   kit/tier). States: idle | move | work | attack | gate_wait | error |
   dead, driven by the world snapshot (status/orders) — see GDD 4. */
import * as THREE from "three";
import { themeOf } from "./themes.js";
import { arrive } from "./pathing.js";

const TIER_SCALE = { Footman: 0.95, Knight: 1.1, Commander: 1.28 };
const KIT_GEAR = {
  Write: "hammer", March: "boots", Cartography: "map",
  Verify: "scale", Farsight: "spyglass", Envoy: "seal",
  Parley: "horn", Camp: "tent", Track: "bow", Scouting: "spyglass",
};

function std(c, o = {}) {
  return new THREE.MeshStandardMaterial(
    Object.assign({ color: c, roughness: 0.7, metalness: 0.15 }, o));
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

  const ring = new THREE.Mesh(
    new THREE.RingGeometry(0.55, 0.7, 24),
    new THREE.MeshBasicMaterial({ color: 0x7fc9ff,
                                  side: THREE.DoubleSide }));
  ring.rotation.x = -Math.PI / 2; ring.position.y = 0.03;
  ring.visible = false;
  g.add(ring);

  g.scale.setScalar(s);
  g.userData = {
    kind: "unit", id: u.id, info: u, ring,
    rig: { pelvis, torso, head, armL, armR, legL, legR },
    phase: Math.random() * 6.28, speed: 0,
    state: "idle", path: null, target: null, home: null,
  };
  return g;
}

/* Per-frame FSM: position lerp via path, limb articulation by state. */
export function updateUnit(g, dt, t) {
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
  /* dead: sink */
  if (st === "dead") {
    g.position.y -= dt * 0.6;
    g.rotation.z = Math.min(Math.PI / 2, g.rotation.z + dt * 1.5);
  }
}
