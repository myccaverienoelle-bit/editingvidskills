# brand.md

The one file you personalise. Every style file refers to colours as `$accent` or `$bg` instead of
hardcoding hex values, so changing one brand colour recolours every graphic in every style at
once.

Source: the Algorism theme tokens, sampled from the algorism.org hero, 21 Aug 2026.

> **Still to fill:** caption voice, default hook text, and the mishear list. Colours and fonts are
> done. The remaining `TODO`s are marked below.

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

TODO — two or three sentences on how captions should sound. Casing, punctuation, whether
you swear, whether numerals stay numerals, how much a caption is allowed to differ from what
was actually said.

## Default hook text

TODO — the line that opens a video when the footage has not supplied one.

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
| TODO | TODO |

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
  "caption_voice": "TODO",
  "default_hook": "TODO",
  "misheards": [
    {"heard": "cloud", "correct": "Claude"},
    {"heard": "algorithm", "correct": "Algorism", "verify_in_context": true}
  ]
}
```

## The interview — what is left

1. ~~Six colours.~~ Done, from the Algorism tokens. Verify against DevTools once.
2. ~~Display and caption fonts.~~ Done, files vendored.
3. **How should captions sound?** Casing, punctuation, profanity, numerals.
4. **Default hook text.**
5. **Which words does WhisperX get wrong on this channel?** Your own name, product names,
   recurring jargon. The rough cut's unknown-word pass will grow the list from there.
6. **Which format do you mostly cut** — short form explainer, short form raw, long form? That
   decides which style file gets built out first.
