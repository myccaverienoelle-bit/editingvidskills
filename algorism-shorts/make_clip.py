"""Per-clip renderer for the Algorism founder short-form series.

Stdlib-only driver (this container has no PIL/numpy) that builds ONE
finished social clip from the 4K source per invocation, following the
video-use skill's hard rules:

  per-segment extract (crop straight from 4K -> 1080x1920 or 1080x1080,
  grade, 30ms audio edge fades) -> lossless concat -> lower-third overlay
  (first 3s, alpha fades) -> per-clip SRT burned LAST -> 1.5s end-frame
  card appended with identical encode params -> two-pass -14 LUFS loudnorm.

Captions: natural sentence case, <=4-word chunks broken on punctuation and
speech gaps, Jost, white, subtle shadow, MarginV inside the platform safe
zone. The one key line per clip renders larger in Cormorant Garamond,
copper #B85C38, via inline ASS override tags (libass honors them in SRT).

Usage:
    python3 make_clip.py clipspec.json
"""

from __future__ import annotations

import json
import re
import subprocess
import sys
import tempfile
from pathlib import Path

COPPER_ASS = "&H385CB8&"  # #B85C38 in ASS BGR order

SUB_STYLE_916 = (
    "FontName=Jost,FontSize=15,Bold=0,"
    "PrimaryColour=&H00FFFFFF,OutlineColour=&H00000000,BackColour=&H80000000,"
    "BorderStyle=1,Outline=1,Shadow=1,"
    "Alignment=2,MarginV=90,MarginL=24,MarginR=24"
)
# 1:1 LinkedIn feed: lighter bottom UI, keep >=25% clearance anyway
SUB_STYLE_11 = (
    "FontName=Jost,FontSize=15,Bold=0,"
    "PrimaryColour=&H00FFFFFF,OutlineColour=&H00000000,BackColour=&H80000000,"
    "BorderStyle=1,Outline=1,Shadow=1,"
    "Alignment=2,MarginV=78,MarginL=24,MarginR=24"
)

GAP_BREAK = 0.6       # start a new caption chunk across silences >= this
MAX_WORDS = 4
PUNCT_HARD = ".!?"
PUNCT_SOFT = ",;:"


def run(cmd: list[str]) -> None:
    p = subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)
    if p.returncode != 0:
        sys.exit(f"FAILED: {' '.join(str(c) for c in cmd[:12])}...\n"
                 + p.stderr.decode(errors="replace")[-2000:])


def probe_fps(video: str) -> str:
    out = subprocess.run(
        ["ffprobe", "-v", "error", "-select_streams", "v:0",
         "-show_entries", "stream=r_frame_rate", "-of",
         "default=noprint_wrappers=1:nokey=1", video],
        capture_output=True, text=True, check=True).stdout.strip()
    return out  # e.g. "25/1" or "24000/1001"


def srt_ts(t: float) -> str:
    ms = int(round(t * 1000))
    h, r = divmod(ms, 3600_000)
    m, r = divmod(r, 60_000)
    s, ms = divmod(r, 1000)
    return f"{h:02d}:{m:02d}:{s:02d},{ms:03d}"


def norm(s: str) -> str:
    return re.sub(r"[^a-z0-9 ]", "", s.lower()).strip()


def words_in(transcript: dict, a: float, b: float) -> list[dict]:
    out = []
    for w in transcript.get("words", []):
        if w.get("type") != "word":
            continue
        ws, we = w.get("start"), w.get("end")
        if ws is None or we is None or we <= a or ws >= b:
            continue
        out.append(w)
    return out


def chunk_words(words: list[dict]) -> list[list[dict]]:
    chunks, cur = [], []
    for i, w in enumerate(words):
        cur.append(w)
        text = (w.get("text") or "").strip()
        nxt = words[i + 1] if i + 1 < len(words) else None
        gap = (nxt["start"] - w["end"]) if nxt else 0.0
        if (text and text[-1] in PUNCT_HARD) or gap >= GAP_BREAK \
                or len(cur) >= MAX_WORDS \
                or (len(cur) >= 3 and text and text[-1] in PUNCT_SOFT):
            chunks.append(cur)
            cur = []
    if cur:
        # avoid a 1-word orphan: merge into previous when possible
        if chunks and len(cur) == 1 and len(chunks[-1]) < MAX_WORDS:
            chunks[-1].extend(cur)
        else:
            chunks.append(cur)
    return chunks


