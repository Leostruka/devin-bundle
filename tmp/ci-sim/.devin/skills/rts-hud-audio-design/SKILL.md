---
name: rts-hud-audio-design
description: Use when designing or overhauling RTS user interfaces, command cards, hotkey grids, tooltips, game menus, or procedural WebAudio sound effects (Karplus-Strong strings, FM metallic clashes, filtered noise wind/rain/thunder, and theme-specific foley).
---

# RTS HUD Architecture, Ergonomics & Procedural WebAudio DSP

## 1. Three-Layer RTS Control & HUD Hierarchy

Per competitive RTS design (Warcraft III, Age of Empires III, StarCraft II):

| Layer | Screen Zone | Elements & Ergonomic Rules |
|---|---|---|
| **Macro** | Top Bar (`36px`) | Gold/Tokens (+rate/min), Lumber/Context %, Supply (used/cap), Upkeep Crest, Idle Worker Alert (`[.]`), Sun/Moon + Live Local Weather Orb, `F10` Game Menu button. |
| **Wide** | Battlefield Overlays | Left: **Hero Roster (`F1-F5`)** with portrait, level, HP/MP bars (click=select, dblclick=center). Right: **District/Building Strip** (click=select/inspect, dblclick=center). Canvas: elliptical ground selection rings, health/mana plates, floating combat/loot numbers, tactical cursor state. |
| **Micro** | Bottom Console (`168px`) | Left: **Minimap** + filter toggles (`All`, `Units`, `Bld`, `Ping`). Center-Left: **Animated 3D-Lit Portrait** (`#portcv`). Center: **Stats + 6-Slot Runed Inventory / Production Queue**. Right: **4x3 Grid Command Card (`QWER / ASDF / ZXCV`)** with vector icons, hotkey badges, and anchored WC3 tooltip above the card. |

## 2. 4x3 Grid Command Card (`Q W E R / A S D F / Z X C V`)

- Every slot displays:
  1. Custom procedural vector SVG/Canvas icon (Sword, Boot, Shield, Patrol Loop, Pickaxe, Arcane Eye, Hammer, Scales, Scroll, War-Drum, Spyglass, Emissary Seal, Horn, Tent, Tome).
  2. Top-right hotkey badge (`Q`, `W`, `E`, `R`, `A`, `S`, `D`, `F`, `Z`, `X`, `C`, `V`).
  3. Concise 1-word label (`Move`, `Stop`, `Hold`, `Patrol`, `Attack`, `Gather`, etc.).
- **Anchored WC3 Tooltip (`#cardtip`)**: Hovering any command card button or inventory slot renders a gold-beveled tooltip anchored directly above the bottom console with Title, `[Hotkey]`, Backing CLI/Bundle Surface, and Tactical Effect.

## 3. Procedural WebAudio DSP Sound Engine

Zero external audio files; synthesize every sound in real time from physical/DSP primitives:

1. **Continuous Environmental Soundscape (Noise + Biquad Filter Bank)**:
   - Generate a 2-second looping pink/brown noise `AudioBuffer`.
   - Route through a `BiquadFilterNode` (`bandpass` for wind, `highpass` + droplet modulation for rain):
     - Wind cutoff `180 + 14 * v_kph` Hz, Q=1.8, gain scaled by wind gust envelope.
     - Rain adds high-frequency patter (`2200 Hz` bandpass) + randomized Karplus-Strong water drips.
     - Thunder cascades brown noise through a `90 Hz` low-pass filter with multi-tap exponential decay.
2. **Metallic & Weapon Synthesis (Inharmonic FM + Bandpass Noise Burst)**:
   - **Sword Clash / Attack**: Noise burst (`40ms`, bandpass `2400 Hz`) + 3 detuned high-Q partials (`780, 1240, 1960 Hz`).
   - **Anvil Clang (Runeforge)**: FM carrier `587 Hz`, modulator `830 Hz`, index decaying over `350ms`.
   - **Gold Coin / Gather**: Dual high sine chimes (`1760 Hz -> 2637 Hz`).
3. **Theme-Aware Foley (`Battlefield` vs `Office`)**:
   - Check `Theme.get().name`: in `office` mode, map unit/building actions to office acoustics (mechanical keyswitch clicks, desk bell ding, espresso steam hiss, printer stepper whir, water-cooler bubble glug).
