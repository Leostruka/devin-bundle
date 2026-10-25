/* scene.js - WebGL2 PBR pipeline: renderer, procedural IBL, sun+hemi,
   PCFSoft shadows, EffectComposer (RenderPass -> SSAO -> TiltShift ->
   Output), canvas-baked terrain with fog+mark overlay. */
import * as THREE from "three";
import { EffectComposer } from "three/addons/postprocessing/EffectComposer.js";
import { RenderPass } from "three/addons/postprocessing/RenderPass.js";
import { ShaderPass } from "three/addons/postprocessing/ShaderPass.js";
import { OutputPass } from "three/addons/postprocessing/OutputPass.js";
import { themeOf, noiseCanvas, normalFromHeight } from "./themes.js";

const MAP_W = 72, MAP_H = 54;
let SSAOPass = null;   // optional addon (vendored if present)
try {
  ({ SSAOPass } = await import("three/addons/postprocessing/SSAOPass.js"));
} catch { /* vendored addon absent: contact AO still gives depth */ }

/* Tilt-shift: banded DOF blur around the screen-space focus line;
   the maquete/miniature look. */
const TiltShiftShader = {
  uniforms: {
    tDiffuse: { value: null },
    uFocus: { value: 0.52 },      // screen-y of sharp band
    uBand: { value: 0.28 },       // half-height of sharp band
    uMaxBlur: { value: 8.0 },
    uAspect: { value: 1.0 },
  },
  vertexShader: `varying vec2 vUv;
    void main(){ vUv=uv; gl_Position=projectionMatrix*modelViewMatrix*vec4(position,1.); }`,
  fragmentShader: `uniform sampler2D tDiffuse; uniform float uFocus,uBand,uMaxBlur,uAspect;
    varying vec2 vUv;
    void main(){
      float d=abs(vUv.y-uFocus)-uBand;
      float b=clamp(d/uBand,0.,1.)*uMaxBlur;
      vec4 acc=vec4(0.); float n=0.;
      for(int i=-4;i<=4;i++){
        vec2 off=vec2(float(i)/uAspect,float(i))*b*0.0018;
        acc+=texture2D(tDiffuse,vUv+off); n+=1.;
      }
      gl_FragColor=acc/n;
    }`,
};

export class Scene3D {
  constructor(canvas) {
    this.canvas = canvas;
    this.renderer = new THREE.WebGLRenderer({ canvas, antialias: true });
    this.renderer.setPixelRatio(Math.min(devicePixelRatio, 2));
    this.renderer.setSize(innerWidth, innerHeight);
    this.renderer.shadowMap.enabled = true;
    this.renderer.shadowMap.type = THREE.PCFSoftShadowMap;
    this.renderer.toneMapping = THREE.ACESFilmicToneMapping;
    this.renderer.toneMappingExposure = 1.05;

    this.scene = new THREE.Scene();
    this.camera = new THREE.PerspectiveCamera(
      40, innerWidth / innerHeight, 0.5, 500);

    this.sun = new THREE.DirectionalLight(0xffffff, 2.4);
    this.sun.castShadow = true;
    this.sun.shadow.mapSize.set(2048, 2048);
    Object.assign(this.sun.shadow.camera,
      { left: -70, right: 70, top: 70, bottom: -70, far: 220 });
    this.sun.shadow.camera.updateProjectionMatrix();
    this.sun.shadow.bias = -0.0004;
    this.scene.add(this.sun);
    this.hemi = new THREE.HemisphereLight(0xffffff, 0x222222, 0.6);
    this.scene.add(this.hemi);
    this.accent = new THREE.PointLight(0xffb347, 30, 30);
    this.accent.position.set(36, 6, 27);
    this.scene.add(this.accent);

    this.world = new THREE.Group();       // entities (units/buildings)
    this.fx = new THREE.Group();          // particles/effects
    this.scene.add(this.world, this.fx);

    /* post chain */
    this.composer = new EffectComposer(this.renderer);
    this.composer.addPass(new RenderPass(this.scene, this.camera));
    this.ssao = null;
    if (SSAOPass) {
      this.ssao = new SSAOPass(this.scene, this.camera,
                               innerWidth, innerHeight);
      this.ssao.kernelRadius = 0.7;
      this.ssao.minDistance = 0.001;
      this.ssao.maxDistance = 0.08;
      this.composer.addPass(this.ssao);
    }
    this.tilt = new ShaderPass(TiltShiftShader);
    this.composer.addPass(this.tilt);
    this.composer.addPass(new OutputPass());

    this._envRT = null;
    this._terrain = null;
    this._terrainCv = null;
    this.setTheme("medieval");
    addEventListener("resize", () => this.resize());
  }

