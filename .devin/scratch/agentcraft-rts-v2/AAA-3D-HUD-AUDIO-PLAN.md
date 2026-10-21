# Master Plan: AAA 3D Procedural Modeling, Physics, RTS HUD/Menu Ergonomics & WebAudio DSP Overhaul

## 1. Executive Summary

Following deep research into **3D procedural modeling, PBR-inspired lighting, skeletal IK/FK animation, Verlet cloth physics, RTS UI/UX ergonomics (Warcraft III / Age of Empires III / StarCraft II), and WebAudio DSP synthesis**, this plan defines the next three milestone `v3.8.0` issues (`#163`, `#164`, `#165`) to elevate every area of the RTS orchestration game.

---

## 2. Pillar 1 — Issue #163: 3D Volumetric Modeling, Seamless Terrain Splatting & Skeletal/Verlet Physics

### 2.1 Seamless Organic Terrain Splatting (`_ensureTerrainCanvas` in `engine.js`)
- **Problem**: Tile-by-tile `fillRect` creates visible rectangular grid seams even with meadow grass tufts.
- **Solution**: Pre-bake an offscreen high-resolution terrain canvas (`W * TILE` x `H * TILE`) per map layout signature:
  - Organic multi-octave noise biome blending across Voronoi region boundaries.
  - Individual stone pavers and mortar rings on Keep courtyards (`roads === 2`).
  - Soft-edged packed-earth roads (`roads === 1`) with grassy verges and wheel ruts.
  - Coastal sand/pebble shelves along rivers and lakes (`water > 0`).
  - Elevation contour shading and cliff drop-shadows.
  - Blitted per frame with a single `ctx.drawImage` call (`<0.2ms`), then topped with live Gerstner water waves, foam, swaying 3D-lit trees, and weather particles.

### 2.2 3D-Lit Axonometric Buildings with Directional Cast Shadows & AO (`Theme._paintBuilding` + `engine.js`)
- **Directional Sun/Moon Vector $\mathbf{L} = (-0.55, -0.62, 0.56)$**:
  - Every building and tree casts a **skewed ground shadow** whose opacity scales inversely with `weather.cloud_pct` and shifts with `nightFactor`.
  - **Ambient Occlusion (AO)** radial contact gradient under every structure foundation.
  - **3D Volumetric Gradients**: Cylindrical stone towers with 4-stop Lambertian + specular + Fresnel rim gradients; 3D extruded South + East walls; sunlit West roof slopes vs shadowed East roof slopes with individual shingle courses; recessed archways and paned windows with glass specular reflection by day and warm candle bloom at night.

### 2.3 Articulated Skeletal Unit/Hero Rigs, Verlet Cloth & Projectiles (`_drawUnitLive` in `engine.js`)
- **9-Part Articulated Rig**:
  - Ground cast shadow + Hero Glow + rotating geometric Aura rune.
  - **4-Node Verlet Cloth Cape** trailing unit velocity vector + oscillating with live Open-Meteo wind speed/gusts/direction.
  - Articulated Left & Right Legs/Greaves with 2-bone stride kinematics during movement + pelvis bounce.
  - 3D-shaded Cuirass/Robe torso + swaying tabard + counter-rotating oversized WC3 Pauldrons.
  - Articulated Left Arm (3D-shaded Kite Shield / Spell Tome / Buckler) and Right Arm (Broadsword / Crystal Arch-Staff / Recurve Bow / Dwarven Warhammer / Twin Daggers / Pickaxe).
  - **Combat Projectiles & Slash Trails**: Rangers/Scouts fire visible arcing arrows; Casters launch glowing arcane bolts; Knights/Marshals sweep broadswords with a glowing slash ribbon and metallic sparks.

---

## 3. Pillar 2 — Issue #164: RTS HUD, F10 Game Menu, 4x3 QWER Command Card & Inventory Ergonomics

### 3.1 Sculpted Top Macro Bar & `F10` Game Menu Modal
- Sculpted resource pills with custom SVG icons for **Gold (Tokens + rate)**, **Lumber (Context %)**, **Supply (Used/Cap)**, **Upkeep Crest**, **Idle Worker Bell (`[.]`)**, **WC3 Sun/Moon + Live Weather Clock Orb**, and **`Menu (F10)`**.
- **`F10` In-Game Menu Modal (`#gamemenu`)**:
  - Master Volume + Continuous Ambience toggle.
  - Live Weather Inspector (shows full 8-hour Curitiba forecast table + 1-click Weather Mode buttons: `Live Forecast`, `Clear Sun`, `Overcast`, `Rain`, `Thunderstorm`, `Snow`, `Dense Fog`, `Gale Wind`).
  - Theme Switcher (`Battlefield` vs `Isometric Office`) + Day/Night Cycle toggle.
  - Quick links to `Victory Score / Match History`, `Tech Tree (K)`, and `Hotkey Guide (?)`.

### 3.2 4x3 Grid Command Card (`Q W E R / A S D F / Z X C V`) with Vector Icons & Anchored WC3 Tooltip
- Upgrade `#cmdcard` to a true **4x3 (12-slot) RTS Command Grid** mapped to `Q W E R / A S D F / Z X C V` (while preserving classic `M/S/H/P/A/G` aliases for compatibility!):
  - Every slot renders a custom **inline SVG vector icon** (Sword, Boot, Shield, Patrol Loop, Pickaxe, Arcane Eye, Hammer, Scales, Scroll, War-Drum, Spyglass, Emissary Seal, Horn, Tent, Spell Tome).
  - **Anchored WC3 Command Tooltip (`#cardtip`)** directly above the Command Card showing Action Name, `[Hotkey]`, Backing CLI/Bundle Surface, and Tactical Effect.
- **Minimap Filter Buttons**: `All`, `Units`, `Bld`, `Ping` next to the minimap, plus a proper **Isometric Camera Trapezoid** on the minimap when in Office/Iso mode!
- **WC3 6-Slot Runed Inventory Grid** in the center console alongside the animated 3D-lit `#portcv` portrait and beveled HP/MP/XP progress bars.

---

## 4. Pillar 3 — Issue #165: Theme-Aware WebAudio DSP Sound Engine (`Battlefield` + `Office` + Live Weather)

- **Continuous Environmental Noise & Filter Bank (`_ambNode`)**:
  - Procedural pink/brown noise `AudioBuffer` loop routed through WebAudio `BiquadFilterNode`s tracking live `weather.wind_kph`, `weather.wind_gust_kph`, and `weather.condition` (`rain`/`storm` patter + Karplus-Strong water drips + low-pass thunder rumbles).
- **Physical & FM Synthesis for Unit/Building SFX**:
  - Inharmonic FM metallic partials for Sword Clash (`attack`), Anvil Strike (`runeforge`), Shield Clink (`select_hero`), Coin Jingle (`gather`/`marketplace`), Cathedral Choir (`altar`), War Horn (`barracks`/`town-hall`), Arcane Shimmer (`library`/`spell`), Lute/Tavern Chord (`tavern`).
- **Theme-Aware Office Foley (`Theme.get().name === "office"`)**:
  - Automatically switches SFX to realistic office acoustics when in Isometric Office Mode: mechanical keyboard clacks, reception desk bell, espresso steamer hiss, printer stepper motor, and water-cooler bubble glug!