def build_srt(spec: dict, transcript: dict, out_path: Path) -> None:
    """Output-timeline SRT (Hard Rule 5) with copper key-line overrides."""
    key_norm = norm(spec.get("keyline", {}).get("text", "")) if spec.get("keyline") else ""
    entries = []
    offset = 0.0
    for r in spec["ranges"]:
        a, b = float(r["start"]), float(r["end"])
        ws = words_in(transcript, a, b)
        for ch in chunk_words(ws):
            t0 = max(0.0, max(a, ch[0]["start"]) - a) + offset
            t1 = max(0.0, min(b, ch[-1]["end"]) - a) + offset
            if t1 <= t0:
                t1 = t0 + 0.35
            text = " ".join((w.get("text") or "").strip() for w in ch)
            text = re.sub(r"\s+", " ", text).strip()
            is_key = bool(key_norm) and norm(text) in key_norm
            if is_key:
                text = r"{\fnCormorant Garamond\fs20\1c" + COPPER_ASS + "}" + text
            entries.append((t0, t1, text))
        offset += b - a
    entries.sort(key=lambda e: e[0])
    lines = []
    for i, (a, b, t) in enumerate(entries, 1):
        lines += [str(i), f"{srt_ts(a)} --> {srt_ts(b)}", t, ""]
    out_path.write_text("\n".join(lines), encoding="utf-8")


def vf_for(spec: dict, rng: dict) -> str:
    """Crop straight from the 4K frame, then scale. Optional punch-in zoom."""
    aspect = spec.get("aspect", "916")
    cx = rng.get("cx", spec.get("cx"))  # left edge of crop window in source px
    z = float(rng.get("zoom", 1.0))
    if aspect == "916":
        cw, ch_, ow, oh = "ih*9/16", "ih", 1080, 1920
    else:
        cw, ch_, ow, oh = "ih", "ih", 1080, 1080
    if z > 1.0:
        cw, ch_ = f"({cw})/{z:.4f}", f"({ch_})/{z:.4f}"
    x = f"{cx}" if cx is not None else f"(iw-({cw}))/2"
    if z > 1.0 and cx is not None:
        # keep the zoom window centered on the same subject center
        x = f"({cx}+(ih*9/16)/2-({cw})/2)" if aspect == "916" else f"({cx}+ih/2-({cw})/2)"
    y = f"(ih-({ch_}))/2" if z > 1.0 else "0"
    parts = [f"crop=w={cw}:h={ch_}:x={x}:y={y}", f"scale={ow}:{oh}"]
    if spec.get("grade"):
        parts.append(spec["grade"])
    return ",".join(parts)