  resize() {
    this.camera.aspect = innerWidth / innerHeight;
    this.camera.updateProjectionMatrix();
    this.renderer.setSize(innerWidth, innerHeight);
    this.composer.setSize(innerWidth, innerHeight);
    this.tilt.uniforms.uAspect.value = innerWidth / innerHeight;
  }

  /* Procedural IBL: render a tiny gradient-sky scene through PMREM so
     Standard/Physical materials get believable reflections. */
  _buildEnv(theme) {
    if (this._envRT) this._envRT.dispose();
    const env = new THREE.Scene();
    const geo = new THREE.SphereGeometry(50, 16, 12);
    const mat = new THREE.ShaderMaterial({
      side: THREE.BackSide,
      uniforms: { top: { value: new THREE.Color(theme.sky.top) },
                  hor: { value: new THREE.Color(theme.sky.horizon) } },
      vertexShader: `varying vec3 vP; void main(){ vP=position;
        gl_Position=projectionMatrix*modelViewMatrix*vec4(position,1.);}`,
      fragmentShader: `uniform vec3 top,hor; varying vec3 vP;
        void main(){ float k=clamp(vP.y/50.*.5+.5,0.,1.);
        gl_FragColor=vec4(mix(hor,top,k),1.);}`,
    });
    env.add(new THREE.Mesh(geo, mat));
    const pm = new THREE.PMREMGenerator(this.renderer);
    this._envRT = pm.fromScene(env, 0.04);
    this.scene.environment = this._envRT.texture;
    pm.dispose();
  }

  setTheme(name) {
    this.theme = themeOf(name);
    const t = this.theme;
    this.scene.background = new THREE.Color(t.sky.top);
    this.scene.fog = new THREE.Fog(t.sky.horizon, 90, 220);
    this.sun.color.set(t.sun.color);
    this.sun.intensity = t.sun.intensity;
    this.sun.position.set(...t.sun.pos);
    this.hemi.color.set(t.hemi.sky);
    this.hemi.groundColor.set(t.hemi.ground);
    this.hemi.intensity = t.hemi.intensity;
    this.accent.color.set(t.building.glow);
    /* base values for the day/night lerp (WC3: world darkens at night,
       hero/building glow reads stronger) */
    this._base = {
      sunColor: new THREE.Color(t.sun.color), sunI: t.sun.intensity,
      sunPos: t.sun.pos.slice(), moonColor: new THREE.Color(0x8fa8e8),
      hemiI: t.hemi.intensity, skyTop: new THREE.Color(t.sky.top),
      skyHor: new THREE.Color(t.sky.horizon),
      night: new THREE.Color(t.sky.night ?? 0x0a1020),
    };
    if (this._dayPhase !== undefined) this.setDayPhase(this._dayPhase);
    this._buildEnv(t);
    this._buildGround(t);
    if (this._mapData) this.bakeTerrain(this._mapData);
  }

