# Datamosh

## Visual Anatomy
1. **Motion smear** — pixels melt as vectors from clip B are applied to clip A.
2. **Bloom/melt transitions** — cuts turn viscous; image "grows" over the next.
3. **Ghosting** — stale framebuffer persists under new content.
4. **Macroblock artifacts** — 16×16 blocks visible as residuals accumulate.

## The Math / Algorithm
GOP abuse in temporal codecs (H.264/MPEG-4 ASP):
- **I-frame** = full image (keyframe); **P-frame** = motion vectors + residual
  vs previous; **B-frame** = bidirectional (avoid — complicates reference).
- **I-frame drop**: decoder applies B-scene motion vectors onto A-scene
  buffer → melt. **P-frame duplication**: repeated deltas → frozen motion +
  accumulating bloom.
- Encode recipe: `mpeg4`/`libxvid`, `-g 9999` (one I-frame per file),
  `-bf 0` (no B-frames), lowish bitrate.
- FFmpeg `select='eq(pict_type,PICT_TYPE_P)'` strips I-frames at stream level;
  `bsf:datamosh` patch drops keyframes by `target` count.

## Implementation — Media/Python
```bash
# classic: concat + strip I-frames
ffmpeg -i a.mp4 -i b.mp4 -filter_complex concat -c:v libxvid -g 9999 -bf 0 tmp.avi
ffmpeg -i tmp.avi -vf "select='eq(pict_type,PICT_TYPE_P)',setpts=N/FRAME_RATE/TB" -c:v libx264 -an mosh.mp4
```
- FFglitch/ffmosh: edit motion vectors as JSON (`-bf` bitstream editing).
- Avidemux manual: cut I-frames in GUI.

## Implementation — Web/UI
- Real datamosh needs codec access — do it offline with FFmpeg, ship result.
- Fake it: `mix(texA, texB, smearMask)` with motion-vector-like displacement
  field + temporal feedback buffer (ping-pong FBO, `decay≈0.9`).

## Sources
- https://glitchology.com/datamoshing/ (GOP/I-P-B mechanics + workflow)
- https://hoop.dev/blog/ffmpeg-mosh/ (FFmpeg select/PICT_TYPE_P commands)
- http://mplayerhq.hu/pipermail/ffmpeg-devel/2024-May/326858.html (datamosh bitstream filter patch)
- https://github.com/Nuvotion-Visuals/ffmosh (FFglitch-derived bitstream editing lib)

## Related local tools
- `grainrad.py --effect vhs` (adjacent analog corruption)
