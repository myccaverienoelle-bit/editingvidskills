# HyperFrames: the gotchas that cost a month

HyperFrames builds every graphic as HTML, CSS and GSAP, then renders it in a headless
browser. That is why there is no ceiling on how many graphics a video can have. It is also where
all the sharp edges live. None of these are guessable — read this file before writing a
composition.

## The timeline contract

**Compositions are seeked, not played.** The renderer jumps to arbitrary frames rather than
running in real time. Everything below follows from that.

- Build **one master timeline**, created paused, with every tween at an **absolute second**.
  Not relative offsets.
- **Never use random values.** The same frame has to render identically on every seek.
- **Never drive state from real-time timers.** No `setTimeout`, no animation frame loops.
  Everything comes off timeline position.
- **Every exit that lands on a boundary needs an explicit hard kill** — an opacity set to zero at
  that exact time. An unresolved tween pops instead of finishing.
- **Time is always in seconds.** Never frames.
- **Every entrance uses a from-to tween, never a bare `to`.** A bare `to` has no defined start
  state when the timeline is seeked into the middle of it.
- **Never put a CSS transform and a GSAP tween on the same property.**

## Things that silently do not render

This is the category that wastes days, because nothing errors. It just quietly comes out wrong.

- **Never transform a video element directly.** Put a scale or a move on a `<video>` and the
  headless render composites it away — the face just vanishes where the move should be. No
  error, no warning. Reframe **through layout** instead: wrap the video in a div with hidden
  overflow, and animate the wrapper's `left`, `top`, `width`, `height`. The parent shrinks and
  crops the untransformed video inside it.
- **CSS blur filters are not render-safe.** For a blur-in text reveal, use a per-letter opacity
  stagger instead, around 0.045s between letters.
- **Grayscale filters fail the same way.** Fake desaturation by tweening the colour toward a
  flatter value.
- **Class-name tweens do not survive the seek.** Worse than failing to apply, they can wipe the
  base class's styling entirely. Tween the actual CSS properties directly.
- **Near-zero-duration tweens are unreliable.** Two identical 0.001s tweens in the same call:
  one applied, one did not. Give every instant state change a real duration of 0.2–0.35s. It still
  reads as a cut.
- **Raw emoji glyphs hang the render.** A single emoji codepoint sends the headless browser
  spinning at full CPU trying to load a colour emoji font it cannot decode. It never errors and
  never times out — a five second part that should take seven seconds will burn five minutes
  before you kill it. Fake the look with the brand font, or pre-render the glyph as a transparent
  PNG and overlay it. **The tell:** a render still going at three times the length of a same-sized
  part is an emoji, not a real hang.
- **Transparent overlays have nothing behind them**, so backdrop blur does not happen. Design
  frosted panels to read on their own fill.

## Linter and workflow notes

- **Lint and validate are the gate.** Run both on every part before rendering.
- **Contrast warnings on deliberately dim text** are worth satisfying by raising the opacity
  rather than the brightness. It keeps the intended look.
- **A dense-track warning on a short build is normal.** Do not refactor a handful of parts into
  sub-compositions to silence it.
- **Keep the build source durable, never only in a temp folder.** Temp is volatile on every
  platform; an overnight clear has wiped an entire in-progress build. The small stuff — the build
  script and the compositions — belongs in `graphics-build/` inside the project. Only the heavy
  regenerable renders belong in a cache.
- **Pin the HyperFrames version.** Everything here is tuned against one version's quirks. Two
  `doctor` failures are expected on a healthy machine: the nag to upgrade past the pin, and
  Docker not running. Ignore both.