  /* day \in [0,1]: 1 = noon sun, 0 = deep night moonlight. */
  setDayPhase(day) {
    this._dayPhase = day;
    const b = this._base; if (!b) return;
    const night = 1 - day;
    this.sun.color.copy(b.sunColor).lerp(b.moonColor, night);
    this.sun.intensity = b.sunI * (0.22 + 0.78 * day);
    this.sun.position.set(b.sunPos[0],
      Math.max(8, b.sunPos[1] * (0.25 + 0.75 * day)), b.sunPos[2]);
    this.hemi.intensity = b.hemiI * (0.42 + 0.58 * day);
    this.scene.background.copy(b.skyTop).lerp(b.night, night * 0.85);
    this.scene.fog.color.copy(b.skyHor).lerp(b.night, night * 0.7);
    this.accent.intensity = 30 * (0.45 + night * 0.9);
    this.renderer.toneMappingExposure = 1.05 * (0.88 + 0.12 * day);
    /* WC3 sky disc: visible sun by day, pale moon at night. A billboarded
       circle hanging over the sun's direction vector */
    if (!this._sunDisc) {
      const cv = document.createElement("canvas");
      cv.width = cv.height = 64;
      const c = cv.getContext("2d");
      const rad = c.createRadialGradient(32, 32, 4, 32, 32, 30);
      rad.addColorStop(0, "rgba(255,255,255,1)");
      rad.addColorStop(0.55, "rgba(255,255,255,.9)");
      rad.addColorStop(1, "rgba(255,255,255,0)");
      c.fillStyle = rad; c.fillRect(0, 0, 64, 64);
      const tex = new THREE.CanvasTexture(cv);
      this._sunDisc = new THREE.Sprite(new THREE.SpriteMaterial({
        map: tex, transparent: true, depthWrite: false, fog: false }));
      this._sunDisc.scale.setScalar(26);
      this.scene.add(this._sunDisc);
    }
    const d = this.sun.position.clone().normalize();
    this._sunDisc.position.set(d.x * 150 + 36,
      26 + day * 55, d.z * 150 + 27);
    this._sunDisc.material.color.setHex(day > 0.35 ? 0xfff2c0
      : 0xbccdf2);
    this._sunDisc.material.opacity = 0.35 + day * 0.55;
  }

  /* Ground: displaced-ish plane with procedural PBR maps. Terrain art
     (regions, marks, fog) bakes into a canvas -> albedo texture. */
  _buildGround(t) {
    if (this._ground) { this.scene.remove(this._ground); }
    const albedo = noiseCanvas(256, "#ffffff", 0.35, 14);
    const nrm = normalFromHeight(albedo, 1.4);
    const rough = noiseCanvas(128, "#b4b4b4", 0.5, 9);
    const tex = new THREE.CanvasTexture(albedo);
    tex.wrapS = tex.wrapT = THREE.RepeatWrapping;
    tex.repeat.set(24, 18);
    const ntex = new THREE.CanvasTexture(nrm);
    ntex.wrapS = ntex.wrapT = THREE.RepeatWrapping;
    ntex.repeat.set(24, 18);
    const rtex = new THREE.CanvasTexture(rough);
    rtex.wrapS = rtex.wrapT = THREE.RepeatWrapping;
    rtex.repeat.set(16, 12);
    this._groundMat = new THREE.MeshStandardMaterial({
      map: tex, normalMap: ntex, roughnessMap: rtex,
      roughness: 1.0, metalness: 0.0 });
    this._terrainCv = document.createElement("canvas");
    this._terrainCv.width = 1024;
    this._terrainCv.height = 768;
    this._terrainTex = new THREE.CanvasTexture(this._terrainCv);
    this._terrainTex.colorSpace = THREE.SRGBColorSpace;
    const g = new THREE.Mesh(
      new THREE.PlaneGeometry(MAP_W + 6, MAP_H + 6, 1, 1),
      new THREE.MeshStandardMaterial({
        map: this._terrainTex, roughness: 0.94, metalness: 0.0,
        normalMap: ntex, normalScale: new THREE.Vector2(0.35, 0.35) }));
    g.rotation.x = -Math.PI / 2;
    g.position.set(MAP_W / 2, 0, MAP_H / 2);
    g.receiveShadow = true;
    g.name = "ground";
    this._ground = g;
    this.scene.add(g);
    /* WC3 map edge: the world ends in darkness, not open sky: a huge
       near-black plane under/around the terrain kills the void */
    const void_ = new THREE.Mesh(
      new THREE.PlaneGeometry(MAP_W * 4, MAP_H * 4),
      new THREE.MeshStandardMaterial({ color: 0x05080b,
        roughness: 1, metalness: 0 }));
    void_.rotation.x = -Math.PI / 2;
    void_.position.set(MAP_W / 2, -0.06, MAP_H / 2);
    this.scene.add(void_);
    /* fog overlay lives on its own plane above the terrain so army vision
       (units carrying sight, WC3) can repaint it cheaply without re-baking
       the whole albedo */
    this._fogCv = document.createElement("canvas");
    this._fogTex = new THREE.CanvasTexture(this._fogCv);
    const fp = new THREE.Mesh(
      new THREE.PlaneGeometry(MAP_W + 1.2, MAP_H + 1.2, 1, 1),
      new THREE.MeshBasicMaterial({ map: this._fogTex, transparent: true,
        depthWrite: false, fog: false }));
    fp.rotation.x = -Math.PI / 2;
    fp.position.set(MAP_W / 2, 0.03, MAP_H / 2);
    fp.name = "fogshroud";
    fp.renderOrder = 1;
    this._fogMesh = fp;
    this.scene.add(fp);
  }

