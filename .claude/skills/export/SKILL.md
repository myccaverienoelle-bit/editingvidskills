---
name: export
description: Stage 5 of the video pipeline. Promote the newest real render to one unambiguously named final file, retire superseded drafts, and optionally reclaim scratch space. Use when a job is finished and the outputs folder has several passes in it, or when asked to export, finalise, ship, or clean up a video job. Dry run by default.
---

# Skill 5: export

**Its whole job:** turn a messy outputs folder into one unambiguous file.

By the end of a job there is a base cut, a graphics pass, a captions pass, a music pass and two
drafts — and in a week nobody will know which one shipped.

## Promote

Export:

- promotes the newest **real** render to a single clearly named final,
- retires the superseded drafts,
- **keeps** the base cut, the transcript, and the `graphics-build/` source so the job can be
  reopened,
- and drops a copy somewhere convenient, like Downloads.

Name the final after the job, never with a stage suffix:
`projects/<job>/outputs/<job>-final.mp4`.

## Reclaim (separate, and optional)

Render scratch, cached intermediate renders, stray `node_modules`. **Never source footage.
Never the `outputs/` folder.**

## The two rules that make this safe enough to trust

1. **Dry run by default, always.** Both halves print exactly what they would promote, delete
   and keep, and do nothing until an explicit `--apply` flag is passed after reading the plan.
2. **Never delete anything newer than the deliverable.** Put that guard **inside the script
   itself**, comparing modification times, so a future session cannot talk itself past it.

## Before closing the job out

Absorb the corrections. Any note from the final review that should apply to every future video
gets written back into `styles/<style>/style.md` and appended to the `learned` array in
`style.json`. One-off notes are applied and forgotten. **Show the diff before it becomes
standing behaviour.** Because review sub-agents read the style fresh on every pass, an
absorbed correction tightens every future review with no extra wiring.

## Files this skill owns

| Path | What |
|------|------|
| `projects/<job>/outputs/<job>-final.mp4` | The one deliverable. |
| `projects/<job>/outputs/` | Retired drafts removed from here — never the folder itself. |
