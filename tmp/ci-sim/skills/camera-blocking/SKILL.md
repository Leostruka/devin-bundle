---
name: camera-blocking
description: Use when turning a product or scene into a camera-directed hero video: blockout low-poly scene in headless Blender, keyframe a camera path, playblast to MP4, then hand a second-by-second prompt template to a video-repaint model (Seedance-class) and scaffold the result as a scroll-bound web hero.
triggers: [user]
---

# Camera Blocking

Video-AI repaint models (Seedance class) keep camera and framing only when
they get an explicit motion reference. This skill turns headless Blender
into the camera-direction tool: block the scene in greybox, animate only
the camera, playblast, then describe every beat to the repaint model.

The muscle already exists: `extensions/blender-operator/` presets +
`extensions/blender-operator/camera_blocking.py` orchestrator.

## Conventions

- **Blockout = greybox only.** Low-poly primitives, flat grey material,
  ground plane, one key light. Look is irrelevant; only the camera matters.
- **The camera is the deliverable.** Model detail is wasted tokens - the
  repaint model does the look.
- **Never invent camera motion in the prompt.** Every beat in the prompt
  template must correspond to a real keyframed segment of the playblast.

## Flow

One command runs the whole blockout -> rig -> playblast chain on its own
isolated `-b --factory-startup` server (never touches user scenes):

```sh
python extensions/blender-operator/camera_blocking.py --out DIR \
    [--name shot] [--fps 24] [--frames 48] [--path orbit|dolly]
```

Outputs: `DIR/shot.mp4` + `camera.json` + frame PNGs, validated and handed
off as a media-tools job descriptor.

Manual step-by-step (when the orchestrator is too coarse): presets live in
`extensions/blender-operator/presets/` and take a `PARAMS` dict injected
before exec:

1. `presets/blockout.py` - primitives kit (boxes, cylinders, flat grey
   material, ground plane, key light).
2. `presets/camera_rig.py` - paths `orbit`|`dolly`, TRACK_TO target,
   keyframed camera; PARAMS: frame_start/frame_end/fps/radius/height/lens.
3. `presets/playblast.py` - fast viewport/EEVEE render to MP4
   (PARAMS: name, width, height, engine, force, preview_frame).

Then:

1. Write the second-by-second prompt (template below) from the REAL
   keyframes - timestamps must match the playblast.
2. External handoff: paste playblast + prompt (+ reference photos of the
   real product - they improve adherence) into the repaint model. SaaS is
   out of scope; the template is the contract.
3. Scaffold the delivered clip as a scroll-bound hero (below).

## Prompt template

```
REPAINT TARGET: <playblast.mp4>  |  <N>s @ <fps>fps
REFERENCES: [product-front.png] = the real product; [style-ref.png] = mood.
HARD LOCATION MAP: the product stays center-frame on the grey pedestal at
all times; camera never goes below the ground plane; no new objects may
appear. Preserve exact camera motion - do not invent moves.

BEATS:
t=0.0s..t=1.5s  camera orbits 0deg..60deg, product idle
t=1.5s..t=3.0s  dolly-in, exploded view: 4 panels separate outward
t=3.0s..t=4.0s  crane rise +30cm, panels reassemble
STYLE: <one line - e.g. matte black product, warm rim light, shallow DOF>
```

Named references keep the model honest; the hard location map forbids
invented camera moves; beats are copied verbatim from the rig keyframes.

## Scroll scaffold (web hero)

Generate in the user's project, never autoplay, never loose loops:

```html
<video id="hero" muted playsinline preload="auto" src="hero.mp4"></video>
<script>
  const v = document.getElementById('hero');
  addEventListener('scroll', () => {
    const p = scrollY / (document.body.scrollHeight - innerHeight);
    v.currentTime = p * v.duration;   // playhead bound to scrollY
  });
</script>
```

## Cross-links

- `operate-blender` - generic muscle (exec loop, server lifecycle).
- `creative-engineering` - repaint style direction.
- `animation-direction` - beat/timestamp grammar shared with the prompt.

## Non-goals

No Seedance/Higgsfield client (external SaaS - template only). No real
video render in CI. No heavy assets in the repo.