  /* Repaint the 1px/tile fog canvas; bilinear upscale gives soft edges.
     army = Set of tile idx forced to live vision (own units carry sight). */
  paintFog(map, army) {
    this._army = army;
    const fc = this._fogCv;
    fc.width = map.w; fc.height = map.h;
    const fctx = fc.getContext("2d");
    for (let y = 0; y < map.h; y++)
      for (let x = 0; x < map.w; x++) {
        const i = y * map.w + x;
        const f = (map.reveal?.has(i) || army?.has(i)) ? 2
                : (map.fog || [])[i];
        fctx.fillStyle = f === 2 ? "rgba(4,8,12,0)" :
          f === 1 ? "rgba(12,20,30,.30)" : "rgba(2,5,9,.9)";
        fctx.fillRect(x, y, 1, 1);
      }
    this._fogTex.needsUpdate = true;
  }

  /* Bake region fills + marks + fog into the terrain albedo canvas.
     map = {w,h,tile_region,fog,mark,regions,pois}. */
  bakeTerrain(map) {
    this._mapData = map;
    const t = this.theme, cv = this._terrainCv, ctx = cv.getContext("2d");
    const W = cv.width, H = cv.height;
    const tw = W / map.w, th = H / map.h;
    const regs = map.tile_region || [];
    for (let y = 0; y < map.h; y++)
      for (let x = 0; x < map.w; x++) {
        const i = y * map.w + x;
        const rid = (map.regions || [])[regs[i]] || "_";
        ctx.fillStyle = t.terrain[rid] || t.terrain._;
        ctx.fillRect(x * tw, y * th, tw + 0.5, th + 0.5);
      }
    /* organic noise wash so tiles don't read as a grid */
    const img = ctx.getImageData(0, 0, W, H);
    for (let i = 0; i < img.data.length; i += 4) {
      const n = (Math.sin(i * 0.618) * 0.5 + 0.5) * 0.10 + 0.95;
      img.data[i] *= n; img.data[i + 1] *= n; img.data[i + 2] *= n;
    }
    ctx.putImageData(img, 0, 0);
    /* marks: plots outlined, gold diamonds, quest !, camp flags,
       contested hatch — gated by fog so map data never leaks into
       never-seen shroud (matches the instanced decals rule) */
    for (let y = 0; y < map.h; y++)
      for (let x = 0; x < map.w; x++) {
        const mk = (map.mark || [])[y * map.w + x];
        if (!mk) continue;
        const mi = y * map.w + x;
        if (!(((map.fog || [])[mi] ?? 0) >= 1 || map.reveal?.has(mi)))
          continue;
        const cx = x * tw, cy = y * th;
        if (mk === 1) {           // plot
          ctx.strokeStyle = "rgba(255,255,255,.25)";
          ctx.strokeRect(cx + 1, cy + 1, tw - 2, th - 2);
        } else if (mk === 2) {    // contested
          ctx.fillStyle = "rgba(200,60,40,.35)";
          ctx.fillRect(cx, cy, tw, th);
        } else if (mk === 4) {    // gold node
          ctx.fillStyle = "rgba(255,215,80,.5)";
          ctx.beginPath();
          ctx.arc(cx + tw / 2, cy + th / 2, tw * 0.35, 0, 7);
          ctx.fill();
        }
      }
    /* canonical explored-set signature (army vision is overlay-only:
       temporary sight must not grow terrain furniture or leak marks) */
    let sig = 0;
    for (let i = 0; i < map.w * map.h; i++) {
      const f = map.reveal?.has(i) ? 2 : (map.fog || [])[i];
      if (f >= 1) sig = (sig + i + 1) | 0;
    }
    this._terrainTex.needsUpdate = true;
    this.paintFog(map, this._army);
    /* explored set changed -> terrain furniture must be rebaked so
       newly-revealed land grows trees/marks */
    if (sig !== this._fogSig) {
      this._fogSig = sig;
      this._doodadsBuilt = this._decalsBuilt = false;
    }
    this._doodads(map);
    this._decals(map);
  }

