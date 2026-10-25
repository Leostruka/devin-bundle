/* audio.js - procedural WebAudio foley (zero files).
   Theme-aware: medieval anvil/horn vs office keys/ding. */
export class Audio3 {
  constructor() {
    this.ctx = null;
    this.theme = "medieval";
    this.enabled = true;
    this._wind = null;             // ambient soundscape nodes
  }
  _ensure() {
    if (!this.ctx && this.enabled) {
      try { this.ctx = new (window.AudioContext ||
                             window.webkitAudioContext)(); }
      catch { this.enabled = false; }
    }
    return this.ctx;
  }
  resume() { this._ensure()?.resume?.(); this.ambient(); }

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
  _noise(dur, freq, gain = 0.05, when = 0, q = 1.2, ftype = "bandpass") {
    const c = this._ensure(); if (!c) return;
    const t = c.currentTime + when;
    const n = Math.max(1, c.sampleRate * dur);
    const buf = c.createBuffer(1, n, c.sampleRate);
    const d = buf.getChannelData(0);
    for (let i = 0; i < n; i++) d[i] = (Math.random() * 2 - 1) *
      (1 - i / n);
    const s = c.createBufferSource(); s.buffer = buf;
    const f = c.createBiquadFilter(); f.type = ftype;
    f.frequency.value = freq; f.Q.value = q;
    const g = c.createGain(); g.gain.value = gain;
    s.connect(f).connect(g).connect(c.destination);
    s.start(t);
  }
  /* FM metallic hit: carrier `fc` modulated by `fm`, index decays. */
  _fm(fc, fm, dur, gain = 0.07, when = 0) {
    const c = this._ensure(); if (!c) return;
    const t = c.currentTime + when;
    const car = c.createOscillator(), mod = c.createOscillator();
    const idx = c.createGain(), g = c.createGain();
    mod.frequency.value = fm;
    idx.gain.setValueAtTime(fc * 1.4, t);
    idx.gain.exponentialRampToValueAtTime(0.01, t + dur);
    mod.connect(idx).connect(car.frequency);
    car.frequency.value = fc;
    g.gain.setValueAtTime(gain, t);
    g.gain.exponentialRampToValueAtTime(0.0001, t + dur);
    car.connect(g).connect(c.destination);
    mod.start(t); car.start(t);
    mod.stop(t + dur + 0.02); car.stop(t + dur + 0.02);
  }

  /* ---- ambient wind soundscape (looping noise + gust envelope) ---- */
  ambient() {
    const c = this._ensure(); if (!c || this._wind) return;
    const n = c.sampleRate * 2;                  // 2s loop
    const buf = c.createBuffer(1, n, c.sampleRate);
    const d = buf.getChannelData(0);
    let last = 0;                                // brown-ish noise
    for (let i = 0; i < n; i++) {
      last = (last + (Math.random() * 2 - 1) * 0.02) * 0.998;
      d[i] = last * 3.2;
    }
    const s = c.createBufferSource();
    s.buffer = buf; s.loop = true;
    const f = c.createBiquadFilter();            // wind bandpass
    f.type = "bandpass"; f.frequency.value = 320; f.Q.value = 1.8;
    const g = c.createGain(); g.gain.value = 0;
    const lfo = c.createOscillator();            // gust envelope ~0.07Hz
    const lg = c.createGain();
    lfo.frequency.value = 0.07; lg.gain.value = 0.018;
    lfo.connect(lg).connect(g.gain);
    g.gain.value = 0.022;
    s.connect(f).connect(g).connect(c.destination);
    s.start(); lfo.start();
    this._wind = { s, f, g, lfo };
    this._pad();
  }
  /* WC3 ambient music layer: quiet detuned triad drone under the foley,
     slow filter sweep so it breathes instead of looping audibly */
  _pad() {
    const c = this._ensure(); if (!c || this._padN) return;
    const f = c.createBiquadFilter();
    f.type = "lowpass"; f.frequency.value = 380; f.Q.value = 0.6;
    const g = c.createGain(); g.gain.value = 0;
    const notes = this.theme === "office" ? [110, 165, 220.5]
                                          : [98, 146.8, 196.2];
    const oscs = notes.map((fr, i) => {
      const o = c.createOscillator();
      o.type = i === 2 ? "triangle" : "sine";
      o.frequency.value = fr;
      o.detune.value = (i - 1) * 4;
      o.connect(f); o.start();
      return o;
    });
    const lfo = c.createOscillator(), lg = c.createGain();
    lfo.frequency.value = 0.05; lg.gain.value = 90;
    lfo.connect(lg).connect(f.frequency); lfo.start();
    g.gain.linearRampToValueAtTime(0.014, c.currentTime + 6);
    f.connect(g).connect(c.destination);
    this._padN = { oscs, f, g, lfo };
  }
  setWind(vKph = 12) {                           // live gust cutoff
    if (this._wind) this._wind.f.frequency.value = 180 + 14 * vKph;
  }
  stopAmbient() {
    if (this._wind) { try { this._wind.s.stop(); this._wind.lfo.stop(); }
                      catch {} this._wind = null; }
    if (this._padN) {
      try { this._padN.oscs.forEach(o => o.stop());
            this._padN.lfo.stop(); } catch {}
      this._padN = null;
    }
  }
  levelup() {                                  // WC3 rising fanfare
    if (this.theme === "office") return this.bell();
    [523.25, 659.25, 784, 1046.5].forEach((f, i) =>
      this._tone(f, f, 0.35 - i * 0.04, "triangle", 0.05, i * 0.09));
    this._noise(0.5, 5200, 0.025, 0.3, 0.6, "highpass");
  }
  toggle() {
    this.enabled = !this.enabled;
    if (!this.enabled) this.stopAmbient();
    return this.enabled;
  }

