# Style: editorial

Starter style. It is deliberately opinionated and deliberately concrete, because the bar for a
style file is this: **you should be able to make new videos in this style from this file alone,
without ever rewatching a reference.** If it reads like a mood board full of adjectives, it is not
done.

Everything here is tuned by editing it, not by overriding it per job. Corrections from a final
review that should apply to every future video get written back here (and into the `learned`
array in `style.json`) before the job closes out.

Colours are always tokens — `$bg`, `$rule`, `$accent`, `$accent-soft`, `$ink`, `$muted` — resolved
from `brand.md`. Never a hex value in this file.

## Scene vocabulary

The named scene types this style uses. A beat is always one of these; if it is not, the plan is
wrong or the vocabulary needs a new entry (which is a style edit, not a job decision).

| Name | What it is | When |
|------|-----------|------|
| **Head** | Talking head, full frame, no graphic. | Connective tissue, asides, emotional delivery. The default. |
| **Head + chip** | Head with a small lower-third chip under the chin. | A name, a number, a label that supports the line without taking the frame. |
| **Card** | Full-frame or panel typographic card. | Hook and punchlines only. Give it motion and a visual element, never a wall of type. |
| **Stat** | One big number, counted up or flipped. | A single figure is the payoff. |
| **Screenshot** | The real screenshot or screen recording, with a slow pan or push. | Anything showable. Reach for this before a card. |
| **Diagram** | Boxes, connectors, a process drawing itself in. | A system or a sequence a picture makes instantly clearer. |
| **Takeover** | Full-frame cutaway that replaces the footage. | A beat that stands on its own for 3s or more. |
| **Zoom** | Push-in or reframe on the footage itself, no browser. | Emphasis inside a head beat. Pure geometry — done in FFmpeg. |
| **B-roll slot** | A generated or supplied clip filling the window. | No real footage exists for the beat. |

## Rhythm

Measured pacing, not vibes:

- Head beats run 4–9 seconds. Longer than 12 seconds of unbroken head needs a zoom or a chip.
- Graphic beats run 2.5–6 seconds. A graphic under 2 seconds reads as a flash.
- No more than two graphic beats back to back before returning to head. Three in a row is a
  slideshow.
- Roughly one graphic per 4–6 lines of transcript in short form explainer; one per 8–12 in long
  form. If the plan is denser than that, the plan is wrong, not the pacing.
- Every video opens on the hook, within the first 1.5 seconds. No preamble ever survives.

## Transitions — the mechanic at every boundary

| Boundary | Mechanic |
|----------|----------|
| Head → head (a cut inside a sentence) | Hard cut. No dissolve, ever. |
| Head → takeover | Takeover wipes in from the direction of the last motion, 0.35s, `power3.out`. Footage holds underneath. |
| Takeover → head | Takeover clears in 0.3s, `power2.inOut`. The head frame is already live behind it. |
| Graphic → graphic | Hard cut on the content, PiP stays put. The picture-in-picture never re-enters between two graphics. |
| Head → head + chip | Chip rises 24px and fades over 0.3s, `power2.out`. |
| Into a b-roll slot | Hard cut in, hard cut out. Generated footage never dissolves. |
| Outro | Push-in holds on the last frame. Deliberately held — this is the one place a repeat tail is correct. |

## Picture-in-picture geometry

Exact, because "top right, smallish" is how two videos end up not matching.

- **Short form (1080×1920):** PiP occupies the bottom band. Frame 620×826, centred on x, top
  edge at y=940. 24px corner radius, 1px `$rule` border, no shadow.
- **Long form (1920×1080):** PiP is bottom-right. Frame 480×270, right edge 96px from frame
  right, bottom edge 96px from frame bottom. 16px corner radius, 1px `$rule` border.
- **The PiP enters once per graphics run and holds until the run ends.** Chain everything
  between entries. Bouncing between full frame and PiP and back is the single most
  amateur-looking thing an AI editor does. Hard cuts between card contents are fine. A
  full-screen bounce never is.
- Reframe is always done through layout: the `<video>` sits inside a wrapper with hidden
  overflow, and the wrapper's `left/top/width/height` animate. Never a transform on the video.

## Title card anatomy

Top to bottom, on `$bg` with a fine grid at 4% `$rule`:

1. Eyebrow — caption font, 32px short form / 24px long form, `$muted`, letter-spaced 0.08em, uppercase.
2. Rule — 2px `$accent`, 96px wide, draws in left to right over 0.4s.
3. Headline — display font, 120px short form / 84px long form, `$ink`, max three lines, clip-mask reveal per line, staggered 0.12s.
4. Support line — caption font, 40px / 30px, `$muted`, appears 0.4s after the headline settles.
5. One visual element — icon, mark, or screenshot fragment — carrying `$accent` on exactly one element in the frame.

## Camera behaviour inside a scene

- Every card has a slow continuous drift: 1.0 → 1.03 scale across its whole window, linear.
  Nothing is ever truly static.
- Screenshots pan or push at 2–4% across the window, anchored on the region that matters,
  measured from the actual frame — never estimated.
- Zooms ramp, they do not snap: `power2.inOut` over at least 0.8s.
- On any beat 20 seconds or longer, something is moving for the entire duration. A count-up
  that finishes at six seconds of a nineteen second beat reads as a frozen frame for thirteen
  seconds.

## Texture

- Background is never flat: a vertical `$bg` → `$accent-soft` gradient at 6% opacity, plus a
  1px grid at 4% `$rule` on 96px pitch, plus a 12% vignette.
- Panels read on their own fill (`$bg` at 92%), never on a backdrop blur — transparent overlays
  have nothing behind them to blur.
- Thin 1px `$accent` highlights on the top edge of raised panels. Low-opacity reflections under
  hero numbers.
- No drop shadows deeper than 24px blur / 8% opacity.

## Which font does which job

- Display font: headlines, stats, big numbers, the hook card. Never body copy.
- Caption font: burned-in captions, eyebrows, labels, chips, support lines, diagram text.
- Primary numbers are 160px minimum. Scale is dramatic or it is not a stat.

## Format behaviour

- **Short form explainer:** graphics live in the top half, face in the bottom. Captions on.
- **Short form raw:** exactly one hook card and nothing else. Captions on.
- **Long form:** full-frame takeovers, lower thirds, no reframe at all. Captions off — YouTube
  serves its own and burn-ins clutter a 16:9 frame. Keep the outro's right 40% clear for end
  screen cards.

## Safe zones

| Format | Frame | Keep key visuals inside |
|--------|-------|--------------------------|
| Short form | 1080×1920 | y 200 to 1620. Top 200px and bottom 300px are background only. |
| Long form | 1920×1080 | Title safe, 10% margins. Outro's right 40% clear. |

The short form bands are not a guideline. The platform UI, the username, the audio tag and the
progress bar all land there.

## Building a style from a reference

Two passes, always:

1. One pass over the full runtime — roughly a hundred scene-detected frames — to get the
   scene vocabulary and the rhythm those scenes alternate in.
2. A second pass at high frame rate on three to five specific boundaries: head into takeover,
   takeover back to head, graphic into graphic, and any weird frame the first pass flagged.

The first pass tells you what the scenes are. Only the second pass tells you how they join.
Writing a style from the first minute of a video produces a mood board every time.

**Distil the pattern, never copy the assets.** Take the mechanic, the pacing, the caption
placement, and map all of it onto your colours and your fonts. The one exception is a reference
that is your own channel, where pulling the literal hex values out verbatim is the entire point.