  /* WC3 territory decals: contested tiles get pulsing red ground quads,
     gold nodes get piled nuggets; semantic map marks as geometry */
  _decals(map) {
    if (this._decalsBuilt) return;
    this._decalsBuilt = true;
    if (this._contMesh) { this.scene.remove(this._contMesh);
                          this._contMesh = null; }
    if (this._goldMesh) { this.scene.remove(this._goldMesh);
                          this._goldMesh = null; }
    const mark = map.mark || [], fogA = map.fog || [];
    const cont = [], gold = [];
    for (let y = 0; y < map.h; y++)
      for (let x = 0; x < map.w; x++) {
        const i = y * map.w + x;
        /* marks never leak into the unexplored shroud */
        if (!((fogA[i] ?? 0) >= 1 || map.reveal?.has(i))) continue;
        const mk = mark[i];
        if (mk === 2) cont.push([x, y]);
        else if (mk === 4) gold.push([x, y]);
      }
    if (cont.length) {
      const g = new THREE.PlaneGeometry(1, 1);
      this._contMesh = new THREE.InstancedMesh(g,
        new THREE.MeshBasicMaterial({ color: 0xc03024, transparent: true,
          opacity: 0.16, depthWrite: false }), cont.length);
      const m4 = new THREE.Matrix4(), q = new THREE.Quaternion()
        .setFromAxisAngle(new THREE.Vector3(1, 0, 0), -Math.PI / 2);
      cont.forEach((p, i) => this._contMesh.setMatrixAt(i,
        m4.compose(new THREE.Vector3(p[0] + 0.5, 0.055, p[1] + 0.5), q,
                   new THREE.Vector3(1, 1, 1))));
      this._contMesh.frustumCulled = false;
      this.scene.add(this._contMesh);
    }
    if (gold.length) {
      const g = new THREE.IcosahedronGeometry(0.16);
      const im = new THREE.InstancedMesh(g,
        new THREE.MeshStandardMaterial({ color: 0xe8c86a,
          metalness: 0.85, roughness: 0.3 }), gold.length * 3);
      const m4 = new THREE.Matrix4(), q = new THREE.Quaternion(),
            v = new THREE.Vector3(), s = new THREE.Vector3(1, 1, 1);
      gold.forEach((p, i) => {
        for (let k = 0; k < 3; k++) {
          v.set(p[0] + 0.3 + (k * 0.18), 0.1 + (k === 2 ? 0.14 : 0),
                p[1] + 0.4 + (k === 1 ? 0.2 : 0));
          q.setFromEuler(new THREE.Euler(k * 0.9, k * 1.7, 0.5));
          im.setMatrixAt(i * 3 + k, m4.compose(v, q, s));
        }
      });
      im.castShadow = true;
      this._goldMesh = im;
      this.scene.add(im);
    }
  }

