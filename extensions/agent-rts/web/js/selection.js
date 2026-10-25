/* selection.js - raycast pick + rubber-band box select + order issue.
   Emits intents through net.send (kind:"order" per GDD protocol). */
import * as THREE from "three";

const MAP_W = 72, MAP_H = 54;
/* square-spiral arrival slots around an order point (WC3 formation) */
const SPIRAL = (() => {
  const s = [[0, 0]];
  for (let r = 1; r <= 3; r++)
    for (let dy = -r; dy <= r; dy++)
      for (let dx = -r; dx <= r; dx++)
        if (Math.max(Math.abs(dx), Math.abs(dy)) === r) s.push([dx, dy]);
  return s;
})();

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
    /* WC3 targeting reticle: 4-point ring snapped to the hovered tile
       while an order is armed (color = order verb) */
    this.reticle = new THREE.Group();
    const rm = new THREE.MeshBasicMaterial({ color: 0x6fe39a,
      transparent: true, opacity: 0.85, side: THREE.DoubleSide,
      depthWrite: false });
    const rr = new THREE.Mesh(new THREE.RingGeometry(0.42, 0.58, 4), rm);
    this.reticle.add(rr);
    this.reticle.rotation.x = -Math.PI / 2;
    this.reticle.position.y = 0.06;
    this.reticle.visible = false;
    this.reticle.userData.spin = rr;
    opts.scene.add(this.reticle);
    /* WC3 hover pre-highlight: faint white ring under the unit the
       cursor is over (unarmed, no drag) */
    this.hoverRing = new THREE.Mesh(
      new THREE.RingGeometry(0.55, 0.7, 24),
      new THREE.MeshBasicMaterial({ color: 0xffffff, transparent: true,
        opacity: 0.35, side: THREE.DoubleSide, depthWrite: false }));
    this.hoverRing.rotation.x = -Math.PI / 2;
    this.hoverRing.position.y = 0.05;
    this.hoverRing.visible = false;
    opts.scene.add(this.hoverRing);
    this._dragStart = null;
    this.groups = new Map();               // control groups 1-9 (WC3)
    this._lastSel = 0; this._lastSelT = 0;
    this._bind(dom);
  }

  _bind(dom) {
    dom.addEventListener("pointerdown", (e) => {
      if (e.button === 0)
        this._dragStart = { x: e.clientX, y: e.clientY };
    });
    dom.addEventListener("pointermove", (e) => {
      if (this.pending) {               // armed: reticle tracks the tile
        const p = this._ground(e);
        if (p) this.reticle.position.set(
          Math.round(p.x) + 0.5, 0.06, Math.round(p.z) + 0.5);
        this.hoverRing.visible = false;
      } else if (!this._dragStart) {
        const o = this._pick(e);
        if (o?.userData.kind === "unit") {
          this.hoverRing.position.set(o.position.x, 0.05,
                                      o.position.z);
          this.hoverRing.visible = true;
        } else this.hoverRing.visible = false;
      }
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
        this._issue(this.pending, p, e.shiftKey);
        this._disarm();
        return;
      }
      if (this.sel.size) {
        /* WC3 smart order: right-click resolves context: own unit =
           guard/follow, building = move-to, ground = move */
        const o = this._pick(e);
        if (o?.userData.kind === "unit")
          this._issue({ order: "guard", target: o.userData.id }, p,
                      e.shiftKey);
        else
          this._issue("move", p, e.shiftKey);
      }
    });
    /* control groups: Ctrl+N assign, N recall, double-tap centers */
    addEventListener("keydown", (e) => {
      if (e.target.tagName === "INPUT" || e.repeat) return;
      /* WC3 Tab: cycle the active subgroup inside a multi-selection
         (Shift+Tab goes backwards); portrait/card follow the active one */
      if (e.code === "Tab") {
        const ids = [...this.sel];
        if (ids.length > 1) {
          const i = ids.indexOf(this.activeId);
          const d = e.shiftKey ? -1 : 1;
          this.activeId = ids[(i + d + ids.length) % ids.length];
          this.onsubgroup?.(this.activeId);
          e.preventDefault();
        }
        return;
      }
      /* WC3 ESC: first cancels an armed order, then drops selection */
      if (e.code === "Escape") {
        if (this.pending) this._disarm();
        else if (this.sel.size) { this.clear(); this.onchange?.(); }
        return;
      }
      const m = e.code.match(/^Digit([1-9])$/);
      if (!m) return;
      const n = +m[1];
      if (e.ctrlKey || e.metaKey) {
        if (!this.sel.size) return;
        this.groups.set(n, new Set(this.sel));
        try { localStorage.setItem("rts.grp." + n,
              JSON.stringify([...this.sel])); } catch {}
        this.ongroup?.(n, "set");
        e.preventDefault();
        return;
      }
      let g = this.groups.get(n);
      if (!g) {
        try { g = new Set(JSON.parse(
              localStorage.getItem("rts.grp." + n) || "[]")); } catch {}
        if (g?.size) this.groups.set(n, g);
      }
      if (!g || !g.size) return;
      const now = performance.now();
      const center = this._lastSel === n && now - this._lastSelT < 400;
      this.clear();
      const units = this.getUnits();
      for (const id of g) { const um = units.get(id); if (um) this.add(um); }
      this.onchange?.();
      this.onrecall?.(n, center);
      this._lastSel = n; this._lastSelT = now;
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
      if (p) { this._issue(this.pending, p); this._disarm(); }
      return;
    }
    const o = this._pick(e);
    if (!e.shiftKey) this.clear();
    /* WC3: double-click or ctrl-click selects all of the same class */
    if (o && (e.detail === 2 || (e.ctrlKey && !e.shiftKey)) &&
        o.userData.kind === "unit") {
      const cls = o.userData.info?.cls || o.userData.info?.profile;
      for (const [id, m] of this.getUnits())
        if ((m.userData.info?.cls || m.userData.info?.profile) === cls)
          this.add(m);
    } else if (o) {
      if (e.shiftKey && this.sel.has(o.userData.id || o.userData.bid)) {
        const id = o.userData.id || o.userData.bid;
        this.sel.delete(id);
        if (o.userData.ring) o.userData.ring.visible = false;
      } else this.add(o);
    }
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
    if (!this.activeId) this.activeId = id;
    if (o.userData.ring) {
      o.userData.ring.visible = true;
      o.userData._ringPop = 1;          // WC3 select: brief ring punch
    }
  }

  clear() {
    this.activeId = null;
    for (const m of this.getUnits().values())
      if (m.userData.ring) m.userData.ring.visible = false;
    for (const m of this.getBuildings().values())
      if (m.userData.ring) m.userData.ring.visible = false;
    this.sel.clear();
  }

  arm(order) {                          // next right-click issues `order`
    this.pending = order;
    const col = { attack: 0xff5040, set_rally: 0xe8c86a,
                  patrol: 0x66aaff }[order] || 0x6fe39a;
    this.reticle.userData.spin.material.color.setHex(col);
    this.reticle.visible = true;
    this.dom.style.cursor = "crosshair";
    this.onarm?.(order);
  }

  _disarm() {
    const was = this.pending;
    this.pending = null;
    this.reticle.visible = false;
    this.dom.style.cursor = "";
    if (was) this.ondisarm?.();
  }

  _issue(order, p, queued = false) {
    const x = Math.max(0, Math.min(MAP_W - 1, Math.round(p.x)));
    const y = Math.max(0, Math.min(MAP_H - 1, Math.round(p.z)));
    const extra = typeof order === "object" ? order : {};
    const name = typeof order === "object" ? order.order : order;
    const targets = this.sel.size ? [...this.sel] : ["all"];
    /* WC3 formation: a group never stacks on one tile. Each unit gets a
       square-spiral slot around the click point (unit ids only) */
    const units = this.getUnits();
    let fi = 0;
    for (const to of targets) {
      const isUnit = units.has(to);
      const off = isUnit && targets.length > 1 ? SPIRAL[fi++ % SPIRAL.length]
                                               : [0, 0];
      const tx = Math.max(0, Math.min(MAP_W - 1, x + off[0])),
            ty = Math.max(0, Math.min(MAP_H - 1, y + off[1]));
      this.net.send(Object.assign(
        { type: "order", to, order: name, x: tx, y: ty, queued }, extra));
    }
    this.marker.position.set(x + 0.5, 0.05, y + 0.5);
    this.marker.visible = true;
    this.marker.userData.t = 0;
    this.onorder?.(order, x, y, targets);
  }
}
