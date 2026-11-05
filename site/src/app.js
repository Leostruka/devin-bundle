/* devin-bundle // atlas — terminal interactions */
(() => {
const D = window.DATA || {};
const $ = (s, r = document) => r.querySelector(s);
const $$ = (s, r = document) => [...r.querySelectorAll(s)];
const esc = s => s.replace(/[&<>"]/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[c]));

/* ---------------- tabs / router ---------------- */
const SECTIONS = ["boot","skills","agents","hooks","scripts","adr","docs","issues","changelog"];
const tabs = $("#tabs");
tabs.innerHTML = SECTIONS.map(s =>
  `<button role="tab" data-sec="${s}" aria-selected="${s==="boot"}">~/${s}</button>`).join("");

function go(sec){
  if(!SECTIONS.includes(sec)) sec = "boot";
  SECTIONS.forEach(s => {
    $("#view-"+s).hidden = s !== sec;
    $(`button[data-sec="${s}"]`).setAttribute("aria-selected", s===sec);
  });
  location.hash = sec === "boot" ? "" : sec;
  curSec = sec;
  const rp = $("#repl-path"); if(rp) rp.textContent = (sec === "boot" ? "~" : "~/" + sec) + "$";
  if(sec === "adr" && !$("#adr-body").innerHTML) openDoc("adr", 0);
  if(sec === "docs" && !$("#docs-body").innerHTML) openDoc("docs", 0);
  if(sec !== "boot") document.title = `devin-bundle // atlas — ${sec}`;
  window.scrollTo(0,0);
}
tabs.addEventListener("click", e => { const b = e.target.closest("button"); if(b) go(b.dataset.sec); });
addEventListener("hashchange", () => go(location.hash.slice(1) || "boot"));

/* ---------------- boot sequence ---------------- */
const LINES = [
  ["dim","$ devin doctor --verbose"],
  ["ok","  pass  custom subagent profiles   21 profile(s) loaded"],
  ["ok","  pass  otel exporter environment  no unsupported variables"],
  ["ok","  pass  otel export                off"],
  ["dim",""],
  ["dim","$ cat manifest.json | jq '.skill_count, .agent_count'"],
  ["",`${D.counts?.skills ?? 168}`],
  ["",`${(D.counts?.agents ?? 16) + 5}`],
  ["dim",""],
  ["dim","$ ./install.ps1 -Force"],
  ["ok","  [+] skills        " + `${D.counts?.skills ?? 168} synced   live=bundle`],
  ["ok","  [+] agents        " + `${D.counts?.agents ?? 16} profiles`],
  ["ok","  [+] hooks         " + `${(D.hooks||[]).reduce((n,e)=>n+e.hooks.length,0)} hooks rendered from hooks.v1.json`],
  ["ok","  [+] scripts       " + `${D.counts?.scripts ?? 34} hook scripts`],
  ["warn","  [~] credentials.toml  use -RestoreSecrets to install"],
  ["dim",""],
  ["dim","$ ls .devin/adr | wc -l && ls .devin/docs | wc -l"],
  ["",`${D.counts?.adrs ?? 8}`],
  ["",`${D.counts?.docs ?? 14}`],
  ["dim",""],
  ["",`bundle v${D.version ?? "?"} — atlas ready. cd <section> to explore.`],
];

const LOGO_DEVIN = ` ____            _          ____                  _ _
|  _ \\  _____   _(_)_ __    | __ ) _   _ _ __   __| | | ___
| | | |/ _ \\ \\ / / | '_ \\   |  _ \\| | | | '_ \\ / _\` | |/ _ \\
| |_| |  __/\\ V /| | | | |  | |_) | |_| | | | | (_| | |  __/
|____/ \\___| \\_/ |_|_| |_|  |____/ \\__,_|_| |_|\\__,_|_|\\___|`;
const LOGO_LEO = ` _        _____   ___   ____   _____  ____   _   _  _  __   _
| |      | ____| / _ \\ / ___| |_   _||  _ \\ | | | || |/ /  / \\
| |      |  _|  | | | |\\___ \\   | |  | |_) || | | || ' /  / _ \\
| |___   | |___ | |_| | ___) |  | |  |  _ < | |_| || . \\ / ___ \\
|_____|  |_____| \\___/ |____/   |_|  |_| \\_\\ \\___/ |_|\\_\\/_/   \\_\\`;

const NOISE = "\\|/-_<>[]{}=+*#%&";
function scrambleSwap(pre, from, to){
  const a = from.split("\n"), b = to.split("\n");
  const rows = Math.max(a.length, b.length);
  const out = [];
  for(let r = 0; r < rows; r++){
    const fa = a[r] || "", fb = b[r] || "";
    const len = Math.max(fa.length, fb.length);
    out.push({fa: fa.padEnd(len), fb: fb.padEnd(len)});
  }
  let frame = 0;
  const frames = 14;
  const tick = () => {
    frame++;
    const prog = frame / frames;
    pre.textContent = out.map(({fa, fb}) =>
      [...fa].map((ca, i) => {
        const reveal = (i / fa.length) < prog * 1.15;
        if(reveal) return fb[i];
        if(fb[i] === " " && ca === " ") return " ";
        return NOISE[(Math.random() * NOISE.length) | 0];
      }).join("")
    ).join("\n");
    if(frame < frames) setTimeout(tick, 40);
    else pre.textContent = to;
  };
  tick();
}
function logoSwap(){
  const pre = $(".logo");
  if(!pre) return;
  let cur = LOGO_DEVIN, showDevin = true;
  const reduced = matchMedia("(prefers-reduced-motion: reduce)").matches;
  setInterval(() => {
    const next = showDevin ? LOGO_LEO : LOGO_DEVIN;
    if(reduced) pre.textContent = next;
    else scrambleSwap(pre, cur, next);
    cur = next; showDevin = !showDevin;
  }, 5000);
}

function boot(){
  const el = $("#bootlog");
  const reduced = matchMedia("(prefers-reduced-motion: reduce)").matches;
  if(reduced){
    el.innerHTML = LINES.map(([c,t]) => `<span class="${c}">${esc(t) || " "}</span>`).join("\n");
    logoSwap();
    return;
  }
  let li = 0, ci = 0, cur;
  const cursor = '<span class="cursor"></span>';
  function step(){
    if(li >= LINES.length){ el.innerHTML += cursor; setTimeout(logoSwap, 4000); return; }
    const [cls, txt] = LINES[li];
    if(!cur){ cur = document.createElement("div"); cur.className = cls; el.appendChild(cur); }
    if(txt === ""){ el.removeChild(cur); el.innerHTML += "<br>"; cur=null; li++; step(); return; }
    cur.textContent = txt.slice(0, ++ci);
    if(ci >= txt.length){ cur=null; ci=0; li++; setTimeout(step, txt.startsWith("$")?60:22); }
    else setTimeout(step, txt.startsWith("$")?18:4);
  }
  step();
}

/* ---------------- skills ---------------- */
const grid = $("#skill-grid");
function skillCard(s){
  return `<button class="card" data-open="skill" data-name="${esc(s.dir)}">
    <span class="cname">${esc(s.name)}</span>
    <span class="cdesc">${esc(s.desc||"")}</span>
    <span class="cmeta"><span class="tag">${s.lines}L</span>${s.vendor?'<span class="tag cy">'+esc(s.vendor)+"</span>":""}</span>
  </button>`;
}
grid.innerHTML = (D.skills||[]).map(skillCard).join("");
$("#skill-count").textContent = `${(D.skills||[]).length} match(es)`;
$("#skill-q").addEventListener("input", e => {
  const q = e.target.value.trim().toLowerCase();
  let n = 0;
  $$(".card", grid).forEach(c => {
    const s = (D.skills||[]).find(x => x.dir === c.dataset.name);
    const hit = !q || (s.name+" "+s.desc).toLowerCase().includes(q);
    c.style.display = hit ? "" : "none"; if(hit) n++;
  });
  $("#skill-count").textContent = `${n} match(es)`;
});

/* ---------------- agents ---------------- */
$("#agent-grid").innerHTML = (D.agents||[]).map(a => `
  <button class="card" data-open="agent" data-name="${esc(a.name)}">
    <span class="cname">${esc(a.name)}</span>
    <span class="cdesc">${esc(a.desc||"")}</span>
    <span class="cmeta">${a.model?`<span class="tag am">${esc(a.model)}</span>`:""}</span>
  </button>`).join("");

/* ---------------- hooks ---------------- */
$("#hooks-flow").innerHTML = (D.hooks||[]).map(ev => `
  <div class="evt"><h3>${esc(ev.event)}</h3><div class="lane">
    ${ev.hooks.map(h => `<div class="hkrow">
      <span class="match">${esc(h.matcher)}</span><span class="arrow">-&gt;</span>
      <span class="cmd">${esc(h.script)}
        <span class="badge to">${h.timeout ?? "?"}s</span>
        ${h.fail_closed?'<span class="badge fc">fail_closed</span>':""}
      </span></div>`).join("")}
  </div></div>`).join("");

/* ---------------- scripts ---------------- */
$("#script-list").innerHTML = (D.scripts||[]).map(s => `
  <div class="srow"><div class="sf">${esc(s.file)}</div>
    <div class="sd">${esc(s.doc||"")}</div>
    <div class="sl">${s.lines} lines</div></div>`).join("");

/* ---------------- readers (adr / docs) ---------------- */
function openDoc(kind, i){
  const list = kind === "adr" ? D.adrs : D.docs;
  const body = $(`#${kind}-body`), idx = $(`#${kind}-index`);
  if(!list || !list.length){ body.innerHTML = "<p>empty</p>"; return; }
  i = Math.max(0, Math.min(i, list.length-1));
  const d = list[i];
  idx.innerHTML = list.map((x,j) =>
    `<button aria-current="${j===i}" data-kind="${kind}" data-i="${j}">${esc(x.title)}</button>`).join("");
  body.innerHTML = `<p style="color:var(--dim);font-size:.8em">${esc(d.file)}</p>` + d.html;
  if(d.has_mermaid && window.mermaid){
    try{ mermaid.run({nodes: $$("pre.mermaid", body)}); }catch(e){}
  }
  body.scrollTop = 0;
}
document.addEventListener("click", e => {
  const b = e.target.closest("#adr-index button, #docs-index button");
  if(b) openDoc(b.dataset.kind, +b.dataset.i);
});

/* ---------------- changelog ---------------- */
$("#changelog-log").innerHTML = (D.changelog||[]).map(r => `
  <div class="rel"><span class="rv">${esc(r.version)}</span>
    <span class="rd">${esc(r.date)}</span>
    <span class="rentries">${r.entries} entr(ies)</span>
    <div class="doc">${r.html}</div></div>`).join("");

/* ---------------- issues board ---------------- */
$("#issues-board").innerHTML = (D.issues||[]).map(g => `
  <div class="rel"><span class="rv">${esc(g.group)}</span>
    <span class="rd">${g.resolved}/${g.count} resolved</span>
    <table class="tbl"><tbody>${g.items.map(i => `
      <tr><td class="mono">${esc(i.file.replace(/\.md$/,""))}</td>
      <td>${esc(i.title)}</td>
      <td>${i.priority ? `<span class="pri p${esc(i.priority)}">${esc(i.priority)}</span>` : ""}</td>
      <td><span class="st ${i.status==="resolved"?"ok":"op"}">${esc(i.status)||"?"}</span></td>
      <td class="dim">${i.answered?"answered":""}</td></tr>`).join("")}</tbody></table></div>`).join("") ||
  `<div class="dim">no issue ledgers under .devin/scratch/*/issues/</div>`;

/* ---------------- modal pager ---------------- */
const modal = $("#modal");
function openModal(title, html){
  $("#modal-title").textContent = title;
  $("#modal-body").innerHTML = html;
  modal.hidden = false;
  $("#modal-body").scrollTop = 0;
  const mnodes = $$("pre.mermaid", $("#modal-body"));
  if(mnodes.length && window.mermaid){ try{ mermaid.run({nodes: mnodes}); }catch(e){} }
}
function closeModal(){ modal.hidden = true; }
document.addEventListener("click", e => {
  const c = e.target.closest("[data-open]");
  if(c){
    const kind = c.dataset.open, name = c.dataset.name;
    if(kind === "skill"){
      const s = (D.skills||[]).find(x => x.dir === name);
      if(s) openModal(`skills/${s.dir}/SKILL.md`, s.html);
    } else if(kind === "agent"){
      const a = (D.agents||[]).find(x => x.name === name);
      if(a) openModal(`agents/${a.name}.md`, a.html);
    }
  }
  if(e.target === modal || e.target.id === "modal-close") closeModal();
  if(e.target === $("#palette")) $("#palette").hidden = true;
});

/* ---------------- command palette ---------------- */
const pal = $("#palette"), palIn = $("#pal-input"), palRes = $("#pal-results");
const COMMANDS = [
  ...SECTIONS.map(s => ({label:`cd ${s}`, run:()=>go(s)})),
  ...(D.skills||[]).map(s => ({label:`open ${s.name}`, sub:s.desc?.slice(0,70),
    run:()=>{ openModal(`skills/${s.dir}/SKILL.md`, s.html); }})),
  ...(D.agents||[]).map(a => ({label:`open agent ${a.name}`, sub:a.desc?.slice(0,70),
    run:()=>{ openModal(`agents/${a.name}.md`, a.html); }})),
  {label:"help", sub:"sections: "+SECTIONS.join(", "), run:()=>palIn.value="cd "},
];
function palShow(v){
  pal.hidden = false; palIn.value = v||""; palIn.focus(); palFilter();
}
function palFilter(){
  const q = palIn.value.trim().toLowerCase().replace(/^(cd|open)\s+/,"");
  const hits = COMMANDS.filter(c => !q || c.label.toLowerCase().includes(q)).slice(0,14);
  palRes.innerHTML = hits.map((c,i) =>
    `<button data-i="${COMMANDS.indexOf(c)}" class="${i===0?"sel":""}">
      ${esc(c.label)}${c.sub?`<span class="sub">${esc(c.sub)}</span>`:""}</button>`).join("")
    || `<button class="sel">no match — try: skills, hooks, open &lt;name&gt;</button>`;
}
palIn.addEventListener("input", palFilter);
palRes.addEventListener("click", e => {
  const b = e.target.closest("button[data-i]");
  if(b){ COMMANDS[+b.dataset.i].run(); pal.hidden = true; }
});
palIn.addEventListener("keydown", e => {
  if(e.key === "Enter"){
    const b = $("#pal-results button[data-i]");
    if(b){ COMMANDS[+b.dataset.i].run(); pal.hidden = true; }
  }
});

/* ---------------- repl ---------------- */
const repl = $("#repl"), replOut = $("#repl-out"), replPath = $("#repl-path");
const hist = []; let histIdx = -1;
let curSec = "boot";

function rprint(lines){
  replOut.hidden = false;
  for(const [cls, txt] of lines){
    const d = document.createElement("div");
    if(cls) d.className = cls;
    d.textContent = txt === "" ? " " : txt;
    replOut.appendChild(d);
  }
  replOut.scrollTop = replOut.scrollHeight;
}
const recho = t => rprint([["r-cmd", `visitor@devin-bundle:${curSec === "boot" ? "~" : "~/" + curSec}$ ${t}`]]);

const DOCTOR_LINES = () => [
  ["r-cmd","pass  custom subagent profiles   21 profile(s) loaded"],
  ["r-cmd","pass  otel exporter environment   no unsupported variables"],
  ["r-cmd","pass  otel export                 off"],
];
const INSTALL_LINES = () => [
  ["r-cmd",`  [+] skills        ${D.counts?.skills ?? "?"} synced   live=bundle`],
  ["r-cmd",`  [+] agents        ${D.counts?.agents ?? "?"} profiles`],
  ["r-cmd",`  [+] hooks         ${(D.hooks||[]).reduce((n,e)=>n+e.hooks.length,0)} hooks rendered from hooks.v1.json`],
  ["r-cmd",`  [+] scripts       ${D.counts?.scripts ?? "?"} hook scripts`],
  ["r-amber","  [~] credentials.toml  use -RestoreSecrets to install"],
];

function findThing(q){
  q = (q||"").toLowerCase();
  if(!q) return null;
  const s = (D.skills||[]).find(x => x.dir.toLowerCase()===q || x.name.toLowerCase()===q)
        || (D.skills||[]).find(x => x.dir.toLowerCase().startsWith(q) || x.name.toLowerCase().startsWith(q))
        || (D.skills||[]).find(x => x.dir.toLowerCase().includes(q));
  if(s) return {kind:"skill", s};
  const a = (D.agents||[]).find(x => x.name.toLowerCase()===q)
        || (D.agents||[]).find(x => x.name.toLowerCase().startsWith(q));
  if(a) return {kind:"agent", a};
  for(const kind of ["adrs","docs"]){
    const list = D[kind]||[];
    const i = list.findIndex(x => x.title.toLowerCase().includes(q) || x.file.toLowerCase().includes(q));
    if(i >= 0) return {kind: kind === "adrs" ? "adr" : "docs", i};
  }
  return null;
}
function openThing(t){
  if(!t) return false;
  if(t.kind === "skill") openModal(`skills/${t.s.dir}/SKILL.md`, t.s.html);
  else if(t.kind === "agent") openModal(`agents/${t.a.name}.md`, t.a.html);
  else { go(t.kind === "adr" ? "adr" : "docs"); openDoc(t.kind, t.i); }
  return true;
}

const REPL_HELP = [
  ["","help                    this list"],
  ["","cd <section>            boot skills agents hooks scripts adr docs changelog"],
  ["","ls [section]            list sections or items in a section"],
  ["","cat|open <name>         open a skill, agent, adr, or doc"],
  ["","grep <pattern>          filter skills and jump there"],
  ["","doctor                  re-run the boot health check"],
  ["","install                 print the -Force install summary"],
  ["","version                 bundle version"],
  ["","pwd                     current section path"],
  ["","history                 command history"],
  ["","clear                   clear this scrollback"],
  ["",":q                      try it"],
];

function replRun(raw){
  const line = raw.trim();
  if(!line) return;
  recho(line);
  hist.push(line); histIdx = hist.length;
  const [cmd, ...rest] = line.split(/\s+/);
  const arg = rest.join(" ");
  const c = cmd.toLowerCase();
  const secs = SECTIONS;
  if(c === "help" || c === "?"){ rprint(REPL_HELP); return; }
  if(c === "cd"){
    if(!arg || arg === "~" || arg === ".."){ go("boot"); return; }
    const t = secs.find(s => s === arg) || secs.find(s => s.startsWith(arg));
    if(t) go(t);
    else rprint([["r-err",`cd: no such section: ${arg}`]]);
    return;
  }
  if(secs.includes(c)){ go(c); return; }
  if(c === "ls"){
    if(!arg){
      rprint(secs.map(s => ["r-cyan", `${s}/`]));
      return;
    }
    const t = secs.find(s => s === arg || s.startsWith(arg));
    if(!t){ rprint([["r-err",`ls: no such section: ${arg}`]]); return; }
    if(t === "skills") rprint((D.skills||[]).map(s => ["", s.dir]));
    else if(t === "agents") rprint((D.agents||[]).map(a => ["", a.name]));
    else if(t === "adr" || t === "docs") rprint((D[t === "adr" ? "adrs" : "docs"]||[]).map(x => ["", x.file]));
    else if(t === "scripts") rprint((D.scripts||[]).map(x => ["", x.name || x]));
    else if(t === "hooks") rprint((D.hooks||[]).map(e => ["", `${e.event}  (${e.hooks.length} hooks)`]));
    else rprint([["r-dim","nothing to list; it is a rendered view"]]);
    return;
  }
  if(c === "cat" || c === "open"){
    if(!arg){ rprint([["r-err",`${c}: missing operand`]]); return; }
    if(!openThing(findThing(arg))) rprint([["r-err",`${c}: no match: ${arg}`]]);
    return;
  }
  if(c === "grep"){
    if(!arg){ rprint([["r-err","grep: missing pattern"]]); return; }
    go("skills");
    const q = $("#skill-q");
    q.value = arg; q.dispatchEvent(new Event("input"));
    return;
  }
  if(c === "doctor"){ rprint(DOCTOR_LINES()); return; }
  if(c === "install"){ rprint(INSTALL_LINES()); return; }
  if(c === "version" || c === "--version"){
    rprint([["",`devin-bundle v${D.version ?? "?"} · ${D.counts?.skills ?? "?"} skills · ${D.counts?.agents ?? "?"} agents`]]);
    return;
  }
  if(c === "pwd"){ rprint([["",`~/atlas${curSec === "boot" ? "" : "/" + curSec}`]]); return; }
  if(c === "history"){ rprint(hist.map((h,i) => ["r-dim",`  ${i+1}  ${h}`])); return; }
  if(c === "clear"){ replOut.innerHTML = ""; replOut.hidden = true; return; }
  if(c === ":q" || c === "exit" || c === "quit"){
    rprint([["r-dim","no escape. there is only the bundle."]]);
    go("boot"); return;
  }
  if(c === "man"){ rprint(REPL_HELP); return; }
  const cand = [...REPL_HELP.map(l=>l[1].split(/\s+/)[0]), ...secs];
  const sug = cand.find(x => x.startsWith(c)) || cand.find(x => x.includes(c));
  rprint([["r-err",`sh: ${cmd}: command not found`]]
    .concat(sug ? [["r-dim",`did you mean '${sug}'?`]] : []));
}

repl.addEventListener("keydown", e => {
  if(e.key === "Enter"){ replRun(repl.value); repl.value = ""; }
  else if(e.key === "ArrowUp"){ if(histIdx > 0){ repl.value = hist[--histIdx]; } e.preventDefault(); }
  else if(e.key === "ArrowDown"){
    histIdx = Math.min(histIdx+1, hist.length);
    repl.value = hist[histIdx] ?? "";
    e.preventDefault();
  }
  else if(e.key === "Tab"){
    e.preventDefault();
    const v = repl.value, parts = v.split(/\s+/);
    if(parts.length <= 1){
      const names = ["help","cd","ls","cat","open","grep","doctor","install","version","pwd","history","clear",":q",...SECTIONS];
      const m = names.filter(n => n.startsWith(v));
      if(m.length === 1) repl.value = m[0] + " ";
      else if(m.length) rprint([["r-dim", m.join("   ")]]);
    } else if(parts[0] === "cd"){
      const m = SECTIONS.filter(s => s.startsWith(parts[1] || ""));
      if(m.length === 1) repl.value = `cd ${m[0]}`;
      else if(m.length) rprint([["r-dim", m.join("   ")]]);
    } else if(["cat","open"].includes(parts[0])){
      const q = parts[1] || "";
      const m = (D.skills||[]).map(s => s.dir).filter(n => n.startsWith(q));
      if(m.length === 1) repl.value = `${parts[0]} ${m[0]}`;
      else if(m.length && m.length <= 12) rprint([["r-dim", m.join("   ")]]);
    }
  }
});

/* ---------------- keys ---------------- */
document.addEventListener("keydown", e => {
  const typing = /input|textarea/i.test(e.target.tagName);
  if((e.key === "/" && !typing) || (e.ctrlKey && e.key.toLowerCase() === "k")){
    e.preventDefault(); palShow(); return;
  }
  if(e.key === "Escape"){ pal.hidden = true; closeModal(); return; }
  if(typing || !modal.hidden || !pal.hidden) return;
  if(e.key === "q") closeModal();
  const n = +e.key;
  if(n >= 1 && n <= SECTIONS.length){ go(SECTIONS[n-1]); return; }
  // type-anywhere: printable chars drop into the repl like a real terminal
  if(e.key.length === 1 && !e.ctrlKey && !e.altKey && !e.metaKey
     && /[a-zA-Z ]/.test(e.key)){
    repl.focus();
    repl.value += e.key;
    e.preventDefault();
  }
});

/* ---------------- init ---------------- */
$("#tb-version").innerHTML = `v<b>${esc(D.version||"?")}</b> · ${D.counts?.skills??"?"} skills · ${D.counts?.agents??"?"} agents`;
go(location.hash.slice(1) || "boot");
boot();
})();