  /* contested tiles breathe (called per frame) */
  stepDecals(t) {
    if (this._contMesh)
      this._contMesh.material.opacity = 0.12 + Math.sin(t * 3.2) * 0.08;
  }

  /* WC3 ambient weather: huge soft cloud shadows crawl across the
     terrain with the wind (darkens tiles, sells scale + motion) */
  clouds(map) {
    if (this._clouds) return this._clouds;
    this._clouds = [];
    const cv = document.createElement("canvas");
    cv.width = cv.height = 128;
    const c = cv.getContext("2d");
    const g = c.createRadialGradient(64, 64, 8, 64, 64, 62);
    g.addColorStop(0, "rgba(8,14,10,.42)");
    g.addColorStop(1, "rgba(8,14,10,0)");
    c.fillStyle = g; c.fillRect(0, 0, 128, 128);
    const tex = new THREE.CanvasTexture(cv);
    for (let i = 0; i < 5; i++) {
      const m = new THREE.Mesh(
        new THREE.PlaneGeometry(14 + i * 4, 10 + i * 3),
        new THREE.MeshBasicMaterial({ map: tex, transparent: true,
          depthWrite: false, opacity: 0.85 }));
      m.rotation.x = -Math.PI / 2;
      m.position.set(Math.random() * (map?.w || 72), 0.09,
                     Math.random() * (map?.h || 54));
      m.renderOrder = 2;
      this.scene.add(m);
      this._clouds.push(m);
    }
    return this._clouds;
  }

  /* WC3 critters: tiny neutral wanderers (sheep/deer) that pace slowly
     around revealed ground. Pure ambience, never canonical state */
  critters(map) {
    if (this._critters) return;
    this._critters = [];
    const body = new THREE.SphereGeometry(0.14, 8, 6);
    const mat = new THREE.MeshStandardMaterial({ color: 0xd8d2c4 });
    const seen = (x, z) => {
      const i = Math.round(z) * (map?.w || 72) + Math.round(x);
      return (map?.fog?.[i] ?? 0) >= 1 || !!map?.reveal?.has(i);
    };
    for (let i = 0; i < 6; i++) {
      const m = new THREE.Mesh(body, mat);
      m.scale.set(1.4, 0.9, 0.9);
      m.castShadow = true;
      let x = 8, z = 8;
      for (let t = 0; t < 12 && !seen(x, z); t++) {   // explored only
        x = 8 + Math.random() * ((map?.w || 72) - 16);
        z = 8 + Math.random() * ((map?.h || 54) - 16);
      }
      m.position.set(x, 0.16, z);
      m.userData.home = { x, z };
      m.userData.t = Math.random() * 9;
      m.userData.dir = Math.random() * Math.PI * 2;
      this.scene.add(m);
      this._critters.push(m);
    }
  }

  stepCritters(dt, t) {
    for (const m of this._critters || []) {
      const u = m.userData;
      u.t -= dt;
      if (u.t <= 0) {                          // pick a new wander dir
        u.t = 2 + Math.random() * 5;
        u.dir = Math.random() * Math.PI * 2;
      }
      const nx = m.position.x + Math.cos(u.dir) * dt * 0.7,
            nz = m.position.z + Math.sin(u.dir) * dt * 0.7;
      if (Math.hypot(nx - u.home.x, nz - u.home.z) < 6) {
        m.position.x = nx; m.position.z = nz;
        m.rotation.y = -u.dir;
        m.position.y = 0.16 + Math.abs(Math.sin(t * 9 + u.home.x)) * 0.05;
      } else u.dir += Math.PI * 0.7;           // steer back toward home
    }
  }

