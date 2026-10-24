/* hud.js - three-layer RTS HUD: macro bar, battlefield overlays,
   bottom console (minimap | portrait/stats | 4x3 command card),
   Cafe-Mania ticket rail, decision modal, alert stack, F10 menu. */
const esc = (s) => String(s ?? "").replace(/[&<>"]/g,
  c => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }[c]));

const SLOTS = [
  ["Q", "move",    "Move",    "»", "Order selected units to march"],
  ["W", "stop",    "Stop",    "[]", "Halt all orders"],
  ["E", "hold",    "Hold",    "H", "Hold position"],
  ["R", "patrol",  "Patrol",  "~", "Patrol to point (click map)"],
  ["A", "attack",  "Attack",  "X", "Work a contested/dirty tile"],
  ["S", "dispatch","Dispatch","+", "Request a hero spawn (advisory)"],
  ["D", "forge",   "Forge",   "*", "Ticket -> prompt_compiler"],
  ["F", "guard",   "Guard",   "?", "laya_cli guard preset check"],
  ["Z", "rally",   "Rally",   "!", "Set rally point (click map)"],
  ["X", "compact", "Compact", "C", "Request context compaction"],
  ["C", "power",   "Powers",  "M", "God powers (meteor, vision...)"],
  ["V", "menu",    "Menu",    "=", "F10 game menu"],
];

export class HUD {
  constructor(actions) {
    this.act = actions;              // callbacks into main.js
    this.ticket = null;
    this.root = document.getElementById("hud");
    this._build();
  }

  _build() {
    this.root.innerHTML = `
    <div id="topbar">
      <div class="grp">
        <span class="cap">res</span>
        <span class="pill gold" id="r-gold"><b>Au</b>-</span>
        <span class="pill" id="r-ctx"><b>Cx</b>-</span>
        <span class="pill" id="r-gas"><b>Gas</b>-</span>
        <span class="pill" id="r-sup"><b>Sup</b>-/-</span>
      </div>
      <i class="sep"></i>
      <div class="grp">
        <span class="cap">war</span>
        <span class="pill" id="r-dirty"><b>Dr</b>-</span>
        <span class="pill" id="r-upkeep"><b>Up</b>-</span>
        <span class="pill" id="r-age"><b>Age</b>-</span>
      </div>
      <div class="grp sys">
        <span class="pill btn" id="b-idle" title="jump to an idle unit">[.]</span>
        <span class="pill btn" id="b-tour" title="tutorial tour (T)">?</span>
        <span class="pill btn" id="b-theme" title="theme">theme</span>
        <span class="pill btn" id="b-menu" title="F10">=</span>
      </div>
    </div>
    <div id="roster"></div>
    <div id="bldstrip"></div>
    <div id="tickets"></div>
    <div id="alerts"></div>
    <div id="decision" class="hidden"></div>
    <div id="bottom">
      <canvas id="minimap" width="180" height="135"></canvas>
      <div id="portrait"><div id="p-name">-</div><div id="p-stats"></div>
        <div id="inv"></div></div>
      <div id="cmdcard"></div>
      <div id="feed"></div>
    </div>
    <div id="cardtip" class="hidden"></div>
    <div id="gamemenu" class="hidden">
      <h3>Menu (F10)</h3>
      <button id="gm-theme">Switch Theme</button>
      <button id="gm-ssao">Toggle SSAO</button>
      <button id="gm-audio">Toggle Audio</button>
      <button id="gm-score">Score</button>
      <button id="gm-close">Resume</button>
      <div id="gm-score-out"></div>
    </div>`;
    const card = document.getElementById("cmdcard");
    for (const [hk, id, label, icon, tip] of SLOTS) {
      const b = document.createElement("button");
      b.className = "cmd"; b.dataset.cmd = id;
      b.innerHTML = `<i>${icon}</i><kbd>${hk}</kbd><s>${label}</s>`;
      b.onmouseenter = () => this._tip(b, label, hk, tip);
      b.onmouseleave = () => this._tip();
      b.onclick = () => this.act.command(id);
      card.appendChild(b);
    }
    document.getElementById("b-theme").onclick = () => this.act.theme();
    document.getElementById("b-menu").onclick =
      document.getElementById("gm-close").onclick =
      () => document.getElementById("gamemenu").classList.toggle("hidden");
    document.getElementById("gm-theme").onclick = () => this.act.theme();
    document.getElementById("gm-ssao").onclick = () => this.act.ssao();
    document.getElementById("gm-audio").onclick = () => this.act.audio();
    document.getElementById("gm-score").onclick = () => this.act.score();
    document.getElementById("b-idle").onclick = () => this.act.idlePing();
    document.getElementById("b-tour").onclick = () => this.act.tour();
    addEventListener("keydown", (e) => {
      if (e.target.tagName === "INPUT" || e.repeat) return;
      if (e.code === "F10") {
        e.preventDefault();
        document.getElementById("gamemenu").classList.toggle("hidden");
        return;
      }
      const slot = SLOTS.find(s => "Key" + s[0] === e.code);
      if (slot) this.act.command(slot[1]);
      if (e.code === "KeyT") this.act.tour();
      if (/^F[1-5]$/.test(e.code))
        this.act.focusHero(+e.code[1] - 1);
    });
  }

