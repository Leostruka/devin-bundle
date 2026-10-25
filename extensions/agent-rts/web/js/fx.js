/* fx.js - server fx/alert/decision frames -> scene + HUD effects. */
import * as THREE from "three";

export class FX {
  constructor(particles, audio, hud, camera) {
    this.p = particles; this.audio = audio; this.hud = hud;
    this.cam = camera;
    this._v = new THREE.Vector3();
    /* fog accessor, bound by main.js; world-space fx must not
       leak events happening under unexplored shroud */
    this.fogFn = null;
  }
  _seen(x, y) {
    const m = this.fogFn?.();
    if (!m?.fog?.length) return true;
    const i = Math.max(0, Math.min(m.h - 1, Math.round(y))) * m.w +
              Math.max(0, Math.min(m.w - 1, Math.round(x)));
    return (m.fog[i] ?? 0) >= 1 || !!m.reveal?.has(i);
  }
  /* WC3 floating text: world pos -> screen div, rises & fades */
  floatText(x, y, label, color) {
    if (!label || !this.cam) return;
    this._v.set(x + 0.5, 2.9, y + 0.5).project(this.cam);
    if (this._v.z > 1) return;               // behind camera
    const d = document.createElement("div");
    d.className = "floater f-" + (color || "green");
    d.textContent = label;
    d.style.left = (this._v.x + 1) / 2 * innerWidth + "px";
    d.style.top = (1 - this._v.y) / 2 * innerHeight + "px";
    document.getElementById("hud").appendChild(d);
    setTimeout(() => d.remove(), 1300);
  }
  handle(m) {
    if (m.x !== undefined && m.y !== undefined && !this._seen(m.x, m.y))
      return;
    if (m.fx === "bubble") {
      this.p.bubble(m.x, m.y, m.color, m.label);
      this.floatText(m.x, m.y, m.label, m.color);
      if (m.tool) this.audio?.toolFx(m.bid, m.tool);
      else this.audio?.blip(m.color);
    } else if (m.fx === "meteor") {
      this.p.meteor(m.x, m.y);
      this.audio?.meteor();
    } else if (m.fx === "gate_flash") {
      this.p.spark(m.x, 2.4, m.y, 14);
      this.audio?.alert();
    } else if (m.fx === "confetti") {
      this.p.confetti(m.x, m.y);
    } else if (m.fx === "smoke") {
      this.p.puff(m.x, 2.4, m.y);
    }
  }
  alert(m) {
    this.hud?.alert(m.level, m.code, m.msg, m.x, m.y);
    if (m.level === "crit") this.audio?.alert();
  }
}
