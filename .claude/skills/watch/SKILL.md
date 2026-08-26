---
name: watch
description: Give the editor eyes. Extract frames from a video at exact timestamps so Claude can look at any moment on screen — spot checks, join checks, contact sheets, scene-cut detection and the two-pass review protocol. Use whenever a render needs reviewing, a cut needs checking visually, a graphic's placement needs verifying, or anyone asks whether something looks right. Works with FFmpeg alone; no plugin required.
---

# Watch

**Its whole job:** let Claude look at the footage instead of guessing from the transcript.

Claude cannot play a video, but it can read an image. FFmpeg turns any moment into an image.
That is the entire mechanism — and it is enough to work the way an editor works: make a
change, watch it back, spot what is off, fix it, repeat.

**Frame extraction, not a video understanding model.** Control is the point: pick exactly where
to look, so the seam between two specific graphics can be inspected rather than being handed a
summary of the clip.

## The commands

One frame at an exact time — the workhorse. `-ss` before `-i` seeks fast:

```bash
ffmpeg -v error -ss 42.10 -i input.mp4 -frames:v 1 frame.png
```

A contact sheet, for scanning a stretch at a glance (one frame per second, 4×3 grid):

```bash
ffmpeg -v error -i input.mp4 -vf "fps=1,scale=320:-1,tile=4x3" -frames:v 1 sheet.png
```

Every frame across a short window, for studying motion:

```bash
ffmpeg -v error -ss 41.8 -t 1.5 -i input.mp4 -vf fps=12 win_%03d.png
```

Where the picture actually changes — real cut detection on the rendered file, which is what
footage motion must anchor to rather than nominal cut-sheet times:

```bash
ffmpeg -i input.mp4 -vf "select='gt(scene,0.3)',showinfo" -f null - 2>&1 | grep -oE 'pts_time:[0-9.]+'
```

Brightness per frame, for catching the luma dip at a browser-segment seam:

```bash
ffprobe -v error -f lavfi -i "movie=input.mp4,signalstats" \
  -show_entries frame_tags=lavfi.signalstats.YAVG -of csv=p=0
```

Duplicate-frame count, for the overlay judder bug — clean is under 3%, the bug is around 25%:

```bash
ffmpeg -i input.mp4 -vf mpdecimate -loglevel debug -f null - 2>&1 | grep -c 'drop_count'
```

## Where to look

Never sample a clip generally. Look at the moments that carry a decision:

| Question | Where to pull frames |
|---|---|
| Does this join work? | Last frame before, first frame after. Two frames, compared. |
| Is this graphic placed right? | Its in-point + 0.5s, its midpoint, its out-point − 0.5s. |
| Did the asset survive its whole window? | Every second across the window, plus the final frame. |
| Is the speaker good here? | In-point + 0.5s, midpoint, out-point − 0.5s. |
| Does the seam dip in brightness? | Ten frames either side, plus the YAVG trace. |
| What is this footage even of? | Contact sheet first, then targeted frames. |

## Rules

- **Reviews run in sub-agents, never the main session.** Frame dumps flood the context window.
  Send the review out, get findings back as timestamped items.
- **Two distinct passes.** Technical QA first as a checklist — stretched assets, vanished
  elements, wrong colours, brightness dips. All binary, all catchable. Then **composition as its
  own named step**: "why is that at the top", "that's tiny", "does this make sense". A
  checklist-driven reviewer skips straight past composition while looking directly at the frames
  that show the problem. Running composition separately is the single most useful thing in this
  pipeline.
- **Early spot review after the first ~10% of a build**, not just at the end. A wrong placement
  habit caught once is a fix; caught at the end it is a rebuild.
- **Name the timestamp in every finding.** "The chip is too low" is unusable. "At 42.6 the chip
  sits 40px into the bottom safe band" is a fix.
- **Delete frames when the pass is done.** They are regenerable and they are large.

## Proxies

Full-resolution footage is never needed to look at it. When the source is huge or remote, work
from a proxy and keep the original untouched for the final render:

```bash
ffmpeg -v error -i source.mov -vf "scale=640:-2,fps=12" -c:v libx264 -crf 32 -preset veryfast \
  -c:a aac -b:a 64k -ac 1 proxy.mp4
```

Forty minutes of talking head comes out small enough to move around, and every frame in it is
still a frame. Cut decisions made against a proxy apply unchanged to the original, because the
timings are identical.
