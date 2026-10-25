/* particles.js - instanced particle pool: Tycoon progress bubbles,
   forge sparks, meteor, confetti, smoke. Zero per-frame allocation:
   fixed pools recycled by index. */
import * as THREE from "three";

const COLORS = { blue: 0x66aaff, green: 0x6fe39a, purple: 0xbf8bff,
                 red: 0xff7a7a, gold: 0xffd54a, white: 0xf4f8ff };

/* soft radial sprite for volumetric puffs: hard-edged quads read as
   white squares at range */
let _softTex = null;
function softTex() {
  if (_softTex) return _softTex;
  const cv = document.createElement("canvas");
  cv.width = cv.height = 64;
  const c = cv.getContext("2d");
  const g = c.createRadialGradient(32, 32, 4, 32, 32, 30);
  g.addColorStop(0, "rgba(255,255,255,.95)");
  g.addColorStop(0.55, "rgba(255,255,255,.55)");
  g.addColorStop(1, "rgba(255,255,255,0)");
  c.fillStyle = g; c.fillRect(0, 0, 64, 64);
  _softTex = new THREE.CanvasTexture(cv);
  return _softTex;
}

class Pool {
  constructor(scene, n, size, color, opts = {}) {
    this.n = n; this.items = [];
    const geo = new THREE.PlaneGeometry(size, size);
    for (let i = 0; i < n; i++) {
      const m = new THREE.Mesh(geo, new THREE.MeshBasicMaterial({
        color, transparent: true, opacity: 0, depthWrite: false,
        side: THREE.DoubleSide,
        map: opts.soft ? softTex() : null }));
      m.visible = false;
      m.userData = { t: 0, life: 0, vx: 0, vy: 0, vz: 0, wob: Math.random() * 9 };
      scene.add(m);
      this.items.push(m);
    }
    this.i = 0;
  }
  emit(x, y, z, vy, life, spread = 0.4) {
    const p = this.items[this.i++ % this.n];
    p.visible = true;
    p.position.set(x + (Math.random() - 0.5) * spread, y,
                   z + (Math.random() - 0.5) * spread);
    p.userData.t = 0; p.userData.life = life;
    p.userData.vy = vy;
    p.userData.vx = (Math.random() - 0.5) * 0.4;
    p.userData.vz = (Math.random() - 0.5) * 0.4;
    p.material.opacity = 0.95;
    return p;
  }
  step(dt, cam) {
    for (const p of this.items) {
      if (!p.visible) continue;
      const u = p.userData;
      u.t += dt;
      if (u.t > u.life) { p.visible = false; p.material.opacity = 0;
                          continue; }
      p.position.y += u.vy * dt;
      p.position.x += u.vx * dt + Math.sin(u.t * 5 + u.wob) * 0.15 * dt;
      p.position.z += u.vz * dt;
      p.material.opacity = 0.95 * (1 - (u.t / u.life) ** 1.6);
      p.quaternion.copy(cam.quaternion);      // billboard
    }
  }
}

export class Particles {
  constructor(scene) {
    this.scene = scene;
    this.pools = {};
    for (const [k, c] of Object.entries(COLORS))
      this.pools[k] = new Pool(scene, 90, 0.42, c);
    this.sparks = new Pool(scene, 160, 0.16, 0xffb347);
    this.smoke = new Pool(scene, 60, 0.9, 0x8a929c, { soft: true });
    this.meteors = [];
    /* bound by main.js: () => world.map — meteor trail must not
       scribble smoke over tiles still under unexplored shroud */
    this.fogFn = null;
  }
  _seen(x, z) {
    const m = this.fogFn?.();
    if (!m?.fog?.length) return true;
    const i = Math.max(0, Math.min(m.h - 1, Math.round(z))) * m.w +
              Math.max(0, Math.min(m.w - 1, Math.round(x)));
    return (m.fog[i] ?? 0) >= 1 || !!m.reveal?.has(i);
  }
  bubble(x, y, color = "green", label) {
    (this.pools[color] || this.pools.green).emit(x, 2.6, y, 1.15, 2.1);
  }
  spark(x, y, z, n = 6) {
    for (let i = 0; i < n; i++)
      this.sparks.emit(x + (Math.random() - 0.5) * 0.6,
                       y, z, 1.5 + Math.random() * 2, 0.7, 0.3);
  }
  /* callers pass (x, heightY, z); emit honors real world pos —
     a (x, zAsY, ignored) bug once dumped every puff onto the
     map's north edge */
  puff(x, y = 2.4, z = 0) {
    this.smoke.emit(x, y, z, 0.55, 3.2, 1.0);
  }
  meteor(x, y) {
    const m = new THREE.Mesh(
      new THREE.SphereGeometry(0.85, 14, 10),
      new THREE.MeshStandardMaterial({
        color: 0xff8844, emissive: 0xff4400, emissiveIntensity: 2.4,
        roughness: 0.4 }));
    m.position.set(x - 16, 30, y - 16);
    m.userData = { t: 0, tx: x, ty: y, trail: 0 };
    const light = new THREE.PointLight(0xff6622, 40, 24);
    m.add(light);
    this.scene.add(m);
    this.meteors.push(m);
  }
  confetti(x, y) {
    for (let i = 0; i < 24; i++)
      this.pools[["blue", "green", "purple", "gold"][i % 4]]
        .emit(x, 3 + Math.random() * 2, y, 0.6, 1.6, 1.6);
  }
  step(dt, cam) {
    for (const p of Object.values(this.pools)) p.step(dt, cam);
    this.sparks.step(dt, cam);
    this.smoke.step(dt, cam);
    for (let i = this.meteors.length - 1; i >= 0; i--) {
      const m = this.meteors[i], u = m.userData;
      u.t += dt;
      const k = Math.min(1, u.t / 1.1);
      m.position.x += (u.tx - m.position.x) * Math.min(1, k * 0.16 + 0.02);
      m.position.z += (u.ty - m.position.z) * Math.min(1, k * 0.16 + 0.02);
      m.position.y -= (30 * k * k) * dt * 2.6;
      u.trail += dt;
      /* trail only over the map itself: a meteor spawned at
         (x-16, 30, z-16) otherwise drags a serrated smoke band
         across the void beyond the north edge */
      const inMap = m.position.x >= -1 && m.position.x <= 73 &&
                    m.position.z >= -1 && m.position.z <= 55;
      if (u.trail > 0.02 && inMap &&
          this._seen(m.position.x, m.position.z)) {
        u.trail = 0;
        this.smoke.emit(m.position.x, m.position.y, m.position.z,
                        0.2, 1.2, 0.5);
      }
      if (m.position.y <= 0.7) {              // impact
        this.spark(u.tx, 0.6, u.ty, 26);
        for (let j = 0; j < 8; j++) this.pools.red.emit(u.tx, 1, u.ty,
                                                        1.4, 1.4, 2.2);
        this.scene.remove(m);
        this.meteors.splice(i, 1);
      }
    }
  }
}
