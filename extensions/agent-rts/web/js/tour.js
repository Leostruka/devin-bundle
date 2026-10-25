/* tour.js - first-run guided overlay: dims the field, spotlights one HUD
   region per step with a caption card. Esc/Skip exits, T or the ? pill
   re-runs. Completion flagged in localStorage (rts.tour.v1). */

const STEPS = [
  ["#topbar", "Macro bar", "Resources (Au / Cx / Gas / Sup), war status " +
    "(dirty tree, upkeep, Age + favor) and system buttons live here."],
  ["#roster", "Hero roster", "Your agent units. Click selects, F1-F5 " +
    "focus. Edge color: green = working, red = error, grey = idle."],
  ["#tickets", "Ticket rail", "Open repo issues. Click to arm a ticket, " +
    "then Forge [D] compiles it into an optimized prompt."],
  ["#cmdcard", "Command card", "WC3 grid: QWER / ASDF / ZXCV. Move, " +
    "stop, hold, patrol, attack, dispatch, forge, guard, rally, " +
    "compact, powers, menu. WASD keys are commands, not camera."],
  ["#minimap", "Minimap", "Click to jump the camera. Fog marks unseen " +
    "lanes; gold tiles are contested/dirty."],
  ["#portrait", "Portrait", "Selected unit sheet: model, tier, task, " +
    "status, XP/level and inventory runes."],
  ["#feed", "War feed", "Live session log: orders, spawns, decisions " +
    "and hook activity emitted by the CLI."],
  ["#bottom", "Camera", "Pan: screen edges or arrow keys (1:1, no lag). " +
    "Zoom: wheel. Rotate: Insert/Delete or MMB-drag. RMB gives orders, " +
    "never rotates."],
];

export class Tour {
  constructor() {
    this.i = -1;
    const v = document.createElement("div");
    v.id = "tour-veil"; v.className = "hidden";
    v.innerHTML = `<div id="tour-spot"></div>
      <div id="tour-card"><h5></h5><p></p>
      <div class="t-nav">
        <button id="t-prev">Back</button>
        <button id="t-next">Next</button>
        <button id="t-skip">Skip</button>
        <span class="t-step"></span>
      </div></div>`;
    document.body.appendChild(v);
    this.el = v;
    this.spot = v.querySelector("#tour-spot");
    this.card = v.querySelector("#tour-card");
    v.querySelector("#t-next").onclick = () => this.next();
    v.querySelector("#t-prev").onclick = () => this.show(this.i - 1);
    v.querySelector("#t-skip").onclick = () => this.close();
    addEventListener("keydown", (e) => {
      if (this.i < 0) return;
      if (e.code === "Escape") this.close();
      else if (e.code === "ArrowRight" || e.code === "Enter") this.next();
      else if (e.code === "ArrowLeft") this.show(this.i - 1);
    });
    addEventListener("resize", () => {
      if (this.i >= 0) this.show(this.i);
    });
  }

  get active() { return this.i >= 0; }

  start() { this.show(0); }

  next() {
    if (this.i + 1 >= STEPS.length) this.close();
    else this.show(this.i + 1);
  }

  show(i) {
    this.i = Math.max(0, Math.min(STEPS.length - 1, i));
    const [sel, title, body] = STEPS[this.i];
    const t = document.querySelector(sel);
    this.el.classList.remove("hidden");
    this.card.querySelector("h5").textContent =
      `${this.i + 1}. ${title}`;
    this.card.querySelector("p").textContent = body;
    this.card.querySelector(".t-step").textContent =
      `${this.i + 1}/${STEPS.length}`;
    this.card.querySelector("#t-prev").style.visibility =
      this.i === 0 ? "hidden" : "visible";
    this.card.querySelector("#t-next").textContent =
      this.i === STEPS.length - 1 ? "Done" : "Next";
    if (!t) {                              // element absent: center card
      this.spot.style.display = "none";
      this.card.style.left = "50%"; this.card.style.top = "40%";
      this.card.style.transform = "translate(-50%,-50%)";
      return;
    }
    this.spot.style.display = "";
    const r = t.getBoundingClientRect(), pad = 6;
    this.spot.style.left = (r.left - pad) + "px";
    this.spot.style.top = (r.top - pad) + "px";
    this.spot.style.width = (r.width + pad * 2) + "px";
    this.spot.style.height = (r.height + pad * 2) + "px";
    /* card placement: prefer right of spot, else left, else below */
    const cw = 264, ch = 150, m = 12;
    let x = r.right + pad + m, y = r.top;
    if (x + cw > innerWidth) x = r.left - pad - m - cw;
    if (x < 0) { x = Math.min(r.left, innerWidth - cw - m);
                 y = r.bottom + pad + m; }
    y = Math.max(m, Math.min(innerHeight - ch - m, y));
    this.card.style.transform = "";
    this.card.style.left = x + "px";
    this.card.style.top = y + "px";
  }

  close() {
    this.i = -1;
    this.el.classList.add("hidden");
    try { localStorage.setItem("rts.tour.v1", "1"); } catch {}
  }
}
