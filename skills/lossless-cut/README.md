# lossless-cut skill

Agent skill for lossless video/audio editing (trim, cut, merge, remux, track
extraction, rotation metadata) via ffmpeg stream copy.

It is a headless companion to the [LosslessCut](https://github.com/mifi/lossless-cut)
desktop app by Mikael Finstad: the app itself is a GUI (its CLI and HTTP API only
control a running GUI instance), so this skill re-implements the same operations
with the same ffmpeg semantics — input seeking with `-ss` before `-i`,
`-avoid_negative_ts make_zero`, `-c copy` — and round-trips the app's artifacts:

- `.llc` project files (JSON5, schema v2: `{version, mediaFileName, cutSegments}`,
  auto-saved by the app as `<mediafile>-proj.llc`)
- `Start,End,Name` CSV edit decision lists (seconds)

It also bridges to the `video-use` skill's `edl.json` in both directions.

No LosslessCut source code is vendored here; the helpers are original and only
mirror behavior documented in the app's docs and source. This skill is not
affiliated with the LosslessCut project.

## Requirements

- `ffmpeg` / `ffprobe` on PATH (any modern build)
- Python 3.10+; `pip install json5` (only needed to read `.llc` files written
  by the GUI — files written by this skill are strict JSON)

## Usage

See `SKILL.md`. Helpers are invoked directly:

```bash
python helpers/lossless_ops.py cut input.mp4 -s 12.5 -e 84.0
python helpers/lossless_ops.py export input.mp4          # runs input.mp4-proj.llc
python helpers/llc_io.py to-json input.mp4-proj.llc
```
