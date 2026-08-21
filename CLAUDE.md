# The pipeline contract

This workspace is an AI video editor. It is not one big prompt: it is a human editor's job broken
into stages small enough that an agent can run each one. Claude cannot log into Premiere. The
pipeline is built around what Claude can actually do — read a transcript, make a decision, write
code, run a command line tool.

## The five stages

| # | Stage | What happens | Runs on |
|---|-------|--------------|---------|
| 0 | Setup | Workspace, `brand.md`, style files. Once, before the first video. | Claude |
| 1 | Rough cut | Transcribe every word with timings, decide what goes, cut and stitch. | WhisperX + FFmpeg |
| 2 | Graphics | Decide which lines earn a graphic, then build each one as code. | HyperFrames |
| 3 | B-roll | Generate motion graphics and AI footage for beats with no real footage. | HyperFrames + Higgsfield |
| 4 | Finishing | Captions, a music bed, a handful of sound effects. | FFmpeg |
| 5 | Export | Promote one final file, delete the scratch. | FFmpeg |

Format does not change which stages run. Short form and long form use the same five stages.
All that changes is how graphics and captions behave inside stages 2 and 4, and that is driven
entirely by the style file.

Each stage is a skill in `.claude/skills/`:

- `rough-cut` — stage 1
- `graphics` — stage 2
- `ai-broll` — stage 3
- `finishing` — stage 4
- `export` — stage 5

## The folder contract

```
.
├── CLAUDE.md              this file — the pipeline contract
├── brand.md               colours, fonts, voice. The one file you personalise
├── styles/
│   └── editorial/         one folder per look you edit in
│       ├── style.md       creative direction in prose
│       └── style.json     the same decisions as machine-readable knobs
├── assets/
│   ├── fonts/             real font files. Renders cannot rely on system fonts
│   ├── logos/             your marks, end screens
│   └── sfx/               your growing library of real sound samples
└── projects/
    └── <job-name>/        one folder per video, named after the content
        ├── raw/           source clips, copied in, never moved
        ├── broll/         screen recordings and supporting footage
        ├── audio/         licensed music, sound samples for this video
        ├── assets/        references, screenshots, logos for this video
        ├── transcript/    transcript.json and cutsheet.json, the durable record
        ├── graphics-build/  the composition source. This is the real progress
        └── outputs/       renders and the cut-aligned transcript
```

The top half is taste: permanent, shared across every video. The bottom half is jobs:
disposable. Keeping them apart is what lets the editor get better at your look over time instead
of relearning it every video.

**Every folder earns its place.** Do not add a notes file, a config file, or a `temp/` folder as you
go. Taste lives in `brand.md` and `styles/`; work lives in `projects/`. Anything that does not
clearly belong to one of those two halves means the design drifted.

**Job naming is a rule, not a nicety.** Name the folder after what the video is about, in kebab
case — `projects/claude-edits-my-videos/`. Never the camera filename, never a date, never a
stage suffix like `-final` or `-v2`. One folder carries the whole content piece across every
stage. Stage suffixes are how you end up with four folders and no idea which one shipped.

## The stack

| Tool | What it does | Link |
|------|--------------|------|
| Claude Code | The editor itself. Everything else is a tool it calls. | claude.com/product/claude-code |
| WhisperX | Local transcription with a timestamp on every single word. | github.com/m-bain/whisperX |
| FFmpeg | Every cut, every mix, every composite. The workhorse. | ffmpeg.org |
| HyperFrames | Free, open source graphics engine from the team at HeyGen. Graphics as code. | github.com/heygen-com/hyperframes |
| Higgsfield | One MCP connection to every good image and video model, for AI B-roll. | higgsfield.ai |
| `watch` skill | Gives Claude eyes. The one that makes it autonomous. Free. | github.com/bradautomates/claude-video |

A taste skill is the optional seventh. Every HyperFrames graphic is HTML and CSS, so anything
that makes Claude better at front end design makes the motion graphics better too
(`tasteskill.dev`). Install it globally and every graphic in every video improves at once.

### Install

`./setup.sh` does the binary half of this on macOS and on Ubuntu/Debian/WSL2 — it installs only
what is missing and is safe to re-run. `./setup.sh --check` verifies without installing anything.
It is the one file in this workspace that is neither taste nor a job; it earns its place by being
the thing a fresh machine runs before either of those exists. Everything below is what it does,
and what to do on a platform it does not cover.

On Windows, do this in WSL2 first — FFmpeg, the render engine and the transcription stack are
Unix tools and will not run in PowerShell. `wsl --install` in an Administrator PowerShell, reboot,
then do everything below inside the Ubuntu terminal, including installing Claude Code. Keep the
project in the Linux filesystem under `~`, not `/mnt/c/`, or the shell scripts lose their line
endings and executable bits. `uname -s` returning `Darwin` or `Linux` means you are fine.

macOS:

```bash
brew install ffmpeg node uv python git-lfs
```