  _tip(el, title, hk, tip) {
    const t = document.getElementById("cardtip");
    if (!el) { t.classList.add("hidden"); return; }
    t.innerHTML = `<b>${esc(title)}</b> <kbd>[${hk}]</kbd><br>${esc(tip)}`;
    t.classList.remove("hidden");
  }

  /* ---------- data updates ---------- */
  topbar(world, repo) {
    const r = world?.resources || {}, gas = repo?.gas || {},
          git = repo?.git || {}, sup = r;
    const set = (id, v, cls = "") => {
      const e = document.getElementById(id);
      e.innerHTML = v; e.className = "pill " + cls;
    };
    set("r-gold", `<b>Au</b>${r.gold ?? 0} <i>+${r.income_min ?? 0}/m</i>`,
        "gold");
    set("r-ctx", `<b>Cx</b>${Math.round(r.lumber_pct ?? 0)}%`,
        (r.lumber_pct ?? 0) > (r.thresholds?.crit ?? 90) ? "crit" :
        (r.lumber_pct ?? 0) > (r.thresholds?.warn ?? 70) ? "warn" : "");
    set("r-gas", `<b>Gas</b>${gas.free_pct ?? "-"}%`,
        gas.free_pct < 10 ? "crit" : gas.free_pct < 25 ? "warn" : "");
    set("r-sup", `<b>Sup</b>${sup.supply_used ?? 0}/${sup.supply_cap ?? 8}`);
    set("r-dirty", `<b>Dr</b>${(git.dirty || []).length}`,
        (git.dirty || []).length ? "warn" : "");
    set("r-upkeep", `<b>Up</b>${r.upkeep || "-"}`);
    const a = world?.age || {};
    set("r-age", `<b>${a.roman || "?"}</b>${a.name || ""}
      <i>${a.favor ?? 0}f</i>`);
  }

  roster(units) {
    const el = document.getElementById("roster");
    el.innerHTML = "";
    (units || []).slice(0, 5).forEach((u, i) => {
      const d = document.createElement("div");
      d.className = "hero " + (u.status_live || u.status || "");
      d.innerHTML = `<b>F${i + 1}</b> <span>${esc(u.cls || u.profile)}</span>
        <em>${esc(u.name || u.id)}</em>
        <i class="lv">Lv${u.level || 1}</i>
        <i class="st">${esc(u.status_live || u.status || "")}</i>`;
      d.onclick = () => this.act.select(u.id, true);
      el.appendChild(d);
    });
  }

  bldstrip(buildings) {
    const el = document.getElementById("bldstrip");
    el.innerHTML = "";
    for (const b of buildings || []) {
      const d = document.createElement("div");
      d.className = "bld" + (b.activity ? " act" : "");
      d.innerHTML = `<span>${esc(b.name)}</span>`;
      d.onclick = () => this.act.center(b.pos?.xy || [36, 27]);
      el.appendChild(d);
    }
  }

  tickets(issues) {
    const el = document.getElementById("tickets");
    el.innerHTML = "";
    for (const i of (issues || []).slice(0, 12)) {
      const days = Math.floor((i.age_s || 0) / 86400);
      const d = document.createElement("div");
      d.className = "ticket" + (this.ticket === i.n ? " sel" : "") +
        (days > 14 ? " stale" : "");
      d.innerHTML = `<b>#${esc(i.n)}</b> ${esc(i.title).slice(0, 48)}
        <i>${days}d</i>`;
      d.onclick = () => {
        this.ticket = this.ticket === i.n ? null : i.n;
        this.tickets(this._issues);
        this.act.ticketSel?.(this.ticket);
      };
      el.appendChild(d);
    }
    this._issues = issues;
  }

  feed(lines) {
    const el = document.getElementById("feed");
    el.innerHTML = (lines || []).slice(-9).map(l =>
      `<div class="f-${l.kind || "info"}">${esc(l.text || l)}</div>`).join("");
    el.scrollTop = el.scrollHeight;
  }

