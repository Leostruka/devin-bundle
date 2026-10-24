/* pathing.js - A* over the tile grid + arrival steering.
   Blocking set = building footprints (2x2 around each site) + shroud
   edge. Client-side only; the server owns truth, this just routes the
   animation between order tiles. */
const MAP_W = 72, MAP_H = 54;

export class Grid {
  constructor() { this.blocked = new Set(); }
  block(x, y, r = 1) {
    for (let dy = -r; dy <= r; dy++)
      for (let dx = -r; dx <= r; dx++) {
        const nx = x + dx, ny = y + dy;
        if (nx >= 0 && ny >= 0 && nx < MAP_W && ny < MAP_H)
          this.blocked.add(ny * MAP_W + nx);
      }
  }
  free(x, y) {
    return x >= 0 && y >= 0 && x < MAP_W && y < MAP_H &&
      !this.blocked.has(y * MAP_W + x);
  }
  /* A* with octile heuristic, 8-connected, corner-cut guard */
  path(sx, sy, tx, ty) {
    const key = (x, y) => y * MAP_W + x;
    if (!this.free(tx, ty)) {                 // nearest free fallback
      let best = null, bd = 1e9;
      for (let dy = -3; dy <= 3; dy++)
        for (let dx = -3; dx <= 3; dx++) {
          const nx = tx + dx, ny = ty + dy;
          if (this.free(nx, ny)) {
            const d = dx * dx + dy * dy;
            if (d < bd) { bd = d; best = [nx, ny]; }
          }
        }
      if (best) { tx = best[0]; ty = best[1]; } else return null;
    }
    const open = [[0, sx, sy]], g = new Map([[key(sx, sy), 0]]);
    const from = new Map(), seen = new Set();
    const H = (x, y) => {
      const dx = Math.abs(x - tx), dy = Math.abs(y - ty);
      return Math.max(dx, dy) + 0.41 * Math.min(dx, dy);
    };
    while (open.length) {
      let bi = 0;
      for (let i = 1; i < open.length; i++)
        if (open[i][0] < open[bi][0]) bi = i;
      const [, cx, cy] = open.splice(bi, 1)[0];
      const ck = key(cx, cy);
      if (seen.has(ck)) continue;
      seen.add(ck);
      if (cx === tx && cy === ty) {
        const out = [];
        let k = ck;
        while (k !== undefined) {
          out.unshift([k % MAP_W, Math.floor(k / MAP_W)]);
          k = from.get(k);
        }
        return out;
      }
      for (let dy = -1; dy <= 1; dy++)
        for (let dx = -1; dx <= 1; dx++) {
          if (!dx && !dy) continue;
          const nx = cx + dx, ny = cy + dy;
          if (!this.free(nx, ny)) continue;
          if (dx && dy &&                 // no corner cutting
              (!this.free(cx + dx, cy) || !this.free(cx, cy + dy)))
            continue;
          const nk = key(nx, ny), ng = g.get(ck) + Math.hypot(dx, dy);
          if (ng < (g.get(nk) ?? 1e9)) {
            g.set(nk, ng); from.set(nk, ck);
            open.push([ng + H(nx, ny), nx, ny]);
          }
        }
    }
    return null;
  }
}

/* Arrival steering: seek target, slow inside radius, return vel.
   pos is a THREE.Vector3 on the ground plane (x=east, z=south). */
export function arrive(pos, tx, ty, maxSpeed, slowR = 1.6, dt = 0.016) {
  const dx = tx - pos.x, dy = ty - pos.z;
  const d = Math.hypot(dx, dy);
  if (d < 0.05) return { vx: 0, vy: 0, done: true };
  const sp = Math.min(maxSpeed, maxSpeed * (d / slowR));
  return { vx: dx / d * sp, vy: dy / d * sp, done: false };
}
