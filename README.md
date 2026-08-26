# @remotion/skills

## Usage

This is an internal package and has no documentation.

## AI video editor workspace

This repo also carries the AI video editing pipeline from the AI Video Editing Playbook:
`CLAUDE.md` is the pipeline contract, `brand.md` is the one file you personalise, `styles/` holds
your looks, `assets/` holds real fonts, logos and sound samples, and `projects/` holds one
folder per video. The five stage skills live in `.claude/skills/` — `rough-cut`, `graphics`,
`ai-broll`, `finishing`, `export`.

On a fresh machine, run `./setup.sh` first — it installs the missing half of the stack (FFmpeg,
Node 22, uv, git-lfs, PIL, WhisperX) and prints the two steps that have to happen inside Claude
Code: the `watch` plugin and the Higgsfield MCP. `./setup.sh --check` verifies without
installing.
