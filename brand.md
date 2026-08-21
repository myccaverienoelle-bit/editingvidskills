# brand.md

The one file you personalise. Every style file refers to colours as `$accent` or `$bg` instead of
hardcoding hex values, so changing one brand colour recolours every graphic in every style at
once.

Source: the Algorism theme tokens, sampled from the algorism.org hero, 21 Aug 2026.

> **Status: complete enough to run a job.** Colours, fonts, caption voice and the hook doctrine
> are all set. The mishear list is seeded and grows on its own — the rough cut's unknown-word
> pass surfaces new candidates every video.

> **Colour caveat, carried from the source:** these values were sampled from a screenshot and
> are within ~1–2 shades of production. Verify them in DevTools against the live site before the
> first render — they become the colour of every graphic in every video.

## Colours

Six colours, each with a role, each with one hex value. Six is deliberately few: a palette with
twelve entries is a palette the editor will use badly.

| Token | Role | Hex | From |
|-------|------|-----|------|
| `bg` | Background base | `#0B0C0E` | `--bg-base` |
| `rule` | Thin lines, grid, hairlines | `#2A2B2E` | `--border-subtle` |
| `accent` | The one loud colour | `#B45D3B` | `--accent` |
| `accent-soft` | A quieter tint of it, for gradients and decoration | `#3A2C24` | `--bg-hero-warm` |
| `ink` | Title text | `#F5F3EE` | `--text-display` |
| `muted` | Subheads and labels | `#A8A49C` | `--text-muted` |

**This is a dark palette, so `ink` inverts:** it is still "the colour titles are set in", it is just light
on dark. Nothing downstream should assume `ink` is dark or `bg` is light.

Measured contrast against `bg`: `ink` 17.6:1, `muted` 7.9:1, `accent` 4.3:1. **`accent` is for
large type and non-text elements only** — it clears the 3:1 bar for big display type and misses
4.5:1 for anything small. Same for `#FFF7F2` on `accent` (4.3:1): fine on a 160px number, not
fine on a 24px label.

### Logo mark only — never in a graphic

`#123A63` (deep blue), `#4E9B8A` (teal), `#2C6E9B` (mid blue). These live in the mark and
nowhere else. A graphic that reaches for them has broken the brand, not extended the palette.

## Fonts

Real font files, vendored into `assets/fonts/`. Renders cannot rely on system fonts.

| Role | Family | File |
|------|--------|------|
| Display — titles, stats, hero type, pull quotes | Newsreader (serif, 400, and italic for quotes) | `assets/fonts/Newsreader-Regular.ttf`, `assets/fonts/Newsreader-Italic.ttf` |
| Caption — burned-in captions, labels, eyebrows, UI-ish text | Inter (400, 500) | `assets/fonts/Inter-Regular.ttf`, `assets/fonts/Inter-Medium.ttf` |

Both are OFL 1.1, pulled from Google Fonts. The web stack falls back to Canela/Georgia and
system sans; renders do not fall back at all, so if a weight is missing from `assets/fonts/` it has
to be added there, not assumed.

## Type conventions carried from the web theme

- Display is set at weight **400**, never bold. The serif does the work.
- Headline tracking is tight: `-0.01em`. Line height `1.15`.
- Body/caption line height `1.65`; quotes `1.5`.
- Uppercase labels and buttons are **letter-spaced `0.14em`**; the wordmark `0.18em`.
- **Corner radius is `0` everywhere.** Sharp corners are the look — no rounded cards, no
  rounded caption boxes, no rounded PiP.
- Headlines cap at ~16 characters per line; body copy at ~65 characters.

## Caption voice

**Captions mirror the delivery. They are not a house style applied on top of it.** This is an
educational channel, and the thing that makes teaching land is sounding like a person who
means it — so the caption's job is to carry the way the line was actually said, not to tidy it into
neutral copy.

That makes voice case dependent by design. What is fixed is the floor, not the tone:

- **Verbatim by default.** A caption may drop a filler word the cut kept for rhythm. It may not
  rewrite, compress, or improve a sentence. If the caption and the audio disagree, the viewer
  hears the mismatch even when they cannot name it.
- **Punctuation follows the breath, not the grammar book.** A hard stop mid-sentence gets a
  full stop. A trailing thought gets nothing. Never add a comma the delivery does not take.
- **Emphasis is carried by the highlight, not by capitals.** The per-word `$accent` highlight is
  the emphasis mechanism. No all-caps shouting inside a caption line.
- **Numerals stay numerals.** "3 hours", never "three hours" — a caption is scanned, not read.
- **Profanity is kept if it was said.** Censoring it mid-sentence is the least authentic thing a
  caption can do.
- **Casing is sentence case unless the delivery is doing something else** — a deadpan aside set
  lower-case, a single word landed hard. Sentence case is the default, not the rule.

The tone judgment is per video. Read the transcript first, decide what this one sounds like, and
say so in one line before styling the captions.

## The hook

**Case dependent, and always earned from the footage.** There is no stock hook line, because a
stock hook is exactly the thing that makes an educational audience close the tab.

