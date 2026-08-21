# The composite traps

These are FFmpeg problems, not HyperFrames problems, but they only show up at assemble
time — which is why they belong to this skill.

- **Match every part to the base frame rate exactly.** Probe it, never guess. Mixed frame rates
  drift.
- **Segments carry their own base slice, cut once from the base**, so the first and last frame
  match at the seam.
- **Cut that slice at the time it is placed, not the time it was built.** If the base gets re-spliced
  and graphics shift, a slice cut at the old time makes the footage jump at the seam and run out
  of sync with the audio for its whole duration. Overlays just slide. Only segments carry
  footage, so only segments need re-cutting and re-rendering.
- **Every overlay needs its end-of-file behaviour set to pass, not repeat.** This one is vicious.
  Chain several short overlays over a long base and the frame scheduler starts duplicating
  output frames on a periodic cadence — measured at exactly one in four. The output is
  dead-even constant frame rate, so every tool reads it as perfectly fine, but the content only
  changes about 18 times a second wearing a 24fps costume. Visible judder, worst on smooth
  motion. Every input measures clean on its own, so you will keep "fixing" a zoom that was
  never broken.
  **Detect it by counting exactly duplicate frames in the output: clean is under 3%, the bug is
  around 25%. Wire that check into the assemble script and make it fail above 8%.** Do not
  mask it by forcing a frame rate — the output is already constant.
  The one exception is a deliberately held frame, like an outro push-in that should not zoom
  back out. That one gets `repeat`.
- **Do not use frame padding to hold a zoom.** It never reaches end of file and can balloon a
  few-second clip into gigabytes before you catch it.
- **Browser segments darken the footage.** Round-tripping through the headless browser costs
  about 3% of luma, so the face visibly dips at every segment seam. Fix it at the root, in this
  order:
  1. Do footage motion in FFmpeg instead of the browser. A zoom or a push-in is pure geometry
     and never needs to enter a browser at all. Only reach for a browser segment when the
     reframe needs live graphics revealing behind the moving face.
  2. If it must be a browser segment, render its source frames as PNG rather than the default —
     that halves the dip on its own — then close the remainder with a **gamma** correction at
     assemble time. Gamma, not a flat gain, so it pins black and white and does not clip
     highlights.
- **An FFmpeg zoom on a mid-video slice needs its frame counter reset**, or the zoom comes
  out constant and reads as a hard cut instead of a ramp. Build the slice by trimming inside the
  filtergraph and resetting timestamps, rather than seeking to a start point. This is invisible
  when a part starts at zero, so an intro zoom can work by luck and every later one silently will
  not.
- **Anchor footage motion to measured scene cuts, not nominal ones.** The rendered base drifts
  from the cut sheet — a few hundred milliseconds by the end of a reel — and the transcript
  drifts with it. Detect the real cut with scene detection on the rendered file and use that time.
- **Screen recordings carry black bars.** Run crop detection before compositing one into a card,
  or the bars scale in too and the readable content shrinks. And size the card bigger than feels
  right when you write the CSS: numbers that look generous as CSS render noticeably small.
