/* audio.js - procedural WebAudio foley (zero files).
   Theme-aware: medieval anvil/horn vs office keys/ding. */
export class Audio3 {
  constructor() {
    this.ctx = null;
    this.theme = "medieval";
    this.enabled = true;
  }
  _ensure() {
    if (!this.ctx && this.enabled) {
      try { this.ctx = new (window.AudioContext ||
                             window.webkitAudioContext)(); }
      catch { this.enabled = false; }
    }
    return this.ctx;
  }
  resume() { this._ensure()?.resume?.(); }
  _tone(f0, f1, dur, type = "sine", gain = 0.06, when = 0) {
    const c = this._ensure(); if (!c) return;
    const t = c.currentTime + when;
    const o = c.createOscillator(), g = c.createGain();
    o.type = type;
    o.frequency.setValueAtTime(f0, t);
    o.frequency.exponentialRampToValueAtTime(Math.max(30, f1), t + dur);
    g.gain.setValueAtTime(gain, t);
    g.gain.exponentialRampToValueAtTime(0.0001, t + dur);
    o.connect(g).connect(c.destination);
    o.start(t); o.stop(t + dur + 0.02);
  }
  _noise(dur, freq, gain = 0.05, when = 0) {
    const c = this._ensure(); if (!c) return;
    const t = c.currentTime + when;
    const n = c.sampleRate * dur;
    const buf = c.createBuffer(1, n, c.sampleRate);
    const d = buf.getChannelData(0);
    for (let i = 0; i < n; i++) d[i] = (Math.random() * 2 - 1) *
      (1 - i / n);
    const s = c.createBufferSource(); s.buffer = buf;
    const f = c.createBiquadFilter(); f.type = "bandpass";
    f.frequency.value = freq; f.Q.value = 1.2;
    const g = c.createGain(); g.gain.value = gain;
    s.connect(f).connect(g).connect(c.destination);
    s.start(t);
  }
  blip(color) {
    if (this.theme === "office")
      return this._tone(2200, 1700, 0.05, "square", 0.015);
    const f = { green: 660, blue: 520, purple: 760, red: 300,
                gold: 880 }[color] || 520;
    this._tone(f, f * 1.4, 0.09, "triangle", 0.035);
  }
  order() {
    if (this.theme === "office") this._tone(1200, 900, 0.07, "square", 0.03);
    else { this._tone(180, 120, 0.16, "sawtooth", 0.05);
           this._noise(0.08, 900, 0.03); }
  }
  alert() {
    if (this.theme === "office") {
      this._tone(880, 880, 0.09, "square", 0.05);
      this._tone(880, 880, 0.09, "square", 0.05, 0.14);
    } else {
      this._noise(0.4, 120, 0.1);
      this._tone(90, 55, 0.5, "sawtooth", 0.07);
    }
  }
  meteor() {
    this._noise(1.1, 200, 0.12);
    this._tone(300, 40, 1.1, "sawtooth", 0.08);
  }
  decide() { this._tone(440, 330, 0.25, "triangle", 0.06); }
}
