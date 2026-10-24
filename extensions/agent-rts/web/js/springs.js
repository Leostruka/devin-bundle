/* springs.js - damped spring physics (Hooke, x'' = -k(x-x0) - c*x').
   Drives camera smoothing, selection rings, panel tweens, bubble rise. */
export class Spring {
  constructor(v = 0, k = 90, c = 14) {
    this.x = v; this.v = 0; this.t = v; this.k = k; this.c = c;
  }
  set(target) { this.t = target; }
  snap(v) { this.x = this.t = v; this.v = 0; }
  step(dt) {
    const a = -this.k * (this.x - this.t) - this.c * this.v;
    this.v += a * dt;
    this.x += this.v * dt;
    return this.x;
  }
  settled(eps = 1e-3) {
    return Math.abs(this.x - this.t) < eps && Math.abs(this.v) < eps;
  }
}

export class Spring3 {
  constructor(x = 0, y = 0, z = 0, k = 90, c = 14) {
    this.x = new Spring(x, k, c); this.y = new Spring(y, k, c);
    this.z = new Spring(z, k, c);
  }
  set(x, y, z) { this.x.set(x); this.y.set(y); this.z.set(z); }
  snap(x, y, z) { this.x.snap(x); this.y.snap(y); this.z.snap(z); }
  step(dt, out) {
    out.x = this.x.step(dt); out.y = this.y.step(dt);
    out.z = this.z.step(dt); return out;
  }
}

export const damp = (cur, target, rate, dt) =>
  cur + (target - cur) * (1 - Math.exp(-rate * dt));
