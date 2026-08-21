---
name: graphics
description: Stage 2 of the video pipeline. Decide which lines earn a graphic, then build each one as code with HyperFrames and composite it over the base cut. Use when a job has a base cut and needs motion graphics, cards, stats, screenshots, takeovers, zooms, lower thirds, or a graphics plan. Owns the beat plan, the cut sheet validator, the build script, safe zones, and the HyperFrames and FFmpeg composite gotchas.
---

# Skill 2: graphics

**Its whole job:** decide which lines earn a graphic, then build each one.

This is the biggest skill and it has two halves that **stay separate**: plan, then build. Planning
is a judgment problem. Building is an engineering problem. Mixing them produces a plan written
to be easy to build, which is the wrong optimisation.

Read before touching either half: `brand.md`, the job's style file, and
[rules/hyperframes.md](rules/hyperframes.md) + [rules/composite.md](rules/composite.md).

## The plan

Read three things before deciding a single beat:

1. The finished transcript from the rough cut (`outputs/transcript-cut.json`).
2. Any comments left in the script document — pull those out with the document's XML, not
   with a library.
3. The narration inside the B-roll clips (`transcript/broll.json`).

Then, for every beat, answer in order:

### Does this line even need a graphic?

**Default to no.** A graphic on every line is wrong. Plain beats give rhythm and let the face
carry the moment. A beat earns a graphic when:

- it is the hook,
- it names something concrete and showable — a stat, a screenshot, a before and after,
- it is a payoff worth emphasising,
- it describes a process a picture would make instantly clearer,
- or the creator explicitly asked for one.

Leave connective tissue, transitions, asides and emotional delivery **plain**. Those land harder
on the face alone.

### What kind?

Think in rich terms first, then flatten to the small fixed set the build step can handle. The seven
kinds: `stat`, `card`, `screenshot`, `takeover`, `zoom`, `diagram`, `broll-slot`.

**Reach for showing over telling.** Screen recordings, screenshots, diagrams and stats beat text
cards almost every time. Reserve cards for the hook and the punchlines, and even then give
them motion and a visual element rather than a wall of type.

### Where?

| Format | Placement |
|--------|-----------|
| Short form explainer | Graphics in the top half, face in the bottom. |
| Short form raw | Exactly one hook card and nothing else. |
| Long form | Full-frame takeovers, lower thirds, and no reframe at all. |

### What exactly?

Write the actual creative direction: what is on screen, what the hierarchy is, what the hero
element is, and **critically what animates and in what order**. Concrete enough that the build
step is not guessing.

### Output of the plan

A machine-readable cut sheet — ID, window, kind, direction, notes, per beat — plus a human
readable table to review. **Beats with no graphic simply are not in the list.**

```json
{
  "id": "g07",
  "start": 42.10,
  "end": 46.40,
  "kind": "stat",
  "class": "overlay",
  "direction": "Hero number 3,400 counts up from 0 over 1.2s, display font 220px, $accent on the numeral only. Eyebrow 'HOURS SAVED' clip-masks in 0.4s before it. Thin $rule underline draws left-to-right as the count settles.",
  "notes": "Script comment asked for the dashboard screenshot here — conflicts with style's card-only hook rule, flagged."
}
```

## Validate the plan before the build step ever sees it

Run a script over the cut sheet. It fails on:

- a missing required field,
- a `kind` outside the allowed set,
- `start` not before `end`,
- beats not sorted ascending,
- any overlap,
- and the rule that is not obvious: **consecutive beats must either abut exactly or leave a gap
  of more than a second.** Anything in between — a gap of a few tenths — flashes raw
  un-graphiced footage for a fraction of a second during the composite, and almost always
  means the plan meant to abut and did not.

## Safe zones

| Format | Frame | Keep key visuals inside |
|--------|-------|--------------------------|
| Short form | 1080 × 1920 | y 200 to 1620. Top 200px and bottom 300px are background only. |
| Long form | 1920 × 1080 | Title safe, 10% margins. Keep the outro's right 40% clear for end screen cards. |

The short form bands are not a guideline. The platform UI, the username, the audio tag and the
progress bar all land there.

## The build

**Generate the compositions from a script. Do not hand-write HTML per graphic.** A single build
script in `projects/<job>/graphics-build/` holds the shared CSS, the per-graphic markup and the
per-graphic animation, and emits one composition file per part plus a render script and an
assemble script. That folder is the real progress on the job, so it lives in the project, never in a
temp directory.

Classify every part as one of two things. The question is simple: **does it change the footage
underneath, or does it float on top?**

- **Overlay** — a card, a panel, a callout. Renders standalone to a transparent file and
  composites over the base at its timestamp.
- **Segment** — a takeover, a full-screen cutaway, anything that replaces the frame. Renders
  with its own slice of the base footage baked in, as an opaque file that covers the base for its
  window.

**The base rough cut is never re-rendered.** That is the whole point. Editing one graphic means
regenerating one composition, re-rendering one part in seconds, and running one FFmpeg
composite pass over everything. Lock the parts one at a time.

## Non-negotiables

- **Graphics hold until the next part starts.** Never let one fade out early and leave dead air
  before the next.
- **The picture-in-picture enters once per graphics run.** Chain everything between entries.
  Bouncing between full frame and PiP and back is the single most amateur-looking thing an AI
  editor does. Hard cuts between card contents are fine. A full-screen bounce never is.
- **Continuous motion on any beat 20 seconds or longer.** A count-up that finishes at six
  seconds of a nineteen second beat reads as a frozen frame for thirteen seconds. On any long
  beat, write out explicitly what is moving across its entire duration, not just at the entrance.
- **Real assets over recreations.** The actual logo, the actual screenshot, the actual chart, with
  a slow pan or push on it. Never a redrawn approximation.
- **Measure, do not estimate.** Pull the actual frame, measure the element's bounding box in
  pixels, then set the zoom from that measurement.
- **Check the tail of every clip, not just the start.** A retake seam leaves a bad frame right at
  the out point, and nobody watches the last second.
- **Assets outlast their window.** Give every part about half a second of tail margin past its
  nominal end, so a slightly late composite boundary never exposes a missing asset.
- **Local direction never silently overrides a style convention.** If a script comment says put
  the chip in the upper third and the style says chips sit under the chin, that is a conflict to
  flag, not a decision to make quietly. Following the more recent instruction is recency bias, not
  judgment.

## Review

Render, then review with the `watch` skill in **sub-agents** — frame dumps flood the main
context. Two distinct passes, technical QA as a checklist first, then composition as its own
named step. Run an early spot review after the first ~10% of the parts are built, not just at the
end. See the review-loop section of `CLAUDE.md` for the full contract.

## Files this skill owns

| Path | What |
|------|------|
| `projects/<job>/graphics-build/` | Build script, compositions, render script, assemble script. Durable. |
| `projects/<job>/graphics-build/cutsheet-graphics.json` | The validated beat plan. |
| `projects/<job>/outputs/graphics-pass.mp4` | Base cut with graphics composited. |
