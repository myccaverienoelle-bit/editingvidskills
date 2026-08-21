---
name: finishing
description: Stage 4 of the video pipeline. Captions burned in from the remapped transcript, a flat music bed, and a handful of real sound effects, then review. Use when a job has a graphics pass and needs captions, subtitles, music, audio mix, or SFX. Owns caption styling, music levels, SFX discipline, and the durable effects plan.
---

# Skill 4: the finishing pass

**Its whole job:** captions, a music bed, and a few sound effects, then review.

Three sub-steps that can each run alone, but always run **in this order** when run together,
because each one operates on whatever the previous one produced.

## Captions

Burn them in from the remapped transcript (`outputs/transcript-cut.json`), styled from the style
file. Two things designed in from the start:

- **Never caption a file that is already captioned.** Make the script pick its own input rather
  than accepting whatever it is handed.
- **Make captions genuinely optional.** Long form skips them entirely — YouTube serves its own
  and burn-ins clutter a 16:9 frame.

Caption geometry, casing, highlight behaviour and safe-zone position all come from
`styles/<style>/style.json` under `captions.<format>`. Voice comes from `brand.md`, and on this
brand voice is **case dependent by design**: captions mirror the delivery rather than applying a
house style. Read the transcript, decide in one line what this video sounds like, then style to
that — inside the fixed floor (verbatim, no rewrites, digits for numerals, profanity kept,
emphasis carried by the word highlight and never by capitals).

**Captions never overlap the PiP.** In short form explainer the block is bottom-anchored at
y=1600 and grows upward, capped at two lines at 56px — a third line climbs into the face. If a
line will not fit in two, break the caption; never shrink the type.

## Music

- A **flat bed at about −18 dB**. No ducking. No fade in. A short fade out on the tail.
- The track is **user-supplied and licensed**. The skill never downloads one.
- Ducking and fade-in exist as **opt-in flags** and you should almost never reach for them. If
  the bed is not audible enough, **change the level, do not add a sidechain**.

## Sound effects

- **Sparse.** A handful of moments per video, not a hit on every cut.
- **Real sample files at around −10 dB**, from `assets/sfx/` — a library that grows over time.
- **Never a synthesised tone.** A generated sine wave is instantly recognisable as
  not-a-sound-effect. If there are no samples, **skip the step rather than fabricate one**.

## Both audio passes

**Music and SFX are pure audio passes. Copy the video stream, never re-encode it.**

**Write the effects plan and the filter graph out to disk.** When a graphics tweak later
re-renders the base, re-apply the exact same plan instead of re-deciding every placement.

## Review

Render, then review with the `watch` skill in sub-agents: technical QA as a checklist first, then
composition as its own named step. Caption-specific items for the technical pass — captions
never cover the face, never break the safe zone, never sit under a graphic, and every line is
readable for its full duration.

## Files this skill owns

| Path | What |
|------|------|
| `projects/<job>/outputs/captions-pass.mp4` | Graphics pass with captions burned in. |
| `projects/<job>/outputs/music-pass.mp4` | Captions pass with the bed under it. |
| `projects/<job>/outputs/effects-plan.json` | The SFX placements and levels. Durable — re-applied, not re-decided. |
| `projects/<job>/outputs/effects-filtergraph.txt` | The exact filter graph used. |
