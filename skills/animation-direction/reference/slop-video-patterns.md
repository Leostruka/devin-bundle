# Video slop patterns (anti-patterns corpus)

Anti-patterns that make code-rendered motion graphics read as generated
rather than directed. Evidence: media-osint-20261126 batch1 (eFog2ttK95g,
AI Labs motion workflow). Check every scene plan against this list before
the approval gate; a plan containing one is not ready.

## Layout slop

- **Centered title on gradient** - the single most common generated look:
  big centered text over a purple/blue gradient. Gradients are allowed
  only when they mean something in the piece.
- **Card/frame borders everywhere** - boxing every element in rounded
  rectangles with borders. Real motion design uses space and alignment,
  not containers.
- **Fake chrome** - fake timecodes, corner labels, rec dots, fake UI
  chrome that mimics a real product or camera. If the piece is not a
  screen recording, it does not get screen-recording furniture.
- **Dead-center static shots** - every element sitting at exact center
  with no compositional tension. Negative space is a tool.

## Motion slop

- **Slide-deck resets** - every scene wiping to blank and rebuilding from
  nothing, like a PowerPoint transition. Directed video carries elements
  across cuts or motivates their exit.
- **Meaningless motion** - movement that answers no question: floating
  particles, drifting blobs, parallax for its own sake. Every move either
  directs attention, shows causality, or marks time.
- **Uniform easing everywhere** - everything ease-in-out at the same
  duration. Directed motion varies: anticipation is slow, release is fast,
  settles are small.
- **Constant motion** - no stillness. Holds are where the viewer reads.
  Text holds >= 1.5s minimum.

## Content slop

- **Walls of text** - more than ~12 words on screen as kinetic text;
  the narration carries detail, the screen carries structure.
- **Numbers without scale** - a counter animating to a number with no
  unit, baseline, or comparison. Metrics need meaning.
- **Everything emphasized** - if every beat scales/pops/springs, nothing
  is emphasized. Emphasis is a budget: one or two moments per piece.
