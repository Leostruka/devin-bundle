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

/* Tilt-shift: banded DOF blur around the screen-space focus line —
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
    this._buildEnv(t);
    this._buildGround(t);
    if (this._mapData) this.bakeTerrain(this._mapData);
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
       contested hatch */
    for (let y = 0; y < map.h; y++)
      for (let x = 0; x < map.w; x++) {
        const mk = (map.mark || [])[y * map.w + x];
        if (!mk) continue;
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
    /* fog: shroud dark, explored mid, lit clear */
    for (let y = 0; y < map.h; y++)
      for (let x = 0; x < map.w; x++) {
        const f = (map.fog || [])[y * map.w + x];
        if (!f) {
          ctx.fillStyle = "rgba(4,8,12,.78)";
          ctx.fillRect(x * tw, y * th, tw + 0.5, th + 0.5);
        } else if (f === 1) {
          ctx.fillStyle = "rgba(6,12,18,.38)";
          ctx.fillRect(x * tw, y * th, tw + 0.5, th + 0.5);
        }
      }
    this._terrainTex.needsUpdate = true;
  }

  render() { this.composer.render(); }
}
