# brand.md

The one file you personalise. Every style file refers to colours as `$accent` or `$bg` instead of
hardcoding hex values, so changing one brand colour recolours every graphic in every style at
once.

> **Status: NOT FILLED IN.** Every `TODO` below is a field the interview has to fill. Do not run a
> job against this file while any `TODO` remains — a blank field becomes a guess, and a guess
> becomes standing behaviour. Ask the questions in "The interview" at the bottom, then delete
> this block.

## Colours

Six colours, each with a role, each with one hex value. Six is deliberately few: a palette with
twelve entries is a palette the editor will use badly. Keep `bg` and `ink` at readable contrast,
and let `accent` be your one bold brand colour, used sparingly.

| Token | Role | Hex |
|-------|------|-----|
| `bg` | Background base | TODO |
| `rule` | Thin lines, grid, hairlines | TODO |
| `accent` | The one loud colour | TODO |
| `accent-soft` | A quieter tint of it, for gradients and decoration | TODO |
| `ink` | Dark title text | TODO |
| `muted` | Subheads and labels | TODO |

## Fonts

Real font files live in `assets/fonts/`. Renders cannot rely on system fonts.

| Role | Family | File |
|------|--------|------|
| Display — titles, stats, hero type | TODO | TODO |
| Caption — burned-in captions | TODO | TODO |

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
| TODO | TODO |

Only ever auto-apply single word, whole word swaps. A two-word-into-one fix would change
the word count and break every timestamp downstream — those get flagged for a human.

## Machine-readable block

The skills parse this. Keep it in sync with the tables above — same values, twice, on purpose.

```json
{
  "colors": {
    "bg": "TODO",
    "rule": "TODO",
    "accent": "TODO",
    "accent-soft": "TODO",
    "ink": "TODO",
    "muted": "TODO"
  },
  "fonts": {
    "display": {"family": "TODO", "file": "assets/fonts/TODO"},
    "caption": {"family": "TODO", "file": "assets/fonts/TODO"}
  },
  "caption_voice": "TODO",
  "default_hook": "TODO",
  "misheards": [
    {"heard": "cloud", "correct": "Claude"}
  ]
}
```

## The interview

Ask all of these. Do not leave any field blank, and do not infer a value from another answer.

1. Six colours, one hex each: background base, hairline/rule, the one loud accent, a soft tint of
   that accent, dark title ink, muted subhead grey. If they only have a brand accent, derive the
   other five as a proposal and get them confirmed — proposed and confirmed is fine, silently
   invented is not.
2. Display font and caption font, by name, plus where the files are. If they do not have files,
   that is a task before the first render, not a shrug.
3. How should captions sound? Casing, punctuation, profanity, numerals.
4. Default hook text.
5. Which words does WhisperX get wrong on their channel? Their own name, their product
   names, recurring jargon. Get at least the obvious ones now; the rough cut's unknown-word
   pass will grow the list.
6. Which format do they mostly cut — short form explainer, short form raw, long form? That
   decides which style file gets built out first.
