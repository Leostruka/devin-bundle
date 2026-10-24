/* buildings.js - procedural PBR building factories per theme.
   Medieval: stone keeps, forges with shader fire, towers, tents.
   Office: desks+dual monitors, server racks, kanban boards, coffee. */
import * as THREE from "three";
import { themeOf } from "./themes.js";

const M = {
  box: (w, h, d, m) => new THREE.Mesh(new THREE.BoxGeometry(w, h, d), m),
  cyl: (r0, r1, h, m, s = 10) =>
    new THREE.Mesh(new THREE.CylinderGeometry(r0, r1, h, s), m),
  cone: (r, h, m, s = 4) => new THREE.Mesh(new THREE.ConeGeometry(r, h, s), m),
};

function std(color, opts = {}) {
  return new THREE.MeshStandardMaterial(
    Object.assign({ color, roughness: 0.85, metalness: 0.05 }, opts));
}

function shade(g) {
  g.traverse(o => { if (o.isMesh) { o.castShadow = true;
                                    o.receiveShadow = true; } });
  return g;
}

/* ---------- medieval builders ---------- */
function medievalBuilding(id, T) {
  const B = T.building;
  const wall = std(B.wall), stone = std(B.stone), trim = std(B.trim);
  const roof = std(B.roof, { roughness: 0.95 });
  const g = new THREE.Group();
  const base = M.box(2.6, 2.2, 2.6, stone);
  base.position.y = 1.1;
  g.add(base);
  const rf = M.cone(2.15, 1.5, roof, 4);
  rf.position.y = 2.9; rf.rotation.y = Math.PI / 4;
  g.add(rf);
  if (id === "town-hall") {                 // keep: taller + turret
    base.scale.set(1.25, 1.5, 1.25);
    base.position.y = 1.65;
    const tur = M.cyl(0.5, 0.6, 2.8, stone);
    tur.position.set(1.5, 1.4, 1.5);
    const trf = M.cone(0.75, 0.9, roof);
    trf.position.set(1.5, 3.2, 1.5);
    g.add(tur, trf);
  } else if (id === "watchtower") {
    g.clear();
    const tw = M.cyl(0.9, 1.15, 4.4, stone);
    tw.position.y = 2.2;
    const top = M.cyl(1.35, 1.1, 0.8, trim);
    top.position.y = 4.6;
    const tr = M.cone(1.5, 1.1, roof);
    tr.position.y = 5.5;
    g.add(tw, top, tr);
  } else if (id === "runeforge") {
    const chim = M.cyl(0.3, 0.4, 1.6, trim);
    chim.position.set(0.9, 3.4, 0.9);
    const anvil = M.box(0.9, 0.5, 0.5, std(0x3a3f46, { metalness: 0.7 }));
    anvil.position.set(-0.9, 0.25, 1.4);
    const fire = new THREE.PointLight(0xff7722, 26, 12);
    fire.position.set(0, 1.6, 1.3);
    g.add(chim, anvil, fire);
    g.userData.fire = fire;
  } else if (id === "barracks") {
    const tent = M.cone(1.7, 1.6, std(0x7a4a3a), 6);
    tent.position.set(1.8, 0.8, 0.6);
    g.add(tent);
  } else if (id === "portal") {
    const ring = new THREE.Mesh(
      new THREE.TorusGeometry(1.0, 0.16, 8, 24),
      std(0x6a4ad8, { emissive: 0x5a2bd8, emissiveIntensity: 0.9 }));
    ring.position.set(0, 1.5, 1.35);
    g.add(ring);
    g.userData.portal = ring;
  } else if (id === "altar") {
    const beam = new THREE.Mesh(
      new THREE.CylinderGeometry(0.35, 0.55, 3.4, 10, 1, true),
      new THREE.MeshBasicMaterial({ color: 0xffe9a8, transparent: true,
                                    opacity: 0.28, side: THREE.DoubleSide,
                                    depthWrite: false }));
    beam.position.y = 3.4;
    g.add(beam);
  } else if (id === "tavern" || id === "marketplace") {
    const awn = M.box(3.0, 0.12, 1.4, std(0xa33c31));
    awn.position.set(0, 2.2, 1.5); awn.rotation.x = 0.25;
    g.add(awn);
  } else if (id === "trophy-hall") {
    const cup = M.cyl(0.34, 0.22, 0.7, std(0xd4af37, { metalness: 0.9,
                                                       roughness: 0.3 }));
    cup.position.set(0, 3.9, 0);
    g.add(cup);
  }
  const banner = M.box(0.06, 1.7, 0.06, trim);
  banner.position.set(-1.5, 0.85, 1.5);
  const flag = M.box(0.7, 0.4, 0.02, std(0xa33c31, { side: THREE.DoubleSide }));
  flag.position.set(-1.15, 1.45, 1.5);
  g.add(banner, flag);
  return shade(g);
}

