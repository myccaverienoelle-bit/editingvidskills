---
name: rough-cut
description: Stage 1 of the video pipeline. Turn raw talking-head clips into the shortest cut that still delivers the value. Use when a job has footage in projects/<job>/raw/ and no cut yet, or when asked to transcribe, cut, trim, or assemble a rough cut. Owns WhisperX transcription, the cutsheet, the FFmpeg splice, and the remapped transcript every later stage reads.
---

# Skill 1: the rough cut

**Its whole job:** turn raw talking-head clips into the shortest cut that still delivers the value.

Claude cannot hear audio. It has no idea where a cut should land unless something tells it the
sub-second timing of every word. WhisperX gives exactly that — word level timestamps with
forced alignment, tight enough that cuts land on the breath instead of near it. That is why this
stage lands every time: cutting raw footage down is a pure transcript problem.

## The five steps

1. **Transcribe once**, with WhisperX `large-v3` and wav2vec2 alignment. Write the result to
   `projects/<job>/transcript/transcript.json`. Re-running skips straight to that saved copy.
   This is the slowest step in the whole pipeline and it should run **exactly once per video,
   ever**.
2. **Also transcribe `broll/`.** Creators narrate direction inside their own B-roll takes — "zoom
   in here", "use this for the pricing bit" — and that direction never appears in the main script.
   Stage 2 reads it.
3. **Write `transcript/cutsheet.json`**: an ordered list of segments, each with a source clip, a
   start, an end, and the line of text it contains. That text field matters. It lets the whole edit
   be sanity-checked by reading it, without watching anything.
4. **Splice with a single FFmpeg filtergraph.** One trim per kept segment, concat, then polish
   the audio once on the assembled track.
5. **Write out a second transcript, remapped onto the edited timeline**, to
   `outputs/transcript-cut.json`. Every downstream skill reads that file. Nothing re-transcribes,
   ever.

## Performance is not in the transcript

The transcript records what was said. It records nothing about how it was said — and how it was
said is half of what makes a talking head worth watching. A line that reads redundant on the
page can be the moment the speaker is most alive. A line that reads clean can be delivered flat.

So the cut splits into two tiers, and **only one of them is safe to decide blind.**

### Tier 1 — mechanical kills. Auto-apply.

These carry no performance value by definition, so nothing is lost by deciding them from
timings alone:

- Silences over about 0.4 seconds.
- Stutters and false starts.
- Throat clears, and "let me start over".
- Superseded takes: when a line was recorded several times, **take the last one, always.** It is
  the warmest delivery, and comparing takes wastes an hour.
- Any preamble before the hook lands. **Every video opens on the hook.**
- Vestigial filler words — but **preserve cadence**. Do not surgically remove every "like". Some
  of them are rhythm.

### Tier 2 — editorial kills. Never auto-apply.

Tangents, repetition, weaker phrasings of a point made better elsewhere, anything cut because
it "does not serve the hook". These are exactly the judgments the transcript cannot support.
Each one goes into the cut sheet as a **proposal** — `"proposed": true`, with the segment still
present — and stays a proposal until it is cleared by eyes, either the creator's or a review
sub-agent's.

Every Tier 2 proposal carries an evidence pack, so clearing it takes seconds instead of a
rewatch:

1. **Three frames** — 0.5s after the in-point, the midpoint, and 0.5s before the out-point.
   Extract them at exactly those times; do not sample the clip generally.
2. **Delivery signals for the span**, measured against the video's own median: RMS energy,
   speaking rate in words per second from the word timings, and the pause pattern. A span in
   the top decile for energy or pace is a **performance peak — protect it unless it is a genuine
   tangent**, and say so in the proposal.
3. **The text either side of the join**, so the seam can be read as a sentence.

### The protect list

Before cutting, ask the creator for anything that survives no matter what — a timestamp, a
phrase, "the bit where I get animated about pricing". Those spans are never proposed for
removal, and the cut sheet records why they were kept.

### Check every join with frames, not just the text

A join can read perfectly and still look wrong: the speaker's head jumps position, a hand is
mid-gesture, the eyeline changes. Pull the last frame before and the first frame after each
join and compare them. This catches the class of error the transcript cannot represent at all.

Where audio is all that is available, say so explicitly and hand back the cut sheet as a
proposal in full — never as an applied cut.

## The gotchas that cost the most

- **Stream copy does not work on arbitrary cut points.** `-c copy` desyncs audio and video.
  Re-encode each segment with hardware acceleration instead. Still fast — around fifteen
  seconds for a minute of output.
- **Never encode audio per segment.** Ride it through the cut lossless, then amplify and limit
  **once** on the assembled track. Encoding each piece separately puts a click at every join.
- **Do not auto-snap cuts to silence.** Word level alignment is the whole advantage. Silence
  detection will drag deliberate boundaries into filler words and awkward pauses.
- **Retake seams clip word tails.** When a speaker cuts in on top of their own previous word,
  the kept word can sound chopped. Extend the out point slightly into the stumble and fade
  that segment's audio to zero over its last fraction of a second, so the word rings out instead
  of hard-clipping.
- **Stumbles hide inside long word spans.** WhisperX sometimes merges a stumble and its
  retake into one word span over 1.2 seconds. If a word's duration looks wrong for what it
  should sound like, that is the signal: run silence detection *across that span only* before
  deciding the cut.
- **The transcript will mishear things.** Cross-check before killing a line. "Claude" becoming
  "cloud" makes a perfectly good sentence look broken.
- **Screen recordings can carry a chapter track** that inflates the reported duration and leaves
  a black tail on the end. Probe with `ffprobe` and strip chapters when re-encoding.

## The unknown-word pass

Built on top of the fixed mishear list in `brand.md`, and run automatically:

1. Compare every transcript word against a system dictionary.
2. Print only the words that are neither ordinary English nor already known.
3. Judge each one in context.
4. A recurring brand name goes into the permanent list in `brand.md`. A one-off goes into a
   per-video list inside the job.

**Only ever auto-apply single word, whole word swaps.** A two-word-into-one fix changes the
word count and breaks every timestamp downstream — flag those, never apply them.

## Files this skill owns

| Path | What |
|------|------|
| `projects/<job>/transcript/transcript.json` | Raw transcript, word-level. Written once. |
| `projects/<job>/transcript/broll.json` | Transcript of the B-roll takes, for the direction inside them. |
| `projects/<job>/transcript/cutsheet.json` | Ordered kept segments: source, start, end, text. |
| `projects/<job>/outputs/base-cut.mp4` | The assembled rough cut. Never re-rendered to change a graphic. |
| `projects/<job>/outputs/transcript-cut.json` | Transcript remapped onto the edited timeline. The downstream contract. |

## Done means

- `cutsheet.json` reads as a coherent script from top to bottom.
- The cut opens on the hook.
- No click at any join.
- `transcript-cut.json` timings match the rendered file (spot-check three points, including the
  last ten seconds).
- Nothing in `raw/` was moved or modified.
