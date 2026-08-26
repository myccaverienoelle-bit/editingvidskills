# Algorism Founder Series — project memory

## Session 1 — 2026-08-26

**Strategy:** Cut the 40:19 single-take founder session (C0128.MP4, native-vertical
4K 25fps, rotation=90 metadata) into 23 short-form clips: an 8-part numbered
spine ("Meet Algorism — Part N") plus 15 unnumbered satellites, 9:16 primary,
6-clip 1:1 variety set for LinkedIn. Honesty-first per the brand edit spec:
admissions unbroken, qualifiers kept, no gloss, no music, no grade.

**Decisions:**
- Footage is take-based with retakes; best takes selected per beat. Final
  selection uses only single continuous takes — zero internal cuts anywhere,
  the most Law-1-honest edit available.
- No biographical origin exists in the footage; Part 3 uses the honest
  "not a super techie guy / can't sit back and do nothing" run instead.
- User steer mid-session: personal anecdotes convert — barbecue story,
  Cold War memory, and Copilot/terrible-speller anecdotes added as
  satellites; the two wonkiest policy-discourse clips (governance debate,
  alignment-values debate) dropped for storyline cohesion.
- Captions: .ass with two named styles (this ffmpeg's SRT decoder strips
  inline override tags) — Base = Jost white natural-case ≤4-word chunks,
  Key = Cormorant Garamond copper #B85C38, selected by word-sequence time
  span. MarginV keeps captions ~31% up (9:16) / ~27% (1:1).
- Lower-third John Jerome — Founder, Algorism, 0–3s, alpha fades.
  End-frame: 1.5s ALGORISM copper-on-cream card appended with identical
  encode params. Loudnorm two-pass -14 LUFS / -1 dBTP per clip.
- SPINE-08 is the only hard-CTA clip: copper algorism.org drawtext overlay
  from "let's work together" onward; that overlay is its single copper use.
- SAT-06 caption corrects one ASR mishear ("algorithms" → "Algorism").
- Skipped as standalone: none of the selected; the phone-listening anecdote
  ships as SAT-12 framed exactly as he tells it (user call).

**Reasoning log:**
- 9:16 = full-frame downscale (source is native 9:16 4K) — crispest possible.
- 1:1 = face-anchored square crop, face_y=0.456, face at 40% of frame.
- ElevenLabs key rotated mid-session; STT-scoped key in
  skills/video-use/.env (gitignored). Transcript cached at
  <scratchpad>/footage/edit/transcripts/C0128.json (12,819 tokens, 6,409 words).
- Dropbox egress is platform-blocked (uc*.dl.dropboxusercontent.com 403 at
  gateway regardless of user allowlist); footage came via user's work
  Google Drive share link (drive.usercontent.google.com + confirm token).

**Late-session fixes (user feedback):**
- Camera had slow drift (user caught it in playback; confirmed via
  background difference-blend). Fixed with vid.stab virtual tripod
  (tripod=1 both passes) at output resolution; full re-render.
- 1:1 squares initially mistracked (detect ran on the tight crop where
  the body dominates → over-zoom, off-center). Fixed: stabilize on the
  full 1080x1920 frame, crop square after the transform.

**Delivered:** all 29 files (23×9:16 + 6×1:1) via chat, QC-passed
(durations exact, -14 LUFS, framing/caption/keyline/end-frame verified
on contact sheets and spot frames). Files >30MiB shipped as CRF21-22
delivery transcodes (visually transparent); pristine CRF18 masters
remained in the session scratchpad (ephemeral — regenerate via
specs/*.json + make_clip.py if ever needed).

**Outstanding:** none. Regenerating any clip: put C0128.MP4 at the
spec's source path, transcript JSON at its transcript path, run
`python3 make_clip.py specs/<ID>.json`.

## Session 1 addendum — v3 final (same day)

User feedback after v2 delivery: residual shakiness + clips too loud.
1. Tripod-mode vid.stab was ADDING per-frame micro-jitter (measured 2x
   raw). Replaced with relative stabilization, smoothing=75, shakiness=8,
   accuracy=15 — measured smoother than the raw camera (p95 ~0.4 vs 0.64
   on the background-strip consecutive-frame metric).
2. Loudness retargeted -14 → -16 LUFS integrated, TP -1.5.
3. Root-caused a brutal batch bug: a runner feeding its loop from a file
   via stdin let every ffmpeg child consume that file as interactive
   commands — 'q' in "SPINE-01_sq" quit encodes mid-clip (deterministic
   truncated stubs). Fix: -nostdin + stdin=DEVNULL in run(), </dev/null
   in runners. All render paths now guarded.
4. Priority-ordered rendering (posting order, not alphabetical) with
   rolling wave delivery; every delivered file duration+LUFS-verified.
Final v3 set: 29/29 delivered, QC 0 failures.
