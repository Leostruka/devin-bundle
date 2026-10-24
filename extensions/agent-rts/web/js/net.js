/* net.js - WS client: hello -> snapshot -> upsert/tick/fx/alert frames.
   On upsert: debounced GET /snapshot rebuild (rtsd client parity). */
export class Net {
  constructor() {
    this.handlers = {};
    this.ws = null;
    this._refreshT = null;
    this._retry = 0;
  }
  on(type, fn) { (this.handlers[type] ||= []).push(fn); }
  _emit(type, m) { (this.handlers[type] || []).forEach(f => f(m)); }

  connect() {
    const proto = location.protocol === "https:" ? "wss" : "ws";
    const tok = new URLSearchParams(location.search).get("token");
    const ws = new WebSocket(`${proto}://${location.host}/ws` +
                             (tok ? `?token=${tok}` : ""));
    this.ws = ws;
    ws.onopen = () => { this._retry = 0; this._emit("open", {}); };
    ws.onclose = () => {
      this._emit("close", {});
      setTimeout(() => this.connect(), Math.min(8000, 800 * ++this._retry));
    };
    ws.onerror = () => ws.close();
    ws.onmessage = (e) => {
      let m;
      try { m = JSON.parse(e.data); } catch { return; }
      if (m.type === "upsert") {         // world changed -> cheap refetch
        if (m.feed) this._emit("feed", m);
        if (m.hint) this._emit("hint", m);
        this._scheduleRefresh();
      }
      this._emit(m.type, m);
    };
  }

  _scheduleRefresh() {
    if (this._refreshT) return;
    this._refreshT = setTimeout(() => {
      this._refreshT = null;
      this.snapshot();
    }, 350);
  }

  async snapshot() {
    const tok = new URLSearchParams(location.search).get("token");
    const r = await fetch("/snapshot" +
      (tok ? `?token=${tok}` : ""),
      { headers: tok ? { "X-RTS-Token": tok } : {} });
    if (r.ok) this._emit("snapshot", await r.json());
  }

  async post(path, body) {
    const tok = new URLSearchParams(location.search).get("token");
    const r = await fetch(path + (tok ? `?token=${tok}` : ""), {
      method: "POST",
      headers: { "Content-Type": "application/json",
                 ...(tok ? { "X-RTS-Token": tok } : {}) },
      body: JSON.stringify(body) });
    let j = {};
    try { j = await r.json(); } catch { }
    return { code: r.status, body: j };
  }

  send(o) {
    if (this.ws && this.ws.readyState === 1) this.ws.send(JSON.stringify(o));
  }
}
