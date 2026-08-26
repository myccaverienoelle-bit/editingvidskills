---
name: lossless-cut
description: Lossless video/audio editing via ffmpeg stream copy — trim, cut segments, merge/concat, remux containers, extract or drop tracks, fix rotation — with zero quality loss and near-instant speed. Mirrors the LosslessCut desktop app's semantics and round-trips its .llc project files and CSV EDLs, so cut lists marked in the GUI can be executed here and vice versa. Use for rough-cutting large footage, discarding gigabytes before a fine edit, container swaps, and track surgery.
---

# Lossless Cut

Headless companion to the [LosslessCut](https://github.com/mifi/lossless-cut) desktop app. The app is a GUI; its power is ffmpeg stream copy (`-c copy`). This skill drives the same operations directly, with the same flag semantics the app uses, and reads/writes the app's project files so the user can move between their GUI and this agent freely.

## When to use this vs `video-use`

- **This skill (lossless):** rough cuts, trimming dead air off long recordings, splitting/merging camera files, container remux (MKV→MP4), removing/extracting audio or subtitle tracks, rotation fixes, cutting away gigabytes *before* transcription. Zero quality loss, near-instant, but **cut starts land on keyframes** and there are no fades, overlays, subtitles, or grades.
- **`video-use` (re-encode):** frame/word-precise cuts, audio fades at boundaries, overlays, burned subtitles, color grades — the fine edit.
- **Best together:** losslessly pre-trim the keepers out of long raw footage first (cheaper transcription, faster iteration), then run the `video-use` pipeline on the survivors. Or execute a cut list the user already marked in the LosslessCut GUI on their machine.

If the user asks for anything that changes pixels or samples (fades, subtitles, overlays, grades, resizes, speed changes), that is not lossless — switch to `video-use`.

## Hard rules

1. **`-c copy` means cuts snap to keyframes.** A cut's effective start is the keyframe at or before the requested time (input seeking, `-ss` before `-i`, `-avoid_negative_ts make_zero` — exactly what the app's default "keyframe cut" mode does). Expect up to one GOP (often 1–10s on consumer cameras) of extra leading content. When the exact boundary matters, run `snap`/`keyframes` first and tell the user where the cut will really land. Never promise frame-accuracy from a lossless cut.
2. **Never combine `-c copy` with any filter.** Filters force decoding; that's a re-encode and belongs to `video-use`.
3. **Merge only files with identical codec parameters** (same camera/settings). The `merge` helper probes and warns on mismatch — treat the warning as a stop-and-ask.
4. **Sources are read-only.** All outputs go to `<videos_dir>/edit/` (helpers default to this). Never write into the skill directory; never overwrite an input (helpers refuse).
5. **Verify with `ffprobe` after every operation** — duration ≈ expected, streams present, file plays (spot-check a frame if in doubt). Stream copy fails silently more often than it errors.
6. **Confirm the plan before cutting**, same contract as `video-use`: describe segments in plain English (with keyframe-snapped times), get a yes, then execute.
7. **A `.llc` file next to footage is the user's intent.** LosslessCut auto-saves projects as `<mediafile>-proj.llc` beside the media. If one exists, read it, summarize its segments, and ask whether to execute it — do not silently ignore or overwrite it.

## Helpers

All in `helpers/` next to this file (resolve paths relative to this SKILL.md). Requirements: `ffmpeg`/`ffprobe` on PATH; `pip install json5` for reading GUI-written `.llc` files.

`lossless_ops.py` — the operations (each prints its ffmpeg command before running):

- `keyframes <file> [--start S --end E]` — keyframe timestamps, for planning cuts.
- `snap <file> <t> [--direction prev|next|nearest]` — where a cut at `t` will really land.
- `cut <file> -s A [-e B] [-o out] [--accurate]` — one lossless cut. `--accurate` seeks after `-i` (the app's "normal cut" mode; mainly useful for audio-only files, still keyframe-bound for video).
- `export <file> [--project p.llc] [--outdir D]` — one output file per selected segment of a project (default project: `<file>-proj.llc`).
- `merge -o out <in1> <in2> …` [--faststart] — concat-demuxer lossless join.
- `remux <file> -o out.mp4` — container swap, streams untouched.
- `extract-tracks <file> [--outdir D]` — every video/audio/subtitle stream to its own file (MKV/MKA/MKS wrappers hold anything).
- `rotate <file> --degrees 90` — rotation metadata only, pixels untouched.

`llc_io.py` — formats:

- `to-json p.llc` / `from-json segs.json -o p.llc` — LosslessCut project ⇄ strict JSON.
- `to-csv p.llc -o e.csv` / `from-csv e.csv -o p.llc` — the app's `Start,End,Name` CSV EDL (seconds).
- `from-edl edl.json` — a `video-use` EDL → one `<source>-proj.llc` per source, openable in the GUI.
- `to-edl p.llc --media <path> -o edl.json` — GUI-marked segments → a `video-use` EDL skeleton to feed its render pipeline.

## Typical flows

**Rough-cut then fine-edit:** inventory with `ffprobe` → propose keep-ranges (keyframe-snapped, confirmed with the user) → `cut`/`export` keepers into `edit/` → continue in `video-use` on the trimmed files (transcribe only the keepers).

**Execute a GUI project:** user drops footage + `X.mp4-proj.llc` → `llc_io.py to-json` to read it → summarize segments and confirm → `lossless_ops.py export X.mp4` → verify durations → report.

**Hand a plan back to the GUI:** build segments here (e.g. from a `video-use` `edl.json` via `from-edl`, or `from-json`) → the user opens the media in LosslessCut on their machine and the project file loads with your segments for manual tweaking.

**Track surgery:** `extract-tracks` / `remux` / merge an external audio or subtitle file in by remuxing with extra `-i` inputs — for anything beyond the helpers, compose the ffmpeg command yourself, keeping rules 1–5.

## Verification checklist (after each operation)

- `ffprobe` duration within tolerance: for keyframe cuts, `actual ≥ requested` and `actual − requested <` one GOP; for merges, sum of parts ±0.1s.
- Same stream count/codecs as intended (`-show_streams`).
- For merges: play direction — spot-check the first seconds after each join point (`video-use`'s `timeline_view.py` works on any file if installed).
- Report requested vs actual boundaries to the user; surprises are for them to judge, not to hide.
