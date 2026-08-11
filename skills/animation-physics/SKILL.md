---
name: animation-physics
description: Use when planning, analyzing, or debugging complex UI animations involving multiple elements, transitions, or visual coherence across pages. Decomposes animation problems into coordinate geometry, timing tables, and z-index stacking analysis.
---

# Animation Physics — Mathematical Abstraction for UI Motion

A systematic methodology for decomposing complex UI animation problems into measurable, verifiable mathematical models.

## When to Use

- Multi-element choreography (e.g., element A moves while element B fades)
- Cross-page visual continuity (e.g., login→dashboard transition)
- Z-index stacking conflicts during animations
- Performance validation (compositor-only vs layout-triggering animations)
- Debugging visual artifacts (flashes, jumps, tics)

## Method: 7-Step Analysis

### Step 1: Define Coordinate System

Establish a fixed viewport reference. For web: `(0,0)` = top-left, `X` = right, `Y` = down.

```
(0,0) ──────── X ──────── (viewportW, 0)
  │                         │
  Y                         │
  │                         │
(0, viewportH) ──────── (viewportW, viewportH)
```

Always specify: viewport dimensions, unit (px), and origin.

### Step 2: Measure Element Positions

For each animated element, record:

| Property | Source | Notes |
|----------|--------|-------|
| `getBoundingClientRect().left` | JS | Relative to viewport |
| `getBoundingClientRect().top` | JS | Relative to viewport |
| `width` | JS or CSS | Computed width |
| `height` | JS or CSS | Computed height |
| Center X | `left + width/2` | Key for alignment |
| Center Y | `top + height/2` | Key for alignment |

**Formula for center:**
```
centerX = left + width / 2
centerY = top + height / 2
```

### Step 3: Calculate Deltas

For each animated property, compute: `delta = destination - origin`

| Delta | Formula | Meaning |
|-------|---------|---------|
| `ΔX` | `destCenterX - originCenterX` | Horizontal translation |
| `ΔY` | `destCenterY - originCenterY` | Vertical translation |
| `scaleX` | `destWidth / originWidth` | Horizontal scale factor |
| `scaleY` | `destHeight / originHeight` | Vertical scale factor |
| `scale` | `min(scaleX, scaleY)` | Uniform scale (preserves aspect ratio) |

**GSAP transform mapping:**
```js
gsap.to(element, {
    x: deltaX,           // translateX
    y: deltaY,           // translateY
    scale: scaleFactor,  // uniform scale
});
```

### Step 4: Build Timing Table

Create a table with rows at key time intervals. Include:

| Column | Description |
|--------|-------------|
| Time (s) | Absolute time from animation start |
| Progress | Easing function output (0→1) |
| Element A position | Calculated from deltas × progress |
| Element A opacity | If fading |
| Element B position | If moving simultaneously |
| Element B opacity | If fading |
| Overlap? | Whether elements visually intersect |

**Easing reference (power2.inOut):**
```
t=0.00 → progress=0.000
t=0.25 → progress=0.500 (accelerating)
t=0.50 → progress=1.000 (decelerating)
t=0.75 → progress=1.000 (done)
```

Use GSAP's easing visualizer or calculate: `progress = t² * (3 - 2*t)` for power2.inOut.

### Step 5: Analyze Z-Index Stacking

Map all animated elements to their stacking contexts:

```
Stacking order (bottom to top):
  z-auto    Normal flow elements
  z-50      Fixed/absolute positioned (mid)
  z-100     Overlays
  z-101     Overlay children (logos, spinners)
```

**Key questions:**
1. Does element A pass OVER or UNDER element B during animation?
2. Is that the intended visual behavior?
3. Does `position: fixed` create an unexpected stacking context?

**Rule:** `position: fixed` always creates a new stacking context, regardless of z-index value.

### Step 6: Verify Performance

Classify each animated property:

| Property Type | Compositor-only? | Layout trigger? | Example |
|--------------|-----------------|----------------|---------|
| `transform` | ✅ Yes | ❌ No | `x`, `y`, `scale`, `rotation` |
| `opacity` | ✅ Yes | ❌ No | `autoAlpha`, `opacity` |
| `width`/`height` | ❌ No | ✅ Yes | Avoid animating |
| `top`/`left` | ❌ No | ✅ Yes | Use `x`/`y` instead |
| `margin`/`padding` | ❌ No | ✅ Yes | Avoid animating |

**Target:** All animations should be compositor-only (transforms + opacity).

**Layout thrashing formula:**
```
Layout triggers per animation = count of non-compositor properties animated
Target: 0 (or 1 if gsap.set() is used once at start)
```

### Step 7: Verify Visual Coherence

Define 5-6 key temporal markers and verify at each:

| Marker | Time | What to check |
|--------|------|---------------|
| Start | t=0 | Initial state correct? No flash? |
| Early | t=25% | Elements moving in expected direction? |
| Mid | t=50% | No unwanted overlaps? Progress matches easing? |
| Late | t=75% | Approaching final state? No jitter? |
| End | t=100% | Final position matches CSS target? |
| Post | t>100% | Stable? No residual transforms? |

**Cross-page continuity check:**
```
Page A final state === Page B initial state?
  Position: match (within 1px tolerance)
  Size: match
  Opacity: match
  Z-index: match
```

## Output Format

When analyzing an animation, produce:

1. **Coordinate Diagram** — ASCII art of viewport with element positions
2. **Delta Table** — All translation/scale calculations
3. **Timing Table** — Position at each time interval
4. **Z-Index Map** — Stacking context hierarchy
5. **Performance Table** — Compositor vs layout classification
6. **Coherence Check** — 6-marker verification

## Example: Login→Dashboard Logo Transition

### Input
- Form logo: `h-12` (48px), centered at `(960, 270)`
- Overlay logo: `h-10` (40px), centered at `(960, 540)`
- Animation: form logo fades, overlay logo moves from form position to center

### Analysis Output

**Deltas:**
```
ΔX = 960 - 960 = 0px (no horizontal movement)
ΔY = 540 - 270 = +270px (vertical only)
scale = 40 / 48 = 0.833
```

**Timing (power2.inOut, 0.3s):**
```
t=0.00s: progress=0.00, Y=0px,   scale=1.000
t=0.07s: progress=0.25, Y=68px,  scale=0.958
t=0.15s: progress=0.50, Y=135px, scale=0.917
t=0.22s: progress=0.75, Y=203px, scale=0.875
t=0.30s: progress=1.00, Y=270px, scale=0.833
```

**Final position verification:**
```
Center after transform: (960, 270 + 270) = (960, 540) ✓
Size after scale: 48 × 0.833 = 40px ✓
Matches CSS target: h-10, centered ✓
```

## Anti-Patterns

| Pattern | Problem | Fix |
|---------|---------|-----|
| Animating `top`/`left` | Layout thrashing, 60fps drops | Use `x`/`y` transforms |
| `z-index` wars during animation | Unpredictable layering | Map stacking contexts first |
| `from()` without `immediateRender:false` | Flash on page load | Use `gsap.set()` + `to()` |
| Moving DOM elements | Layout collapse | Use `autoAlpha:0` (preserves space) |
| `position: fixed` mid-animation | Unexpected stacking context | Plan z-index from start |

## Quick Reference

```
gsap.set()      → instant state change (1 layout trigger)
gsap.to()       → animate TO values (compositor-only)
gsap.from()     → animate FROM values (flash risk)
gsap.fromTo()   → explicit from+to (safest)
autoAlpha       → opacity + visibility (preferred over opacity)
clearProps:'all' → remove all inline styles (reset to CSS)
```