/* ---------- office builders ---------- */
function officeBuilding(id, T) {
  const B = T.building;
  const g = new THREE.Group();
  const desk = M.box(2.8, 0.16, 1.5, std(B.wall));
  desk.position.y = 0.95;
  const leg1 = M.box(0.14, 0.95, 1.4, std(B.trim));
  leg1.position.set(-1.3, 0.47, 0);
  const leg2 = leg1.clone(); leg2.position.x = 1.3;
  g.add(desk, leg1, leg2);
  const mon = (x) => {
    const scr = M.box(0.9, 0.62, 0.06, std(0x18222e, {
      emissive: 0x2b5a86, emissiveIntensity: 0.8 }));
    scr.position.set(x, 1.45, -0.3);
    const arm = M.box(0.08, 0.5, 0.08, std(B.trim));
    arm.position.set(x, 1.15, -0.3);
    g.add(scr, arm);
  };
  if (id === "town-hall") {                 // server rack row
    g.clear();
    for (let i = 0; i < 3; i++) {
      const rack = M.box(0.9, 2.3, 0.8, std(0x2a3542, { metalness: 0.4 }));
      rack.position.set(i * 1.05 - 1.05, 1.15, 0);
      const leds = M.box(0.7, 1.9, 0.02, std(0x101820, {
        emissive: 0x33ff88, emissiveIntensity: 1.2 }));
      leds.position.set(i * 1.05 - 1.05, 1.15, 0.41);
      g.add(rack, leds);
    }
  } else if (id === "watchtower") {         // firewall gate arch
    g.clear();
    const l = M.box(0.35, 3.2, 0.6, std(B.trim));
    l.position.set(-1.1, 1.6, 0);
    const r = l.clone(); r.position.x = 1.1;
    const top = M.box(2.6, 0.4, 0.6, std(B.trim));
    top.position.y = 3.2;
    const scan = M.box(2.0, 2.8, 0.03, new THREE.MeshBasicMaterial({
      color: 0x4ad8ff, transparent: true, opacity: 0.18,
      side: THREE.DoubleSide }));
    scan.position.y = 1.6;
    g.add(l, r, top, scan);
    g.userData.scan = scan;
  } else if (id === "runeforge") {          // planning desk + kanban
    const board = M.box(1.9, 1.3, 0.08, std(0xf4f0e4));
    board.position.set(1.0, 1.9, -0.6);
    g.add(board);
    for (let i = 0; i < 6; i++) {
      const card = M.box(0.4, 0.26, 0.02, std(
        [0xffd54a, 0x6fe39a, 0x66aaff][i % 3]));
      card.position.set(0.35 + (i % 3) * 0.6, 2.15 - Math.floor(i / 3) * 0.5,
                        -0.55);
      g.add(card);
    }
    mon(-0.6);
  } else if (id === "barracks") {           // spawn pod
    const pod = M.cyl(0.7, 0.85, 2.0, std(0x3c4c5e));
    pod.position.set(1.6, 1.0, 0.4);
    const lid = new THREE.Mesh(new THREE.SphereGeometry(0.7, 12, 8, 0,
      Math.PI * 2, 0, Math.PI / 2), std(0x4a9fd8, { metalness: 0.5 }));
    lid.position.set(1.6, 2.0, 0.4);
    g.add(pod, lid);
  } else if (id === "tavern" || id === "marketplace") {
    const counter = M.box(2.6, 1.0, 0.8, std(B.trim));
    counter.position.set(0, 0.5, 1.2);
    const coffee = M.box(0.4, 0.55, 0.35, std(0x333));
    coffee.position.set(0.8, 1.3, 1.2);
    g.add(counter, coffee);
  } else if (id === "altar") {              // test shrine: CI pedestal
    const ped = M.box(1.2, 0.9, 1.2, std(B.stone));
    ped.position.y = 0.45;
    const orb = new THREE.Mesh(new THREE.SphereGeometry(0.5, 14, 10),
      std(0x4ad8a0, { emissive: 0x2bd88a, emissiveIntensity: 0.9 }));
    orb.position.y = 1.5;
    g.add(ped, orb);
  } else if (id === "portal") {
    const ring = new THREE.Mesh(
      new THREE.TorusGeometry(1.0, 0.14, 8, 24),
      std(0x4a9fd8, { emissive: 0x2b8ad8, emissiveIntensity: 0.9 }));
    ring.position.set(0, 1.5, 1.2);
    g.add(ring);
    g.userData.portal = ring;
  } else {
    mon(-0.55); mon(0.55);
    const chair = M.cyl(0.4, 0.45, 0.5, std(B.trim));
    chair.position.set(0, 0.25, 1.2);
    g.add(chair);
  }
  return shade(g);
}

export function buildBuilding(id, themeName) {
  const T = themeOf(themeName);
  const g = T.id === "office"
    ? officeBuilding(id, T) : medievalBuilding(id, T);
  g.userData.bid = id;
  g.userData.kind = "building";
  return g;
}
