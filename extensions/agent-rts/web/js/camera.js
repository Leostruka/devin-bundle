/* camera.js - RTS camera, rebuilt from the WC3 control basics:

   INPUT MODEL (direct, 1:1, no lag on user input):
   - Arrow keys / screen edge  -> pan the look-at target on the ground
   - Mouse wheel               -> zoom (distance), centered on screen
   - Insert / Delete           -> rotate yaw
   - Middle-mouse drag         -> rotate yaw (modern RTS extra; never RMB)
   - RMB                       -> NEVER touches the camera (smart orders)

   Springs are used ONLY for scripted jumps (focus(): F-keys, alerts,
   minimap clicks) and for impact shake. Direct user input snaps both
   spring current and target so the response is immediate. */
import * as THREE from "three";
import { Spring, Spring3 } from "./springs.js";

const MAP_W = 72, MAP_H = 54;
const DIST_MIN = 10, DIST_MAX = 110;
const EDGE_PX = 14;
const PAN_SPEED = 30;                       // world-units/s at dist=52
const ROT_SPEED = 1.9;                      // rad/s for Insert/Delete
const WHEEL_STEP = 0.12;                    // per notch: dist *= 1±step

export class RTSCamera {
  constructor(camera, dom) {
    this.cam = camera;
    this.dom = dom;
    this.target = new Spring3(36, 0, 27, 160, 22);
    this.dist = new Spring(52, 160, 22);
    this.yaw = new Spring(Math.PI * 0.75, 160, 22);
    this.pitch = 0.92;                       // ~53deg isometric feel
    this.keys = new Set();
    this._drag = null;                       // MMB rotate drag
    this._edge = { x: 0, y: 0 };
    this._v = new THREE.Vector3();
    this._shake = 0;                         // impact shake (meteor/kills)
    this._bind(dom);
  }

  _bind(dom) {
    dom.addEventListener("pointerdown", (e) => {
      if (e.button === 1) {                  // MMB drag = rotate only
        this._drag = { x: e.clientX };
        try { dom.setPointerCapture(e.pointerId); } catch {}
        e.preventDefault();                  // kill autoscroll
      }
    });
    addEventListener("pointerup", () => { this._drag = null; });
    addEventListener("pointermove", (e) => {
      this._edge.x = e.clientX < EDGE_PX ? -1 :
                     e.clientX > innerWidth - EDGE_PX ? 1 : 0;
      this._edge.y = e.clientY < EDGE_PX ? -1 :
                     e.clientY > innerHeight - EDGE_PX ? 1 : 0;
      if (this._drag) {                      // 1:1 yaw, no spring lag
        const dx = e.clientX - this._drag.x;
        this._drag.x = e.clientX;
        this.yaw.snap(this.yaw.x + dx * 0.011);
      }
    });
    dom.addEventListener("wheel", (e) => {   // WC3 zoom: centered, direct
      const f = e.deltaY > 0 ? 1 + WHEEL_STEP : 1 - WHEEL_STEP;
      this.dist.snap(Math.max(DIST_MIN,
        Math.min(DIST_MAX, this.dist.x * f)));
    }, { passive: true });
    addEventListener("keydown", (e) => {
      if (e.target.tagName === "INPUT") return;
      this.keys.add(e.code);
    });
    addEventListener("keyup", (e) => this.keys.delete(e.code));
    dom.addEventListener("contextmenu", (e) => e.preventDefault());
  }

  /* pan the look-at target in world space, rotated to camera yaw:
     forward = (-cos,-sin), screen-right = (sin,-cos) on the xz plane */
  _pan(px, py) {
    const v = PAN_SPEED * (this.dist.x / 52);
    const cy = Math.cos(this.yaw.x), sy = Math.sin(this.yaw.x);
    const dx = (px * sy + py * cy) * v,
          dz = (py * sy - px * cy) * v;
    this.target.x.snap(this.target.x.x + dx);
    this.target.z.snap(this.target.z.x + dz);
  }

  shake(a = 1) { this._shake = Math.max(this._shake, a); }

  /* scripted moves keep the spring glide (F-keys, alerts, minimap) */
  focus(x, y, dist) {
    this.target.set(x, 0, y);
    if (dist) this.dist.set(dist);
  }

  /* instant placement, no glide: page-load restore and void rescue
     must not make the user watch a slow pan from nowhere */
  jump(x, y, dist) {
    this.target.snap(x, 0, y);
    if (dist) this.dist.snap(dist);
  }

  update(dt) {
    let px = this._edge.x, py = this._edge.y;
    if (this.keys.has("ArrowUp")) py -= 1;
    if (this.keys.has("ArrowDown")) py += 1;
    if (this.keys.has("ArrowLeft")) px -= 1;
    if (this.keys.has("ArrowRight")) px += 1;
    if (px || py) this._pan(px * dt, py * dt);
    /* Insert/Delete rotate: direct snap, still readable per frame */
    if (this.keys.has("Insert")) this.yaw.snap(this.yaw.x + ROT_SPEED * dt);
    if (this.keys.has("Delete")) this.yaw.snap(this.yaw.x - ROT_SPEED * dt);
    /* clamp target to the map (+ small apron) */
    this.target.x.t = Math.max(-4, Math.min(MAP_W + 4, this.target.x.t));
    this.target.z.t = Math.max(-4, Math.min(MAP_H + 4, this.target.z.t));
    this.target.x.x = Math.max(-4, Math.min(MAP_W + 4, this.target.x.x));
    this.target.z.x = Math.max(-4, Math.min(MAP_H + 4, this.target.z.x));
    this.target.step(dt, this._v);
    const d = this.dist.step(dt), yaw = this.yaw.step(dt);
    const cp = Math.cos(this.pitch), sp = Math.sin(this.pitch);
    this.cam.position.set(this._v.x + Math.cos(yaw) * d * cp,
                          this._v.y + d * sp,
                          this._v.z + Math.sin(yaw) * d * cp);
    this.cam.lookAt(this._v.x, this._v.y, this._v.z);
    if (this._shake > 0.005) {               // decaying impact jitter
      const s = this._shake;
      this.cam.position.x += (Math.random() - 0.5) * s;
      this.cam.position.y += (Math.random() - 0.5) * s * 0.6;
      this.cam.position.z += (Math.random() - 0.5) * s;
      this._shake *= Math.exp(-6 * dt);
    }
  }
}
