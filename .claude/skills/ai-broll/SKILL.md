---
name: ai-broll
description: Stage 3 of the video pipeline. Turn a beat that has no footage into a rendered clip — AI B-roll and generated motion graphics via HyperFrames and the Higgsfield MCP. Use when the graphics plan has broll-slot beats, or when asked to generate footage, motion design scenes, stat reveals, or illustrative clips for beats with nothing shot. Owns the scene templates, the twelve design rules, and the prompt discipline.
---

# Skill 3: AI B-roll

**Its whole job:** turn a beat that has no footage into a rendered clip.

Note what it does **not** do. It does not pick windows in footage already shot — that belongs to
`graphics`. And it does not composite anything into the final video. It generates a clip and
writes a manifest entry, and that is it. Keeping generation separate from placement is what
makes both debuggable.

## Pick the scene template first

Map every slot to one of a small fixed set of scene templates **before writing a prompt**.
Picking the right one up front is most of what stops the output reading generic.

| The beat is about | Reach for |
|-------------------|-----------|
| One big number landing | Stat reveal |
| Several categories at once | Data breakdown |
| Parts of a whole | Pie or donut |
| Things ranked | Podium |
| A system or process | Flowchart |
| "Look what showed up" | Phone notification |
| Old versus new | Before and after |
| Words as the payoff | Kinetic type |

## The twelve design rules

These are what separate motion design from PowerPoint. **Make at least half of them explicit in
every single prompt** rather than hoping the render figures them out.

1. Text never just fades in. Clip mask reveals, or word by word.
2. Nothing animates simultaneously. Stagger everything by at least 0.4 seconds.
3. The background is never flat. Gradient, vignette, or a fine grid.
4. The accent colour appears on exactly one element per scene.
5. Numbers count up or flip. They never just appear.
6. Exits are designed. Elements leave with purpose.
7. Generous whitespace. More than feels right.
8. One focal point per frame. Never more than two things moving.
9. Scale is dramatic. Primary numbers 160px minimum.
10. Connectors and dividers draw in, never appear.
11. Small premium details. Thin highlights, low-opacity reflections.
12. Motion blur on fast travel, removed once settled.

## The failure list

The mirror image of the rules, and what a bad clip always has in it:

- the same layout reused for every beat,
- "fade in" instead of a real entrance,
- no stagger,
- a flat background,
- a vague ease like "smooth" instead of a named one,
- small type,
- no exits,
- too many colours,
- everything moving at once.

## Render rules

- **Render at the base video's exact frame rate, probed, never guessed.** If the base is 23.976
  you pass `24000/1001`, not `24`. A rounded guess drifts out of sync the moment the clip is
  composited back.
- **Every generated clip is silent.** The base voice track keeps playing underneath. If a render
  produces an audio stream anyway, strip it before writing the manifest.
- **Duration is the beat window plus half a second of tail margin.** A clip that ends exactly on
  its boundary is a bug waiting for the next composite.

## Generated assets mid-edit

Higgsfield earns its place twice. Once for B-roll, and once for stills: HTML can only draw text,
charts and screen recordings, so when a graphic needs an icon or an illustration that code
cannot build, generate the image mid-edit and hand it to the graphics engine to composite in.
That changes what a graphic can be.

Colours and fonts come from `brand.md` and the style file, exactly as they do for graphics.

## Files this skill owns

| Path | What |
|------|------|
| `projects/<job>/broll/generated/` | The rendered clips. |
| `projects/<job>/broll/manifest.json` | One entry per clip: slot ID, beat window, template, prompt, output path, fps, duration. |

The manifest is the handoff. `graphics` places the clips; this skill never touches the composite.
