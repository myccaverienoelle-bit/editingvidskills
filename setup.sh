#!/usr/bin/env bash
# Installs the stack described in CLAUDE.md. Safe to re-run: it only installs what is missing.
#   ./setup.sh          install anything missing, then verify
#   ./setup.sh --check  verify only, install nothing
set -uo pipefail

# Pinned on purpose. Everything in the skills is tuned against one version's quirks, and a
# silent upgrade breaks renders you already signed off on. Bump it deliberately or not at all.
HF_VERSION="0.8.7"

CHECK_ONLY=0
[ "${1:-}" = "--check" ] && CHECK_ONLY=1

bold() { printf '\033[1m%s\033[0m\n' "$1"; }
ok()   { printf '  \033[32mok\033[0m    %s\n' "$1"; }
miss() { printf '  \033[31mmiss\033[0m  %s\n' "$1"; }
warn() { printf '  \033[33mwarn\033[0m  %s\n' "$1"; }
have() { command -v "$1" >/dev/null 2>&1; }

OS="$(uname -s)"
case "$OS" in
  Darwin) PLATFORM=mac ;;
  Linux)  PLATFORM=linux ;;
  *) echo "Unsupported platform: $OS. On Windows, run this inside WSL2 — not PowerShell."; exit 1 ;;
esac

if [ "$PLATFORM" = linux ] && grep -qi microsoft /proc/version 2>/dev/null; then
  case "$PWD" in
    /mnt/*) echo "You are on the Windows filesystem ($PWD)."
            echo "Move the workspace under ~ or the shell scripts lose their line endings and exec bits."
            exit 1 ;;
  esac
fi

bold "Stack check — $PLATFORM"
NEED=()
for tool in ffmpeg ffprobe node uv git-lfs whisperx; do
  if have "$tool"; then ok "$tool"; else miss "$tool"; NEED+=("$tool"); fi
done
if have node; then
  NODE_MAJOR="$(node --version | sed 's/^v//;s/\..*//')"
  [ "$NODE_MAJOR" -ge 22 ] || warn "node is $(node --version) — the render engine needs 22 or higher"
fi
if python3 -c "import PIL" 2>/dev/null; then ok "python3 + PIL"; else miss "python3 + PIL"; NEED+=(pil); fi

if [ ${#NEED[@]} -eq 0 ]; then
  bold "Everything is installed."
else
  if [ "$CHECK_ONLY" = 1 ]; then
    bold "Missing: ${NEED[*]} — re-run without --check to install."
    exit 1
  fi

  bold "Installing: ${NEED[*]}"
  if [ "$PLATFORM" = mac ]; then
    if ! have brew; then
      echo "Homebrew is required and installs itself interactively. Run this first, then re-run ./setup.sh:"
      echo '  /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"'
      exit 1
    fi
    BREW=()
    for t in "${NEED[@]}"; do
      case "$t" in
        ffmpeg|ffprobe) BREW+=(ffmpeg) ;;
        node)           BREW+=(node) ;;
        uv)             BREW+=(uv) ;;
        git-lfs)        BREW+=(git-lfs) ;;
        pil)            BREW+=(pillow) ;;
      esac
    done
    # de-duplicate: ffmpeg supplies ffprobe
    if [ ${#BREW[@]} -gt 0 ]; then
      UNIQ=$(printf '%s\n' "${BREW[@]}" | sort -u | tr '\n' ' ')
      echo "  brew install $UNIQ"
      # shellcheck disable=SC2086
      brew install $UNIQ || { echo "brew install failed — fix the error above and re-run."; exit 1; }
    fi
  else
    SUDO=""
    [ "$(id -u)" -ne 0 ] && SUDO=sudo
    APT=()
    for t in "${NEED[@]}"; do
      case "$t" in
        ffmpeg|ffprobe) APT+=(ffmpeg) ;;
        git-lfs)        APT+=(git-lfs) ;;
        pil)            APT+=(python3-pil) ;;
      esac
    done
    if [ ${#APT[@]} -gt 0 ]; then
      UNIQ=$(printf '%s\n' "${APT[@]}" | sort -u | tr '\n' ' ')
      echo "  $SUDO apt install $UNIQ   (this is the step that needs your password)"
      $SUDO apt update -qq
      # shellcheck disable=SC2086
      $SUDO apt install -y $UNIQ || { echo "apt install failed — fix the error above and re-run."; exit 1; }
    fi
    if ! have uv; then
      echo "  installing uv"
      curl -LsSf https://astral.sh/uv/install.sh | sh
      export PATH="$HOME/.local/bin:$PATH"
    fi
    if ! have node || [ "${NODE_MAJOR:-0}" -lt 22 ]; then
      echo "  installing node 22"
      curl -fsSL https://deb.nodesource.com/setup_22.x | $SUDO -E bash -
      $SUDO apt install -y nodejs
    fi
  fi

  # WhisperX goes in its own isolated environment. Never into system Python.
  if ! have whisperx; then
    have uv || { echo "uv is required for WhisperX and is not on PATH. Open a new shell and re-run."; exit 1; }
    bold "Installing WhisperX (isolated env, 3-5 GB, several minutes, once)"
    uv tool install whisperx || { echo "WhisperX install failed — see the error above."; exit 1; }
    export PATH="$HOME/.local/bin:$PATH"
  fi
fi

# The render engine drives a headless Chrome. `doctor` reports this as a plain failure, so it is
# easy to read as noise and skip — and then every graphics render fails. It is not optional.
if [ "$CHECK_ONLY" = 0 ] && have npx; then
  bold "HyperFrames $HF_VERSION + its render browser"
  npx --yes "hyperframes@$HF_VERSION" browser ensure || warn "browser ensure failed — graphics cannot render until it succeeds"
fi

bold "Versions"
have ffmpeg   && printf '  ffmpeg    %s\n' "$(ffmpeg -version | head -1 | cut -d' ' -f3)"
have node     && printf '  node      %s\n' "$(node --version)"
have uv       && printf '  uv        %s\n' "$(uv --version | cut -d' ' -f2)"
have whisperx && printf '  whisperx  %s\n' "$(whisperx --version 2>/dev/null || echo installed)"
have git-lfs  && printf '  git-lfs   %s\n' "$(git-lfs --version | cut -d' ' -f1)"
python3 -c "import PIL, sys; print('  PIL      ', PIL.__version__)" 2>/dev/null || warn "PIL still missing"

cat <<'NEXT'

Two steps left, both inside Claude Code rather than this shell:

  1. The watch skill — the one that lets the editor see its own renders:
       /plugin marketplace add bradautomates/claude-video
       /plugin install watch@claude-video

  2. Higgsfield, for AI B-roll. The server is already configured in .mcp.json, so Claude Code
     offers it the first time you open this folder — approve it, then run /mcp and sign in.
     If it does not appear:
       claude mcp add --transport http higgsfield "https://mcp.higgsfield.ai/mcp"

HyperFrames is pinned to the version at the top of this script, and its headless Chrome is
already installed. To see the full picture:

  npx hyperframes@0.8.7 doctor

On a healthy machine set up this way, these failures are expected and fine to ignore:

  - Docker / Docker running .... not needed
  - whisper-cpp ................ optional; WhisperX does transcription here
  - TTS (Kokoro) ............... optional; only for local synthesised voice
  - BGM (MusicGen) ............. optional; music is licensed and user-supplied
  - a nag to upgrade past the pin

Anything else failing is real. In particular, "Chrome ... required for local rendering" must be
green — that is the headless browser every graphic renders in.
NEXT