  /* ---- theme verbs ---- */
  clash() {                                      // sword strike
    if (this.theme === "office") return this.keys();
    this._noise(0.04, 2400, 0.09);               // bandpass burst
    for (const [f, w] of [[780, 0], [1240, 0.004], [1960, 0.008]])
      this._tone(f * (1 + (Math.random() - 0.5) * 0.03), f * 0.86,
                 0.14, "sine", 0.028, w);
  }
  anvil() {                                      // runeforge clang
    if (this.theme === "office") return this.bell();
    this._fm(587, 830, 0.35, 0.09);
    this._noise(0.05, 3200, 0.05);
  }
  coin() {                                       // gold gather
    this._tone(1760, 1760, 0.09, "sine", 0.04);
    this._tone(2637, 2637, 0.16, "sine", 0.035, 0.07);
  }
  keys() {                                       // mechanical keyswitch
    this._noise(0.018, 3200, 0.07, 0, 2.5, "highpass");
    this._tone(190, 120, 0.03, "square", 0.02);
  }
  bell() {                                       // desk bell ding
    this._tone(2093, 2093, 0.5, "sine", 0.05);
    this._tone(3136, 3136, 0.28, "sine", 0.02);
  }
  espresso() {                                   // steam hiss
    this._noise(0.5, 5200, 0.045, 0, 0.8, "highpass");
  }
  printer() {                                    // stepper whir
    for (let i = 0; i < 5; i++)
      this._tone(420, 380, 0.05, "sawtooth", 0.018, i * 0.09);
  }
  glug() {                                       // water-cooler bubble
    for (let i = 0; i < 3; i++)
      this._tone(300 - i * 60, 420, 0.08, "sine", 0.03, i * 0.12);
  }

  /* tool bubble -> foley (bid/tool come from server fx frames) */
  toolFx(bid, tool) {
    if (bid === "runeforge") return this.anvil();
    if (bid === "market" || bid === "bank") return this.coin();
    if (this.theme === "office") {
      if (/exec|write|edit|notebook/.test(tool)) return this.keys();
      if (/ask_user|decision/.test(tool)) return this.bell();
      if (/todo|plan/.test(tool)) return this.printer();
      return this.keys();
    }
    if (/exec|write|edit|notebook/.test(tool)) return this.clash();
    if (/web_search|webfetch|read|grep|find/.test(tool)) return this.coin();
    this.clash();
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
  die() {                                      // WC3 death thud
    this._tone(90, 38, 0.4, "sine", 0.08);
    this._noise(0.22, 160, 0.05, 0, 0.7, "lowpass");
  }
  deny() {                                     // WC3 invalid-command buzz
    this._tone(160, 70, 0.16, "sawtooth", 0.055);
    this._tone(160, 70, 0.16, "sawtooth", 0.055, 0.2);
  }
  warn() {                                     // WC3 under-attack horn
    this._tone(196, 147, 0.5, "sawtooth", 0.05);
    this._tone(98, 74, 0.5, "sine", 0.06);
  }
  /* WC3 unit barks: select = querying grunt, order = acknowledge.
     Procedural "voice": formant bandpass burst over a pitched grunt;
     pitch maps the unit class (Knight deep, Far Seer airy). */
  bark(cls, kind = "select") {
    if (this.theme === "office") return this.keys();
    const base = { Knight: 140, Commander: 120, Footman: 190,
                   "Far Seer": 300 }[cls] || 220;
    if (kind === "order") {                    // short rising ack
      this._tone(base * 0.9, base * 1.3, 0.09, "sawtooth", 0.028);
      this._noise(0.07, base * 6, 0.02, 0, 3);
    } else {                                   // "yes?" grunt
      this._tone(base, base * 0.75, 0.13, "sawtooth", 0.034);
      this._noise(0.1, base * 8, 0.018, 0.02, 4);
    }
  }
}