def main() -> None:
    spec = json.loads(Path(sys.argv[1]).read_text())
    src = spec["source"]
    out = Path(spec["out"])
    out.parent.mkdir(parents=True, exist_ok=True)
    transcript = json.loads(Path(spec["transcript"]).read_text())
    aspect = spec.get("aspect", "916")
    fps = probe_fps(src)
    work = Path(tempfile.mkdtemp(prefix=f"clip_{spec['id']}_"))

    enc_v = ["-c:v", "libx264", "-preset", "fast", "-crf", "18",
             "-pix_fmt", "yuv420p", "-r", fps]
    enc_a = ["-c:a", "aac", "-b:a", "192k", "-ar", "48000", "-ac", "2"]

    # 1) per-segment extract with crop+grade+edge fades
    segs = []
    for i, r in enumerate(spec["ranges"]):
        a, b = float(r["start"]), float(r["end"])
        dur = b - a
        fo = max(0.0, dur - 0.03)
        seg = work / f"seg_{i:02d}.mp4"
        run(["ffmpeg", "-y", "-ss", f"{a:.3f}", "-i", src, "-t", f"{dur:.3f}",
             "-vf", vf_for(spec, r),
             "-af", f"afade=t=in:st=0:d=0.03,afade=t=out:st={fo:.3f}:d=0.03",
             *enc_v, *enc_a, "-movflags", "+faststart", str(seg)])
        segs.append(seg)

    base = work / "base.mp4"
    if len(segs) == 1:
        base = segs[0]
    else:
        lst = work / "concat.txt"
        lst.write_text("".join(f"file '{s}'\n" for s in segs))
        run(["ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", str(lst),
             "-c", "copy", "-movflags", "+faststart", str(base)])

    # 2) SRT (captions always on, per spec)
    srt = work / "clip.srt"
    build_srt(spec, transcript, srt)

    # 3) composite: lower-third overlay (first 3s) then subtitles LAST
    style = SUB_STYLE_916 if aspect == "916" else SUB_STYLE_11
    srt_esc = str(srt).replace(":", r"\:").replace("'", r"\'")
    speech = work / "speech.mp4"
    fc_parts = []
    inputs = ["-i", str(base)]
    cur = "[0:v]"
    if spec.get("lower_third"):
        inputs += ["-loop", "1", "-t", "3.2", "-i", spec["lower_third"]]
        fc_parts.append(
            "[1:v]format=rgba,fade=t=in:st=0.25:d=0.35:alpha=1,"
            "fade=t=out:st=2.7:d=0.45:alpha=1,setpts=PTS-STARTPTS[lt]")
        fc_parts.append(f"{cur}[lt]overlay=enable='lte(t,3.2)'[vlt]")
        cur = "[vlt]"
    fc_parts.append(f"{cur}subtitles='{srt_esc}':force_style='{style}'[outv]")
    run(["ffmpeg", "-y", *inputs,
         "-filter_complex", ";".join(fc_parts),
         "-map", "[outv]", "-map", "0:a",
         *enc_v, *enc_a, "-movflags", "+faststart", str(speech)])

    # 4) end-frame card, identical encode params, silent audio
    ef_png = spec["endframe"]
    ef = work / "endframe.mp4"
    run(["ffmpeg", "-y", "-loop", "1", "-t", "1.5", "-i", ef_png,
         "-f", "lavfi", "-t", "1.5", "-i", "anullsrc=r=48000:cl=stereo",
         "-shortest", *enc_v, *enc_a, "-movflags", "+faststart", str(ef)])
    lst2 = work / "concat2.txt"
    lst2.write_text(f"file '{speech}'\nfile '{ef}'\n")
    prenorm = work / "prenorm.mp4"
    run(["ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", str(lst2),
         "-c", "copy", "-movflags", "+faststart", str(prenorm)])

    # 5) two-pass loudnorm -> final
    meas = subprocess.run(
        ["ffmpeg", "-y", "-hide_banner", "-nostats", "-i", str(prenorm),
         "-af", "loudnorm=I=-14:TP=-1:LRA=11:print_format=json",
         "-vn", "-f", "null", "-"],
        capture_output=True, text=True).stderr
    j0, j1 = meas.rfind("{"), meas.rfind("}")
    ln = "loudnorm=I=-14:TP=-1:LRA=11"
    if j0 != -1 and j1 > j0:
        try:
            m = json.loads(meas[j0:j1 + 1])
            ln += (f":measured_I={m['input_i']}:measured_TP={m['input_tp']}"
                   f":measured_LRA={m['input_lra']}:measured_thresh={m['input_thresh']}"
                   f":offset={m['target_offset']}:linear=true")
        except Exception:
            pass
    run(["ffmpeg", "-y", "-i", str(prenorm), "-c:v", "copy",
         "-af", ln, *enc_a, "-movflags", "+faststart", str(out)])

    d = subprocess.run(["ffprobe", "-v", "error", "-show_entries",
                        "format=duration", "-of",
                        "default=noprint_wrappers=1:nokey=1", str(out)],
                       capture_output=True, text=True).stdout.strip()
    print(f"{spec['id']}: {out.name}  {float(d):.2f}s")


if __name__ == "__main__":
    main()