The problem this doctrine exists to solve: education starts from a receptivity deficit. Nobody
arrives wanting a lesson. The first line has to buy attention before anything can be taught.

Rules for deriving it, every video:

1. **It lands inside the first 1.5 seconds.** No preamble ever survives the cut.
2. **It is a real line from the video, verbatim.** Never written for the edit, never voiced over,
   never assembled from two takes. If the best hook sits at 4:12, move it to the front — that is
   a cut decision, not a fabrication.
3. **It shocks by being unexpectedly true, not by overclaiming.** The pattern interrupt is a
   claim that contradicts what the audience already believes, a number they will not believe, or
   the cost of the thing they are currently doing wrong. Never a fabricated stat, never a promise
   the video does not keep.
4. **It gets paid off within 15 seconds.** An unpaid hook trains the audience to distrust the
   next one, and on an educational channel the next one is the whole business. If nothing in the
   first 15 seconds delivers on the hook, the hook is wrong or the cut is.
5. **It names the stake, not the topic.** "Here's how transcription works" is a topic. "You are
   paying an editor for something a transcript does better" is a stake.

**Fallback, when the footage genuinely supplies nothing:** take the sharpest true claim in the
first sixty seconds and lead with it verbatim. Flag it in the review — a video whose best
available hook is weak is a pre-work problem to fix on the next script, not something to paper
over in the edit.

## Mishear list

WhisperX will reliably mangle product names, your own name, and anything unusual. Write them
out as heard → correct pairs. The rough cut applies them to every transcript automatically,
which means a mishear you fix once is fixed in every future video.

Keep this list here rather than in a separate file. It is brand vocabulary, it changes when your
brand does, and splitting it out just gives you two files to forget about.

| Heard | Correct |
|-------|---------|
| cloud | Claude |
| algorithm | Algorism |

`algorithm → Algorism` is seeded because it is the one this brand will hit constantly, and it is a
safe single word, whole word swap. Check it in context the first time it fires — a line that
genuinely says "algorithm" exists too.

**Only ever auto-apply single word, whole word swaps.** A two-word-into-one fix would change
the word count and break every timestamp downstream — those get flagged for a human.

## Machine-readable block

The skills parse this. Keep it in sync with the tables above — same values, twice, on purpose.

```json
{
  "colors": {
    "bg": "#0B0C0E",
    "rule": "#2A2B2E",
    "accent": "#B45D3B",
    "accent-soft": "#3A2C24",
    "ink": "#F5F3EE",
    "muted": "#A8A49C"
  },
  "colors_logo_only": {
    "brand-blue-deep": "#123A63",
    "brand-teal": "#4E9B8A",
    "brand-blue-mid": "#2C6E9B"
  },
  "fonts": {
    "display": {
      "family": "Newsreader",
      "weight": 400,
      "file": "assets/fonts/Newsreader-Regular.ttf",
      "italic_file": "assets/fonts/Newsreader-Italic.ttf"
    },
    "caption": {
      "family": "Inter",
      "weight": 400,
      "file": "assets/fonts/Inter-Regular.ttf",
      "medium_file": "assets/fonts/Inter-Medium.ttf"
    }
  },
  "type": {
    "radius_px": 0,
    "display_weight": 400,
    "headline_tracking_em": -0.01,
    "headline_line_height": 1.15,
    "body_line_height": 1.65,
    "quote_line_height": 1.5,
    "label_tracking_em": 0.14,
    "wordmark_tracking_em": 0.18,
    "headline_measure_ch": 16,
    "body_measure_ch": 65
  },
  "accent_rules": {
    "min_size_px_for_accent_text": 48,
    "one_accent_element_per_frame": true
  },
  "caption_voice": {
    "mode": "mirror-delivery",
    "verbatim": true,
    "may_drop_fillers": true,
    "may_rewrite": false,
    "case": "sentence-default-delivery-wins",
    "emphasis": "word-highlight",
    "numerals": "digits",
    "profanity": "keep",
    "punctuation": "follows-breath"
  },
  "hook": {
    "mode": "derived-per-video",
    "source": "verbatim-line-from-footage",
    "max_start_s": 1.5,
    "pay_off_within_s": 15,
    "fabricated_claims": false,
    "fallback": "sharpest true claim in the first 60s, verbatim, and flag it in review"
  },
  "misheards": [
    {"heard": "cloud", "correct": "Claude"},
    {"heard": "algorithm", "correct": "Algorism", "verify_in_context": true}
  ]
}
```

## The interview — settled

1. ~~Six colours.~~ Done, from the Algorism tokens. Still verify against DevTools once.
2. ~~Display and caption fonts.~~ Done, files vendored in `assets/fonts/`.
3. ~~Caption voice.~~ Case dependent by design — mirror the delivery, floor rules above.
4. ~~Hook.~~ Case dependent by design — derived per video, doctrine above.
5. **Mishear list — open by design.** Seeded with the two that will fire constantly. The rough
   cut's unknown-word pass prints every word that is neither ordinary English nor already
   known, and recurring ones get promoted into the table above.
6. ~~Primary format.~~ **Short form explainer.** `styles/editorial/` is built out for it.
