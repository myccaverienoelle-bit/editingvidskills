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

**Outstanding:**
- Batch render + per-clip QC (frames at boundaries, duration, loudness).
- Deliver clips to user; decide final delivery channel for 28 files.
