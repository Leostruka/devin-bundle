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
    this._pu = null;
    this._pLoop();
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
        <span class="pill" id="r-orb" title="time of day + wind">&#9788;<i>--</i></span>
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
      <div id="mmwrap">
        <canvas id="minimap" width="180" height="135"></canvas>
        <div id="mmf">
          <button data-f="all" class="on">All</button>
          <button data-f="units">Units</button>
          <button data-f="bld">Bld</button>
          <button data-f="ping" title="alt-click map = ping">Ping</button>
        </div>
      </div>
      <div id="portrait">
        <canvas id="portcv" width="56" height="56"></canvas>
        <div id="p-right"><div id="p-name">-</div><div id="p-stats"></div>
        <div id="p-bar" class="hidden"><i></i><s></s></div>
        <div id="inv"></div></div></div>
      <div id="cmdcard"></div>
      <div id="feed"></div>
    </div>
    <div id="cardtip" class="hidden"></div>
    <div id="banner" class="hidden"></div>
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
      b.onmouseenter = () => this._tip(b, label, hk, tip, id);
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
    /* minimap filter buttons (All / Units / Bld / Ping mode) */
    this._mmf = "all"; this._pings = [];
    document.querySelectorAll("#mmf button").forEach(b =>
      b.onclick = () => {
        this._mmf = b.dataset.f;
        document.querySelectorAll("#mmf button").forEach(x =>
          x.classList.toggle("on", x === b));
      });
    addEventListener("keydown", (e) => {
      if (e.target.tagName === "INPUT" || e.repeat) return;
      if (e.code === "F10") {
        e.preventDefault();
        document.getElementById("gamemenu").classList.toggle("hidden");
        return;
      }
      const slot = SLOTS.find(s => "Key" + s[0] === e.code);
      if (slot) this.act.command(slot[1]);
      /* WC3 Space: snap camera to the last positional alert */
      if (e.code === "Space") { e.preventDefault(); this.act.jumpAlert(); }
      if (e.code === "KeyT") this.act.tour();
      if (/^F[1-5]$/.test(e.code))
        this.act.focusHero(+e.code[1] - 1);
    });
  }

  _tip(el, title, hk, tip, cmdId) {
    const t = document.getElementById("cardtip");
    if (!el) { t.classList.add("hidden"); return; }
    /* WC3 tooltip chrome: title + hotkey, target kind, then flavor */
    const target = { move: "map point", patrol: "map point",
                     attack: "contested tile", rally: "map point" }[cmdId]
                   || "instant";
    t.innerHTML = `<b>${esc(title)}</b> <kbd>[${hk}]</kbd>` +
      `<br><span class="tmeta">target: ${target}</span>` +
      `<br>${esc(tip)}`;
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

  /* WC3 clock dial: tiny canvas: the sun rides the upper arc by day,
     moon the lower at night; wind readout beside it */
  dayOrb(day, windKph) {
    const e = document.getElementById("r-orb");
    if (!e._cv) {
      e.innerHTML = `<canvas id="dial" width="30" height="30"
        style="vertical-align:middle"></canvas><i></i>`;
      e._cv = e.querySelector("canvas");
      e._tx = e.querySelector("i");
    }
    const v = `${Math.round(day * 100)}% ${Math.round(windKph)}kph`;
    if (e._v !== v) { e._tx.textContent = v; e._v = v; }
    const c = e._cv.getContext("2d");
    c.clearRect(0, 0, 30, 30);
    c.fillStyle = "#0a1016"; c.strokeStyle = "#5a6b7d";
    c.beginPath(); c.arc(15, 15, 13, 0, 7); c.fill(); c.stroke();
    c.beginPath();                       // horizon split
    c.moveTo(2, 15); c.lineTo(28, 15);
    c.strokeStyle = "#3a4a58"; c.stroke();
    const a = Math.PI * (1 - day);       // day=1 noon top, day=0 bottom
    const isDay = day > 0.15;
    const bx = 15 + Math.cos(a) * 9, by = 15 - Math.sin(a) * 9;
    c.fillStyle = isDay ? "#ffd54a" : "#cfd8e3";
    c.beginPath(); c.arc(bx, isDay ? by : 15 + Math.sin(Math.PI * day) * 9,
                         3.4, 0, 7); c.fill();
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
    /* the canonical feed can log the same event repeatedly (repeat quest
       completions, mass orders): collapse identical neighbours into
       one line with a counter instead of a wall of duplicates */
    const out = [];
    for (const l of lines || []) {
      const txt = l.text || String(l);
      const last = out[out.length - 1];
      if (last && last.txt === txt && last.l.kind === l.kind) last.n++;
      else out.push({ l, txt, n: 1 });
    }
    el.innerHTML = out.slice(-9).map(({ l, txt, n }) => {
      /* WC3 feed chrome: kind + content colorization */
      const cls = l.kind ? `f-${l.kind}`
        : /complete|reward|green/i.test(txt) ? "f-good"
        : /error|fail|crit|fallen/i.test(txt) ? "f-bad" : "f-info";
      return `<div class="${cls}">${esc(txt)}` +
        (n > 1 ? ` <b>&times;${n}</b>` : "") + `</div>`;
    }).join("");
    el.scrollTop = el.scrollHeight;
  }

  /* animated 3D-lit portrait (skill: #portcv): sphere head lit by a
     slowly-swinging light, class-colored helm, periodic blink */
  _pLoop() {
    const cv = document.getElementById("portcv");
    const ctx = cv.getContext("2d");
    const draw = () => {
      requestAnimationFrame(draw);
      const u = this._pu;
      ctx.clearRect(0, 0, 56, 56);
      if (!u) return;
      const t = performance.now() / 1000;
      const bob = Math.sin(t * 1.3) * 1.2;
      const lx = Math.sin(t * 0.6) * 0.5 - 0.4;      // light dir swing
      /* head: Lambertian-ish radial gradient, lit side toward lx */
      const cx = 28, cy = 30 + bob;
      const grad = ctx.createRadialGradient(
        cx + lx * 10, cy - 8, 3, cx, cy, 22);
      const body = u.tier === "Commander" ? "#d8c8a0" :
                   u.tier === "Knight" ? "#c0d0e8" : "#a8b8c8";
      grad.addColorStop(0, "#f4f8ff");
      grad.addColorStop(0.4, body);
      grad.addColorStop(1, "#1a2230");
      ctx.fillStyle = grad;
      ctx.beginPath(); ctx.arc(cx, cy, 20, 0, 7); ctx.fill();
      /* helm by tier */
      ctx.fillStyle = u.tier === "Commander" ? "#d4af37" :
                      u.tier === "Knight" ? "#8a97a8" : "#5a6878";
      ctx.beginPath();
      ctx.moveTo(cx - 20, cy - 8); ctx.lineTo(cx, cy - 26 - bob * 0.4);
      ctx.lineTo(cx + 20, cy - 8); ctx.closePath(); ctx.fill();
      /* eyes, blink every ~3.4s */
      const blink = (t % 3.4) < 0.12 ? 0.15 : 1;
      ctx.fillStyle = "#0a0f16";
      ctx.fillRect(cx - 8, cy - 2, 5, 4 * blink);
      ctx.fillRect(cx + 4, cy - 2, 5, 4 * blink);
      /* status tint under-glow */
      if (/error|fail/.test(u.status_live || u.status || "")) {
        ctx.strokeStyle = "#ff5a5a"; ctx.lineWidth = 2;
        ctx.beginPath(); ctx.arc(cx, cy, 21.5, 0, 7); ctx.stroke();
      }
    };
    draw();
  }

  portrait(u, nsel = 1) {
    this._pu = u && (u.tier || u.cls || u.kit) ? u : null;   // units only
    document.getElementById("p-name").textContent = nsel > 1
      ? `${nsel} selected · ${u ? (u.cls || u.name || u.id) : ""}`
      : u ? `${u.name || u.id} · ${u.cls || ""}` : "-";
    document.getElementById("p-stats").innerHTML = u ? `
      <div>model ${esc(u.model)} · tier ${esc(u.tier)}</div>
      <div>task ${esc((u.title || u.task || "").slice(0, 60))}</div>
      <div>status ${esc(u.status_live || u.status)} · xp ${u.xp || 0}
        · lv ${u.level || 1}</div>
      <div>kit ${esc((u.kit || []).join(", "))}</div>` : "";
    /* inventory runes arrive as objects ({gate, quest, ledger,
       evidence}): render the seal, keep the evidence on hover */
    document.getElementById("inv").innerHTML = u && u.inventory
      ? u.inventory.map(x => (x && typeof x === "object")
          ? `<i title="${esc(x.evidence || "")}">` +
            `${esc([x.gate, x.quest || x.ledger].filter(Boolean)
              .join(" · "))}</i>`
          : `<i>${esc(x)}</i>`).join("") : "";
    /* progress bar: unit XP -> next level / building production */
    const bar = document.getElementById("p-bar");
    if (u && (u.tier || u.kit)) {
      bar.classList.remove("hidden");
      bar.querySelector("i").style.width = (u.xp || 0) % 100 + "%";
      bar.querySelector("s").textContent = "xp " + (u.xp || 0);
    } else if (u && u.activity !== undefined) {
      bar.classList.remove("hidden");
      bar.querySelector("i").style.width =
        Math.min(100, u.activity) + "%";
      bar.querySelector("s").textContent = "prod " + u.activity;
    } else bar.classList.add("hidden");
  }

  /* WC3 subgroup chips: one chip per selected entity, click = solo select */
  subgroups(list, activeId) {
    let el = document.getElementById("subgrp");
    if (!list || list.length < 2) { if (el) el.innerHTML = ""; return; }
    if (!el) {
      el = document.createElement("div");
      el.id = "subgrp";
      document.getElementById("bottom").insertBefore(
        el, document.getElementById("cmdcard"));
    }
    el.innerHTML = list.map((u, i) =>
      `<button data-id="${esc(u.id)}" title="${esc(u.name || u.id)}">` +
      `${esc((u.cls || u.id || "?").slice(0, 2))}</button>`).join("");
    el.querySelectorAll("button").forEach(b => {
      b.classList.toggle("act", b.dataset.id === activeId);
      b.onclick = () => this.act.select(b.dataset.id, false);
    });
  }

  /* WC3 armed state: the pending command button stays lit */
  armCmd(id) {
    document.querySelectorAll("#cmdcard .cmd").forEach(b =>
      b.classList.toggle("armed", b.dataset.cmd === id));
  }

  /* WC3 quest banner: big center-top gold text, ~3s life */
  banner(text) {
    const b = document.getElementById("banner");
    b.textContent = text;
    b.classList.remove("hidden", "pop");
    void b.offsetWidth;                    // restart the animation
    b.classList.add("pop");
    clearTimeout(this._bT);
    this._bT = setTimeout(() => b.classList.add("hidden"), 3000);
  }

  /* WC3 invalid-command feedback: red flash over the command card */
  deny() {
    const c = document.getElementById("cmdcard");
    c.classList.add("deny");
    clearTimeout(this._denyT);
    this._denyT = setTimeout(() => c.classList.remove("deny"), 240);
  }

  minimap(map, units, buildings, cam, rally) {
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
        /* contested tiles blink on the minimap like WC3 battle flash */
        if (mark[i] === 2 &&
            (performance.now() / 320 % 1) < 0.5) {
          ctx.fillStyle = "rgba(210,50,35,.5)";
          ctx.fillRect(x * tw, y * th, tw, th);
        }
        const f = map.reveal?.has(i) ? 2 : fog[i];
        if (!f) {
          ctx.fillStyle = "rgba(3,6,9,.85)";
          ctx.fillRect(x * tw, y * th, tw + 0.4, th + 0.4);
        } else if (f === 1) {
          ctx.fillStyle = "rgba(3,6,9,.4)";
          ctx.fillRect(x * tw, y * th, tw + 0.4, th + 0.4);
        }
      }
    ctx.fillStyle = "#e8c86a";
    if (this._mmf === "all" || this._mmf === "bld")
      for (const b of buildings || []) {
        const xy = b.pos?.xy || [0, 0];
        ctx.fillRect(xy[0] * tw - 1.5, xy[1] * th - 1.5, 3, 3);
      }
    if (this._mmf === "all" || this._mmf === "units")
      for (const u of units || []) {
        const p = u._pos || u.pos || { x: 36, y: 27 };
        ctx.fillStyle = u.status === "error" ? "#ff7a7a" : "#7fc9ff";
        ctx.beginPath();
        ctx.arc((p.x ?? p[0]) * tw, (p.y ?? p[1]) * th, 1.6, 0, 7);
        ctx.fill();
      }
    /* WC3 pings: expanding gold rings, ~1.6s life */
    const nowP = performance.now();
    this._pings = this._pings.filter(p => nowP - p.t < 1600);
    for (const p of this._pings) {
      const k = (nowP - p.t) / 1600;
      ctx.strokeStyle = `rgba(255,213,74,${1 - k})`;
      ctx.lineWidth = 1.5;
      ctx.beginPath();
      ctx.arc(p.x * tw, p.y * th, 3 + k * 22, 0, 7);
      ctx.stroke();
    }
    /* rally flag glyph on the minimap */
    if (rally) {
      const rx = rally.x * tw, ry = rally.y * th;
      ctx.strokeStyle = "#6fe39a";
      ctx.lineWidth = 1.2;
      ctx.beginPath(); ctx.moveTo(rx, ry); ctx.lineTo(rx, ry - 5);
      ctx.stroke();
      ctx.fillStyle = "#6fe39a";
      ctx.beginPath(); ctx.moveTo(rx, ry - 5);
      ctx.lineTo(rx + 4, ry - 3.6); ctx.lineTo(rx, ry - 2.4);
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

  alert(level, code, msg, x, y) {
    const el = document.getElementById("alerts");
    const d = document.createElement("div");
    d.className = "toast " + level;
    d.innerHTML = `<b>${esc(code)}</b> ${esc(msg)}`;
    if (x !== undefined && y !== undefined) this.lastAlert = [x, y];
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
