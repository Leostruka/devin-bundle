---
name: rts-3d-procedural-art
description: Use when building or upgrading 2D/isometric/top-down games or canvases to look like pre-rendered 3D (Warcraft III, Age of Empires III, Hades) with PBR-style lighting, directional cast shadows, seamless terrain splatting, Gerstner water waves, skeletal IK/FK locomotion, and Verlet cloth physics without external 3D asset files.
---

# RTS 3D Procedural Art & Physics Engine

## Core Principle: Math Over Flat Primitives

Flat `fillRect` and `arc` calls with uniform hex colors read as 2D programmer art. Pre-rendered/realtime 3D RTS visuals require five mathematical layers on every frame:

1. **Seamless Terrain Splatting & Elevation Shading** (no blocky tile grid seams)
2. **Directional Sun/Moon Lighting Vector L + Ground Cast Shadows + Ambient Occlusion (AO)**
3. **3D Volumetric Surface Gradients** (Lambertian diffuse + Blinn-Phong specular + Fresnel rim light)
4. **Articulated Multi-Bone Skeletal Rigs** (2-bone stride kinematics, counter-rotating pauldrons, weapon swing arcs)
5. **Verlet Spring-Damper Cloth & Wind Physics** (capes, banners, canopies, Gerstner water crests)

## 1. Directional Lighting & Projected Cast Shadows

Given a normalized light direction L = (Lx, Ly, Lz) (e.g. (-0.55, -0.62, 0.56) by day, modulated by `nightFactor` and `cloud_pct`):
- **Shadow Skew Projection**: An object of height H at (x, y) casts an elliptical/polygonal shadow offset by (-Lx * H, -Ly * H) with alpha clamped to [0.10, 0.45] inversely proportional to cloud cover.
- **Ambient Occlusion (AO) Contact Ring**: Every structure and unit draws a soft dark radial gradient at its ground contact footprint before drawing geometry, anchoring it to the terrain.

## 2. 3D Volumetric Shading Primitives (Canvas 2D)

- **Cylindrical / Spherical Volume (Towers, Columns, Helmets, Cuirass)**:
  Use a 4-stop linear/radial gradient perpendicular to L:
  - `0.0`: Specular highlight (+35% lightness)
  - `0.28`: Base albedo color
  - `0.78`: Core terminator shadow (-40% lightness)
  - `1.0`: Fresnel rim bounce light (+15% lightness or sky tint)
- **Axonometric 3D Building Extrusion**:
  - Draw South/Front Wall (medium lit, stone courses / timber beams)
  - Draw East/Side Wall (shadowed -28%, depth extrusion)
  - Draw West Roof Slope (sun-lit +18% with shingle courses) and East Roof Slope (shadowed -22%)
  - Draw Recessed Archways & Windows (dark frame + specular glass reflection by day, warm `#ffcf5c` candle bloom at dusk/night).

## 3. Articulated Skeletal Rigs & Locomotion

Decompose every humanoid unit into 9 articulated parts driven by phase `phi = omega * t + seed`:
1. **Shadow + Hero Glow + Rotating Aura Rune** (ground plane)
2. **Back Cape (4-node Verlet ribbon)** trailing unit velocity and oscillating with the live wind vector.
3. **Left & Right Legs / Boots**: Stride offset `sin(phi) * S`, pelvis vertical bounce `-abs(cos(phi)) * A`.
4. **Torso / Cuirass + Tabard**: 3D-shaded breastplate with waist belt and hanging tabard.
5. **Left & Right Pauldrons (Shoulders)**: Oversized WC3-proportioned shoulder plates with metallic trim, counter-rotating with arm swing.
6. **Left Arm (Shield / Tome / Quiver)** & **Right Arm (Weapon / Staff / Bow)**:
   - Idle (`Stand - 1`): slow breathing counter-sway.
   - Look-around (`Stand - 2`): head + helm yaw.
   - Flourish (`Stand - 3`): weapon raised with specular glint.
   - Combat/Work (`Attack`/`Work`): right arm sweeps through slash/strike arc with fading blade-ribbon and impact sparks.
7. **Head & Class Helmet/Hat/Hood** with visor/eyes and plume.

## 4. Seamless Terrain Splatting & Gerstner Water

- **Offscreen Terrain Bake (`_terrainCanvas`)**: Render the base terrain once per map layout into an offscreen canvas using multi-octave value noise, organic biome transitions, stone-paved Keep courtyards, wheel-rutted dirt roads with grassy edges, and cliff drop-shadows. Blit the visible viewport rect in a single `drawImage` call.
- **Gerstner Water Waves**: Superpose 2 directional wave trains aligned with the wind vector, rendering specular sun/moon glints and rhythmic shore foam where water borders land.
