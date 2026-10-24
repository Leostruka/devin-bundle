/* camera.js - RTS orbital controller: edge/arrows/MMB pan, zoom-to-cursor,
   RMB-drag rotate, spring-smoothed, map-clamped. WASD/QE are reserved for
   the HUD command card (hotkey conflict fix). */
import * as THREE from "three";
import { Spring, Spring3 } from "./springs.js";

const MAP_W = 72, MAP_H = 54;

export class RTSCamera {
  constructor(camera, dom) {
    this.cam = camera;
    this.dom = dom;
    this.target = new Spring3(36, 0, 27, 120, 16);
    this.dist = new Spring(52, 120, 16);
    this.yaw = new Spring(Math.PI * 0.75, 140, 18);
    this.pitch = 0.92;                       // ~53deg isometric feel
    this.keys = new Set();
    this._drag = null;
    this._edge = { x: 0, y: 0 };
    this._v = new THREE.Vector3();
    this._ray = new THREE.Raycaster();
    this._plane = new THREE.Plane(new THREE.Vector3(0, 1, 0), 0);
    this._bind(dom);
  }

  _bind(dom) {
    dom.addEventListener("pointerdown", (e) => {
      if (e.button === 1 || (e.button === 2 && !e.shiftKey)) {
        this._drag = { x: e.clientX, y: e.clientY, b: e.button };
        dom.setPointerCapture(e.pointerId);
      }
    });
    addEventListener("pointerup", () => { this._drag = null; });
    addEventListener("pointermove", (e) => {
      this._edge.x = e.clientX < 14 ? -1 : e.clientX > innerWidth - 14 ? 1 : 0;
      this._edge.y = e.clientY < 14 ? -1 : e.clientY > innerHeight - 14 ? 1 : 0;
      if (!this._drag) return;
      const dx = e.clientX - this._drag.x, dy = e.clientY - this._drag.y;
      this._drag.x = e.clientX; this._drag.y = e.clientY;
      if (this._drag.b === 2) {              // RMB drag = rotate
        this.yaw.set(this.yaw.t + dx * 0.008);
      } else {                               // MMB drag = pan
        this._pan(-dx, -dy);
      }
    });
    dom.addEventListener("wheel", (e) => {
      const before = this._groundAt(e.clientX, e.clientY);
      this.dist.set(Math.max(10, Math.min(110,
        this.dist.t * (1 + e.deltaY * 0.0011))));
      const after = this._groundAt(e.clientX, e.clientY);
      if (before && after) {                 // zoom-to-cursor
        this.target.x.t += before.x - after.x;
        this.target.z.t += before.z - after.z;
      }
    }, { passive: true });
    addEventListener("keydown", (e) => {
      if (e.target.tagName === "INPUT") return;
      this.keys.add(e.code);
    });
    addEventListener("keyup", (e) => this.keys.delete(e.code));
    dom.addEventListener("contextmenu", (e) => e.preventDefault());
  }

  _groundAt(sx, sy) {
    const m = new THREE.Vector2(sx / innerWidth * 2 - 1,
                                -(sy / innerHeight) * 2 + 1);
    this._ray.setFromCamera(m, this.cam);
    const p = new THREE.Vector3();
    return this._ray.ray.intersectPlane(this._plane, p) ? p : null;
  }

  _pan(dx, dy) {
    const k = this.dist.t / innerHeight * 1.7;
    const cy = Math.cos(this.yaw.t), sy = Math.sin(this.yaw.t);
    this.target.x.t += dx * k * sy - dy * k * cy;
    this.target.z.t += dx * k * cy + dy * k * sy;
  }

  focus(x, y, dist) {
    this.target.set(x, 0, y);
    if (dist) this.dist.set(dist);
  }

  update(dt) {
    /* arrows + edge pan (WASD belongs to the command card) */
    let px = this._edge.x, py = this._edge.y;
    if (this.keys.has("ArrowUp")) py -= 1;
    if (this.keys.has("ArrowDown")) py += 1;
    if (this.keys.has("ArrowLeft")) px -= 1;
    if (this.keys.has("ArrowRight")) px += 1;
    if (px || py) {
      const v = 26 * dt * (this.dist.t / 52);
      const cy = Math.cos(this.yaw.t), sy = Math.sin(this.yaw.t);
      this.target.x.t += (px * v) * sy - (py * v) * cy;
      this.target.z.t += (px * v) * cy + (py * v) * sy;
    }
    this.target.x.t = Math.max(-4, Math.min(MAP_W + 4, this.target.x.t));
    this.target.z.t = Math.max(-4, Math.min(MAP_H + 4, this.target.z.t));
    this.target.step(dt, this._v);
    const d = this.dist.step(dt), yaw = this.yaw.step(dt);
    const cp = Math.cos(this.pitch), sp = Math.sin(this.pitch);
    this.cam.position.set(this._v.x + Math.cos(yaw) * d * cp,
                          this._v.y + d * sp,
                          this._v.z + Math.sin(yaw) * d * cp);
    this.cam.lookAt(this._v.x, this._v.y, this._v.z);
  }
}
