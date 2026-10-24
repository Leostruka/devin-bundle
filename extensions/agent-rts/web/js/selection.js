/* selection.js - raycast pick + rubber-band box select + order issue.
   Emits intents through net.send (kind:"order" per GDD protocol). */
import * as THREE from "three";

const MAP_W = 72, MAP_H = 54;

export class Selection {
  constructor(camera, dom, net, opts) {
    this.cam = camera; this.dom = dom; this.net = net;
    this.getUnits = opts.getUnits;      // () -> Map(id -> mesh)
    this.getBuildings = opts.getBuildings;
    this.groundPlane = new THREE.Plane(new THREE.Vector3(0, 1, 0), 0);
    this.ray = new THREE.Raycaster();
    this.sel = new Set();
    this.pending = null;                // armed order awaiting map click
    this.box = document.createElement("div");
    this.box.id = "selbox";
    document.body.appendChild(this.box);
    this.marker = new THREE.Mesh(
      new THREE.RingGeometry(0.4, 0.55, 20),
      new THREE.MeshBasicMaterial({ color: 0x6fe39a,
                                    side: THREE.DoubleSide,
                                    transparent: true, opacity: 0.9 }));
    this.marker.rotation.x = -Math.PI / 2;
    this.marker.visible = false;
    opts.scene.add(this.marker);
    this._dragStart = null;
    this._bind(dom);
  }

  _bind(dom) {
    dom.addEventListener("pointerdown", (e) => {
      if (e.button === 0)
        this._dragStart = { x: e.clientX, y: e.clientY };
    });
    dom.addEventListener("pointermove", (e) => {
      if (!this._dragStart) return;
      const dx = e.clientX - this._dragStart.x,
            dy = e.clientY - this._dragStart.y;
      if (Math.hypot(dx, dy) < 6 && !this.box.style.width) return;
      const x = Math.min(this._dragStart.x, e.clientX),
            y = Math.min(this._dragStart.y, e.clientY);
      Object.assign(this.box.style, {
        display: "block", left: x + "px", top: y + "px",
        width: Math.abs(dx) + "px", height: Math.abs(dy) + "px" });
    });
    dom.addEventListener("pointerup", (e) => {
      if (e.button !== 0 || !this._dragStart) return;
      const wasBox = this.box.style.display === "block";
      this.box.style.display = "none";
      const s = this._dragStart; this._dragStart = null;
      if (wasBox) return this._boxSelect(s, e, e.shiftKey);
      this._click(e);
    });
    dom.addEventListener("contextmenu", (e) => {
      if (e.shiftKey) return;           // shift+RMB = camera rotate
      const p = this._ground(e);
      if (!p) return;
      if (this.pending) {               // armed command (move/attack/...)
        this._issue(this.pending, p);
        this.pending = null;
        return;
      }
      if (this.sel.size)
        this._issue("move", p);
    });
  }

  _ground(e) {
    const m = new THREE.Vector2(e.clientX / innerWidth * 2 - 1,
                                -(e.clientY / innerHeight) * 2 + 1);
    this.ray.setFromCamera(m, this.cam);
    const p = new THREE.Vector3();
    return this.ray.ray.intersectPlane(this.groundPlane, p) ? p : null;
  }

  _pick(e) {
    const m = new THREE.Vector2(e.clientX / innerWidth * 2 - 1,
                                -(e.clientY / innerHeight) * 2 + 1);
    this.ray.setFromCamera(m, this.cam);
    const objs = [...this.getUnits().values(),
                  ...this.getBuildings().values()];
    const hits = this.ray.intersectObjects(objs, true);
    for (const h of hits) {
      let o = h.object;
      while (o && !o.userData.kind) o = o.parent;
      if (o) return o;
    }
    return null;
  }

  _click(e) {
    if (this.pending) {                 // armed order: left-click confirms
      const p = this._ground(e);
      if (p) { this._issue(this.pending, p); this.pending = null; }
      return;
    }
    const o = this._pick(e);
    if (!e.shiftKey) this.clear();
    if (o) this.add(o);
    this.onchange?.();
  }

  _boxSelect(s, e, additive) {
    if (!additive) this.clear();
    const x0 = Math.min(s.x, e.clientX), x1 = Math.max(s.x, e.clientX);
    const y0 = Math.min(s.y, e.clientY), y1 = Math.max(s.y, e.clientY);
    const v = new THREE.Vector3();
    for (const [id, m] of this.getUnits()) {
      m.getWorldPosition(v).project(this.cam);
      const sx = (v.x + 1) / 2 * innerWidth,
            sy = (1 - v.y) / 2 * innerHeight;
      if (sx >= x0 && sx <= x1 && sy >= y0 && sy <= y1) this.add(m);
    }
    this.onchange?.();
  }

  add(o) {
    const id = o.userData.id || o.userData.bid;
    this.sel.add(id);
    if (o.userData.ring) o.userData.ring.visible = true;
  }

  clear() {
    for (const m of this.getUnits().values())
      if (m.userData.ring) m.userData.ring.visible = false;
    this.sel.clear();
  }

  arm(order) {                          // next right-click issues `order`
    this.pending = order;
  }

  _issue(order, p) {
    const x = Math.max(0, Math.min(MAP_W - 1, Math.round(p.x)));
    const y = Math.max(0, Math.min(MAP_H - 1, Math.round(p.z)));
    const extra = typeof order === "object" ? order : {};
    const name = typeof order === "object" ? order.order : order;
    const targets = this.sel.size ? [...this.sel] : ["all"];
    for (const to of targets)
      this.net.send(Object.assign(
        { type: "order", to, order: name, x, y }, extra));
    this.marker.position.set(x + 0.5, 0.05, y + 0.5);
    this.marker.visible = true;
    this.marker.userData.t = 0;
    this.onorder?.(order, x, y, targets);
  }
}