Ubuntu, Debian, or WSL2:

```bash
sudo apt update && sudo apt install -y ffmpeg python3 python3-pip python3-pil git-lfs
curl -LsSf https://astral.sh/uv/install.sh | sh
curl -fsSL https://deb.nodesource.com/setup_22.x | sudo -E bash - && sudo apt install -y nodejs
```

Node must be 22 or higher — that is what the render engine runs on.

WhisperX, in its own isolated environment — roughly 3–5 GB, several minutes, once. **Do not
install it into your system Python:**

```bash
uv tool install whisperx
whisperx --help
```

The `large-v3` weights and the wav2vec2 alignment model download on first transcription, not on
install, so the first run is slow and every run after it is not. On an NVIDIA machine WhisperX
uses CUDA and needs a matching cuDNN — a `libcudnn` load error at first run is a
cuDNN-version mismatch, not a bad install. On Apple Silicon it runs on CPU (the backend has no
Metal path); add `--compute_type int8` and expect roughly real-time on a talking head.

The watch skill:

```bash
/plugin marketplace add bradautomates/claude-video
/plugin install watch@claude-video
```

HyperFrames, from inside this workspace:

```bash
npx hyperframes@0.8.7 doctor
npx hyperframes@0.8.7 browser ensure
```

**`browser ensure` is not optional.** The engine renders every graphic in a headless Chrome
(~114 MB, downloaded once). `doctor` reports its absence as one failure among several optional
ones, which makes it easy to read as noise and skip — and then every render fails.

Pin the version and leave it pinned. Everything here is tuned against one version's quirks, and a
silent upgrade will break renders you already signed off on. On a machine set up this way, these
doctor failures are expected and fine to ignore: Docker and Docker-running (not needed),
whisper-cpp (WhisperX does transcription here), Kokoro TTS and MusicGen (music is licensed and
user-supplied), and a nag to upgrade past the pin. Anything else is real.

Higgsfield goes in as an MCP server: copy the connection URL from higgsfield.ai/mcp and ask
Claude to install it. Add it under the connectors menu too if you want it in the desktop app.

### Verify before building anything

```bash
ffmpeg -version && node --version && uv --version && python3 -c "import PIL"
```

Then confirm the `watch` skill and the Higgsfield MCP both show up in the tool list. Half the
"it doesn't work" reports are a missing binary nobody checked for.

## Give it eyes

Claude Code cannot see video. It can only read the transcript. That is exactly why the rough cut
lands every time — cutting raw footage down is a pure transcript problem — and exactly why
graphics come back with small issues, because nothing ever looks at the result.

The `watch` skill pulls frames out one by one so Claude can look at any moment on screen.
Once the editor can see its own work it can work the way a real editor does: make a change,
watch it back, spot what is off, fix it, repeat. The loop needs exactly two ingredients — a goal
(finish the video) and a way to check the work (the watch skill).

Rules for the review loop, and they apply to every stage that renders anything:

- **Reviews run in sub-agents, never the main session.** Frame dumps flood the context
  window. Send the review out, get findings back as timestamped items.
- **Two distinct passes.** Technical QA first, as a checklist: stretched assets, vanished
  elements, wrong colours, brightness dips at seams — all binary, all catchable. Then
  composition as its own named step: "why is that at the top", "that's tiny", "does this make
  sense". A checklist-driven reviewer skips straight past composition while looking directly at
  the frames that show the problem. Running composition as its own pass is the single most
  useful thing in this pipeline.
- **The composition pass has concrete items**: every overlay re-checked against what the style
  file says for that element category, and every distinct visual moment named in the direction
  accounted for as built or explicitly flagged as skipped — never silently simplified away.
- **Run an early spot review after the first ~10% of the build**, not just at the end. A wrong
  placement habit caught once is a fix; caught at the end it is a rebuild.
- **Frame extraction, not a video understanding model.** Control is the point: Claude decides
  exactly where to look, so it can inspect the seam between two specific graphics instead of
  being handed a summary of the clip.

## Standing behaviour

- **The style file absorbs every correction.** Any note from a final review that should apply to
  every future video gets written back into `styles/<style>/style.md` and the `learned` array in
  `style.json` before the job is closed out. One-off notes are applied and forgotten. Show the
  diff before it becomes standing behaviour. Review sub-agents read the style fresh on every
  pass, so an absorbed correction tightens every future review with no extra wiring.
- **Local direction never silently overrides a style convention.** A conflict between a script
  comment and the style file is flagged, not decided quietly. Following the more recent
  instruction is recency bias, not judgment.
- **Pre-work beats prompting.** Scripts written in a document that supports comments, with
  comments left on them — what music and where, what graphic on this line, a link to the
  reference image — are the difference between an edit that comes back usable and one that
  needs an afternoon of directing.
- Never re-transcribe. Stage 1 writes the durable transcript; everything downstream reads it.
- Never re-render the base cut to change a graphic. Regenerate one composition, re-render one
  part, run one composite pass.
