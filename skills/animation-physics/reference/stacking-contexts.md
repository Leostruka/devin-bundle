# Z-Index & Stacking Contexts — Reference

## Stacking Context Formation

A new stacking context is created by:

1. **Root element** (`<html>`)
2. **`position` with `z-index`** (not `auto`)
3. **`position: fixed` or `position: sticky`**
4. **`opacity` < 1** (with `filter`, `transform`, `perspective`, etc.)
5. **`transform`** (not `none`)
6. **`filter`** (not `none`)
7. **`perspective`** (not `none`)
8. **`isolation: isolate`**
9. **`-webkit-overflow-scrolling`**
10. **`will-change`** (any of: transform, opacity, filter, etc.)

## Critical Rule

**`position: fixed` ALWAYS creates a stacking context**, regardless of z-index value.

This means:
```css
.fixed-element {
    position: fixed;
    z-index: 50;
    /* This creates a NEW stacking context */
    /* It will render ABOVE all normal-flow elements */
    /* even if those elements have z-index: 999 */
}
```

## Stacking Order (Bottom to Top)

Within a stacking context:
```
1. Background/border of the element itself
2. Descendants with negative z-index
3. Non-positioned block-level elements (normal flow)
4. Non-positioned floated elements
5. Non-positioned inline elements
6. Descendants with z-index: auto or 0
7. Descendants with positive z-index
```

## Animation-Specific Patterns

### Pattern 1: Overlay Above Normal Flow

```html
<div class="relative">  <!-- z-index: auto -->
    <div class="z-50">Fixed header</div>
    <div class="z-100">Modal overlay</div>  <!-- Creates stacking context -->
    <div class="z-101">Modal content</div>  <!-- Above overlay -->
</div>
```

**Problem:** `position: fixed` on modal creates context. Even `z-index: 1` would be above `z-index: 999` in normal flow.

### Pattern 2: Element Passing Over Another

```js
// Element A (z-101) passes OVER Element B (z-50)
gsap.to(elementA, {
    x: 100,
    y: 200,
    zIndex: 101,  // Set BEFORE animation starts
});
```

**Solution:** Set z-index via `gsap.set()` before animation, not during.

### Pattern 3: Cross-Page Visual Continuity

```html
<!-- Page A -->
<div id="logo" class="fixed z-101" style="left: 960; top: 270;">
    Logo
</div>

<!-- Page B (after transition) -->
<div id="logo" class="fixed z-101" style="left: 960; top: 540;">
    Logo
</div>
```

**Verification:**
```
Page A final: (960, 270), scale=1.0, z=101
Page B initial: (960, 540), scale=0.833, z=101
Delta: (0, +270), scale=0.833
Animation must produce EXACTLY this delta.
```

## Debugging Checklist

| Symptom | Likely Cause | Fix |
|---------|--------------|-----|
| Element appears behind another unexpectedly | Stacking context mismatch | Map all contexts |
| Element flashes during animation | `from()` without `immediateRender:false` | Use `gsap.set()` + `to()` |
| Element jumps at animation start | DOM layout change | Use `autoAlpha:0` (preserves space) |
| Element disappears after animation | `clearProps` removed needed styles | Be selective with `clearProps` |
| Animation works in dev, breaks in prod | CSS specificity or stacking context | Check computed z-index |

## GSAP Z-Index Management

```js
// Set z-index before animation
gsap.set(element, { zIndex: 101 });

// Animate position
gsap.to(element, {
    x: 100,
    y: 200,
    duration: 0.3,
});

// Reset z-index after animation
gsap.set(element, { zIndex: 'auto' });
```

**Rule:** Never animate `z-index`. Set it instantly via `gsap.set()`.
