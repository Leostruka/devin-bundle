/* fx.js - server fx/alert/decision frames -> scene + HUD effects. */
export class FX {
  constructor(particles, audio, hud) {
    this.p = particles; this.audio = audio; this.hud = hud;
  }
  handle(m) {
    if (m.fx === "bubble") {
      this.p.bubble(m.x, m.y, m.color, m.label);
      this.audio?.blip(m.color);
    } else if (m.fx === "meteor") {
      this.p.meteor(m.x, m.y);
      this.audio?.meteor();
    } else if (m.fx === "gate_flash") {
      this.p.spark(m.x, 2.4, m.y, 14);
      this.audio?.alert();
    } else if (m.fx === "confetti") {
      this.p.confetti(m.x, m.y);
    } else if (m.fx === "smoke") {
      this.p.puff(m.x, m.y);
    }
  }
  alert(m) {
    this.hud?.alert(m.level, m.code, m.msg, m.x, m.y);
    if (m.level === "crit") this.audio?.alert();
  }
}