  /* drift cloud shadows with the wind vector */
  stepClouds(dt, windX = 0.8, windZ = 0.35) {
    for (const m of this._clouds || []) {
      m.position.x += windX * dt;
      m.position.z += windZ * dt;
      if (m.position.x > 76) m.position.x = -6;
      if (m.position.z > 58) m.position.z = -6;
    }
  }

  /* WC3 doodads: instanced trees/rocks scattered on revealed non-marked
     tiles, palette keyed by region (biome variety per repo area). */
  _doodads(map) {
    if (this._doodadsBuilt) return;
    this._doodadsBuilt = true;
    if (this._doodadMeshes) {                      // fog grew: rebuild
      for (const m of this._doodadMeshes) this.scene.remove(m);
    }
    const rng = (x, y, s) => {
      let h = (x * 73856093 ^ y * 19349663 ^ s * 83492791) >>> 0;
      return (h % 1000) / 1000;
    };
    const trunkG = new THREE.CylinderGeometry(0.07, 0.11, 0.6, 5);
    const crownG = new THREE.ConeGeometry(0.5, 1.5, 6);
    const rockG = new THREE.DodecahedronGeometry(0.32);
    const trunkM = new THREE.MeshStandardMaterial({ color: 0x4a3826,
      roughness: 0.95 });
    const crownM = new THREE.MeshStandardMaterial({ color: 0x2d4a26,
      roughness: 0.9 });
    const rockM = new THREE.MeshStandardMaterial({ color: 0x5a6169,
      roughness: 0.95 });
    const pts = [];
    for (let y = 1; y < map.h - 1; y++)
      for (let x = 1; x < map.w - 1; x++) {
        const i = y * map.w + x;
        const f = map.reveal?.has(i) ? 2 : (map.fog || [])[i];
        if (f < 1 || (map.mark || [])[i]) continue;
        if (rng(x, y, 1) > 0.09) continue;          // ~9% forest cover
        pts.push([x + 0.2 + rng(x, y, 2) * 0.6, y + 0.2 + rng(x, y, 3) * 0.6,
                  rng(x, y, 4), (map.regions || [])[map.tile_region[i]]]);
      }
    if (pts.length > 900) pts.length = 900;
    const trunks = new THREE.InstancedMesh(trunkG, trunkM, pts.length);
    const crowns = new THREE.InstancedMesh(crownG, crownM, pts.length);
    const rocks = new THREE.InstancedMesh(rockG, rockM, pts.length);
    const m4 = new THREE.Matrix4(), q = new THREE.Quaternion(),
          v = new THREE.Vector3(), sc = new THREE.Vector3();
    const col = new THREE.Color();
    pts.forEach((p, i) => {
      const s = 0.7 + p[2] * 0.7;
      v.set(p[0], 0.3 * s, p[1]);
      q.setFromAxisAngle(new THREE.Vector3(0, 1, 0), p[2] * 6.28);
      sc.setScalar(s);
      trunks.setMatrixAt(i, m4.compose(v, q, sc));
      v.y = 0.6 * s + 0.55 * s;
      crowns.setMatrixAt(i, m4.compose(v, q, sc));
      col.setHSL(0.32 - p[2] * 0.1, 0.4 + p[2] * 0.2,
                 0.2 + rng(i, p[0], 5) * 0.12);
      crowns.setColorAt(i, col);
      v.y = 0.14;
      const rock = p[2] > 0.82;                     // ~18% become rocks
      sc.setScalar(rock ? s * 0.9 : 0.001);
      rocks.setMatrixAt(i, m4.compose(v, q, sc));
    });
    trunks.castShadow = crowns.castShadow = rocks.castShadow = true;
    this._doodadMeshes = [trunks, crowns, rocks];
    this.scene.add(trunks, crowns, rocks);
  }

  render() { this.composer.render(); }
}