  portrait(u) {
    document.getElementById("p-name").textContent =
      u ? `${u.name || u.id} — ${u.cls || ""}` : "-";
    document.getElementById("p-stats").innerHTML = u ? `
      <div>model ${esc(u.model)} · tier ${esc(u.tier)}</div>
      <div>task ${esc((u.title || u.task || "").slice(0, 60))}</div>
      <div>status ${esc(u.status_live || u.status)} · xp ${u.xp || 0}
        · lv ${u.level || 1}</div>
      <div>kit ${esc((u.kit || []).join(", "))}</div>` : "";
    document.getElementById("inv").innerHTML = u && u.inventory
      ? u.inventory.map(x => `<i>${esc(x)}</i>`).join("") : "";
  }

  minimap(map, units, buildings, cam) {
    const cv = document.getElementById("minimap");
    const ctx = cv.getContext("2d");
    const W = cv.width, H = cv.height;
    if (!map) return;
    const tw = W / map.w, th = H / map.h;
    const regs = map.tile_region || [], fog = map.fog || [],
          mark = map.mark || [];
    const cols = ["#3d5238", "#51603f", "#5d6a44", "#495a41", "#57634b",
                  "#4a5c46", "#51634b", "#4d6047", "#556450", "#48573f",
                  "#525f46"];
    for (let y = 0; y < map.h; y++)
      for (let x = 0; x < map.w; x++) {
        const i = y * map.w + x;
        ctx.fillStyle = cols[regs[i] % cols.length];
        ctx.fillRect(x * tw, y * th, tw + 0.4, th + 0.4);
        if (mark[i] === 4) {
          ctx.fillStyle = "#ffd54a";
          ctx.fillRect(x * tw, y * th, tw, th);
        }
        if (!fog[i]) {
          ctx.fillStyle = "rgba(3,6,9,.85)";
          ctx.fillRect(x * tw, y * th, tw + 0.4, th + 0.4);
        } else if (fog[i] === 1) {
          ctx.fillStyle = "rgba(3,6,9,.4)";
          ctx.fillRect(x * tw, y * th, tw + 0.4, th + 0.4);
        }
      }
    ctx.fillStyle = "#e8c86a";
    for (const b of buildings || []) {
      const xy = b.pos?.xy || [0, 0];
      ctx.fillRect(xy[0] * tw - 1.5, xy[1] * th - 1.5, 3, 3);
    }
    for (const u of units || []) {
      const p = u._pos || u.pos || { x: 36, y: 27 };
      ctx.fillStyle = u.status === "error" ? "#ff7a7a" : "#7fc9ff";
      ctx.beginPath();
      ctx.arc((p.x ?? p[0]) * tw, (p.y ?? p[1]) * th, 1.6, 0, 7);
      ctx.fill();
    }
    if (cam) {                                   // view box
      ctx.strokeStyle = "rgba(255,255,255,.6)";
      const vx = cam.target.x.x * tw, vy = cam.target.z.x * th;
      ctx.strokeRect(vx - cam.dist.x * 0.55, vy - cam.dist.x * 0.4,
                     cam.dist.x * 1.1, cam.dist.x * 0.8);
    }
  }

  decision(list) {
    const el = document.getElementById("decision");
    if (!list || !list.length) { el.classList.add("hidden"); return; }
    const d = list[0];
    el.classList.remove("hidden");
    el.innerHTML = `<h4>War Council - ${esc(d.kind || "gate")}</h4>
      <p>${esc(d.prompt)}</p>
      <div>${(d.options || []).map((o, i) =>
        `<button data-i="${i}">${esc(o)}</button>`).join("")}</div>`;
    el.querySelectorAll("button").forEach(b =>
      b.onclick = () => this.act.gateAnswer(d.id, +b.dataset.i));
  }

  alert(level, code, msg) {
    const el = document.getElementById("alerts");
    const d = document.createElement("div");
    d.className = "toast " + level;
    d.innerHTML = `<b>${esc(code)}</b> ${esc(msg)}`;
    el.appendChild(d);
    setTimeout(() => d.remove(), 6500);
  }

  score(s) {
    document.getElementById("gm-score-out").innerHTML =
      `<pre>${esc(JSON.stringify(s, null, 1)).slice(0, 1800)}</pre>`;
  }

  setThemeIcon(theme) {
    document.getElementById("b-theme").textContent = theme;
    document.body.dataset.theme = theme;
  }
}
