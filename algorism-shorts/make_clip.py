"""Per-clip renderer for the Algorism founder short-form series.

Stdlib-only driver (this container has no PIL/numpy) that builds ONE
finished social clip from the 4K source per invocation, following the
video-use skill's hard rules:

  per-segment extract (crop straight from 4K -> 1080x1920 or 1080x1080,
  grade, 30ms audio edge fades) -> lossless concat -> lower-third overlay
  (first 3s, alpha fades) -> per-clip SRT burned LAST -> 1.5s end-frame
  card appended with identical encode params -> two-pass -16 LUFS loudnorm.

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
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

# Subtitles ship as a real .ass file: this ffmpeg build's SRT decoder strips
# inline {\...} override tags, so the copper key line must be a named style.
# PlayRes matches the output frame, so every value below is in real pixels.
# MarginV keeps captions ~31% up the 9:16 frame (platform bottom-UI safe zone)
# and ~27% up the 1:1 frame.
ASS_TEMPLATE = """[Script Info]
ScriptType: v4.00+
PlayResX: {w}
PlayResY: {h}
WrapStyle: 0
ScaledBorderAndShadow: yes

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Base,Jost,{base_fs},&H00FFFFFF,&H000000FF,&H00000000,&H80000000,0,0,0,0,100,100,0,0,1,4,2,2,80,80,{margin_v},1
Style: Key,Cormorant Garamond,{key_fs},&H00385CB8,&H000000FF,&H00000000,&H80000000,0,0,0,0,100,100,0,0,1,4,2,2,80,80,{margin_v},1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Text
"""

ASS_GEOM = {
    "916": {"w": 1080, "h": 1920, "base_fs": 100, "key_fs": 132, "margin_v": 600},
    "11": {"w": 1080, "h": 1080, "base_fs": 88, "key_fs": 116, "margin_v": 292},
}

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
    return out.splitlines()[0]  # e.g. "25/1" or "24000/1001"


def probe_display_dims(video: str) -> tuple[int, int]:
    """Effective display dimensions after container rotation is applied
    (ffmpeg auto-rotates, so filter chains see these dims)."""
    out = subprocess.run(
        ["ffprobe", "-v", "error", "-select_streams", "v:0",
         "-show_entries", "stream=width,height:stream_side_data=rotation",
         "-of", "json", video],
        capture_output=True, text=True, check=True).stdout
    st = json.loads(out)["streams"][0]
    w, h = int(st["width"]), int(st["height"])
    rot = 0
    for sd in st.get("side_data_list", []) or []:
        if "rotation" in sd:
            rot = int(sd["rotation"])
    if abs(rot) % 180 == 90:
        w, h = h, w
    return w, h


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


def ass_ts(t: float) -> str:
    cs = int(round(t * 100))
    h, r = divmod(cs, 360_000)
    m, r = divmod(r, 6_000)
    s, cs = divmod(r, 100)
    return f"{h}:{m:02d}:{s:02d}.{cs:02d}"


def find_key_span(words: list[dict], key_text: str) -> tuple[float, float] | None:
    """Locate the keyline's word sequence inside the clip words and return
    its (start, end) source-time span. Time-based matching — a text substring
    can false-positive on partial repeats elsewhere in the clip."""
    want = [t for t in norm(key_text).split() if t]
    if not want:
        return None
    flat: list[tuple[str, int]] = []
    for i, w in enumerate(words):
        for t in norm(w.get("text") or "").split():
            flat.append((t, i))
    n = len(want)
    for i in range(len(flat) - n + 1):
        if [f[0] for f in flat[i:i + n]] == want:
            return words[flat[i][1]]["start"], words[flat[i + n - 1][1]]["end"]
    return None


def build_ass(spec: dict, transcript: dict, out_path: Path) -> None:
    """Output-timeline ASS captions (Hard Rule 5) with the copper key line
    as a named style, selected by time span.

    word_overrides fixes rare ASR mishears so captions stay word-accurate
    to what was SAID (e.g. Scribe heard "algorithms" for "Algorism"):
    [{"approx": 836.5, "from": "algorithms", "to": "Algorism"}]
    """
    geom = ASS_GEOM[spec.get("aspect", "916")]
    overrides = spec.get("word_overrides") or []
    key_text = (spec.get("keyline") or {}).get("text", "")
    entries = []
    offset = 0.0
    for r in spec["ranges"]:
        a, b = float(r["start"]), float(r["end"])
        ws = words_in(transcript, a, b)
        # apply overrides by index; never mutate the cached transcript objects
        for i2, w in enumerate(ws):
            for ov in overrides:
                if abs(w["start"] - float(ov["approx"])) < 2.0 and \
                        norm(w.get("text") or "") == norm(ov["from"]):
                    nw = dict(w)
                    nw["text"] = ov["to"]
                    ws[i2] = nw
        span = find_key_span(ws, key_text) if key_text else None
        if key_text and span is None:
            print(f"  warning: keyline not found in range, no copper: {key_text!r}")
        for ch in chunk_words(ws):
            t0 = max(0.0, max(a, ch[0]["start"]) - a) + offset
            t1 = max(0.0, min(b, ch[-1]["end"]) - a) + offset
            if t1 <= t0:
                t1 = t0 + 0.35
            text = " ".join((w.get("text") or "").strip() for w in ch)
            text = re.sub(r"\s+", " ", text).strip()
            text = text.replace("{", "").replace("}", "").replace("\\", "")
            mid = (ch[0]["start"] + ch[-1]["end"]) / 2
            is_key = span is not None and span[0] - 0.05 <= mid <= span[1] + 0.05
            entries.append((t0, t1, "Key" if is_key else "Base", text))
        offset += b - a
    entries.sort(key=lambda e: e[0])
    lines = [ASS_TEMPLATE.format(**geom)]
    for (a, b, style, t) in entries:
        lines.append(f"Dialogue: 0,{ass_ts(a)},{ass_ts(b)},{style},,0,0,0,{t}")
    out_path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def vf_pre(spec: dict) -> str:
    """Chain BEFORE stabilization: normalize the native-portrait source to
    the full 1080x1920 frame. Stabilization must always run on this full
    frame — the background dominates it, so vid.stab tracks the room, not
    the speaker. (Detecting on a tighter crop mistracks his body: the 1:1
    squares came out over-zoomed and off-center that way.)"""
    return "scale=1080:1920"


def vf_post(spec: dict, rng: dict) -> str:
    """Chain AFTER stabilization: aspect crop / punch-in, in output pixels.

    face_y: face center as a fraction of frame height (locked-off framing,
    one value serves the whole talk). The 1:1 crop puts the face at 40% of
    the square. Zoom crops upscale from 1080p — unused in this edit.
    """
    aspect = spec.get("aspect", "916")
    z = float(rng.get("zoom", spec.get("zoom", 1.0)))
    fy = float(rng.get("face_y", spec.get("face_y", 0.44)))
    parts = []
    if aspect == "11":
        y = min(1920 - 1080, max(0, int((fy * 1920 - 0.40 * 1080) / 2) * 2))
        parts.append(f"crop=1080:1080:0:{y}")
    if z > 1.0:
        ow, oh = (1080, 1080) if aspect == "11" else (1080, 1920)
        w = max(2, int(ow / z / 2) * 2)
        h = max(2, int(oh / z / 2) * 2)
        x = int((ow - w) / 4) * 2
        yz = min(oh - h, max(0, int(fy * oh * (1 - 1 / z) / 2) * 2))
        parts.append(f"crop={w}:{h}:{x}:{yz}")
        parts.append(f"scale={ow}:{oh}")
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

    # 1) per-segment extract with stabilization+crop+grade+edge fades.
    # The source has slow camera drift; vid.stab virtual-tripod (first frame
    # of the segment as reference) locks the background rigid. Both passes
    # run at OUTPUT resolution (after crop+scale, identical geometry) —
    # detection at 4K is ~8x slower for no visible gain, and the tripod
    # zoom crop at 1080p is imperceptible for this content.
    segs = []
    for i, r in enumerate(spec["ranges"]):
        a, b = float(r["start"]), float(r["end"])
        dur = b - a
        fo = max(0.0, dur - 0.03)
        seg = work / f"seg_{i:02d}.mp4"
        trf = work / f"seg_{i:02d}.trf"
        pre, post = vf_pre(spec), vf_post(spec, r)
        vf = pre
        if spec.get("stabilize", True):
            # Smoothed RELATIVE stabilization, not virtual tripod: tripod
            # aligns each frame independently to a reference, so estimation
            # noise (worsened by the aperture problem on the vertical slats
            # and by his gestures) becomes visible micro-jitter — measured
            # 2x the raw footage's frame-to-frame background motion. A 3s
            # smoothing window removes the slow drift and, because
            # corrections are averaged, cannot introduce per-frame shake.
            run(["ffmpeg", "-y", "-ss", f"{a:.3f}", "-i", src, "-t", f"{dur:.3f}",
                 "-map", "0:v:0",
                 "-vf", f"{pre},vidstabdetect=shakiness=8:accuracy=15:"
                        f"result={trf}",
                 "-f", "null", "-"])
            vf = (f"{pre},vidstabtransform=input={trf}:smoothing=75:"
                  f"crop=black:optzoom=1:interpol=bicubic")
        if post:
            vf += "," + post
        if spec.get("grade"):
            vf += "," + spec["grade"]
        run(["ffmpeg", "-y", "-ss", f"{a:.3f}", "-i", src, "-t", f"{dur:.3f}",
             "-map", "0:v:0", "-map", "0:a:0",
             "-vf", vf,
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

    # 2) captions (always on, per spec) as .ass — see ASS_TEMPLATE note
    subs = work / "clip.ass"
    build_ass(spec, transcript, subs)

    # 3) composite: lower-third overlay (first 3s) then subtitles LAST
    subs_esc = str(subs).replace(":", r"\:").replace("'", r"\'")
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
    cta = spec.get("cta_overlay")
    if cta:
        # hard-CTA clip only (spine part 8): small copper wordmark-url in the
        # top-safe area; this is the clip's single copper use.
        st = float(cta["start"])
        jost = cta.get("font", "/usr/share/fonts/truetype/brand/Jost-VF.ttf")
        txt = cta["text"].replace(":", r"\:").replace("'", r"\'")
        fc_parts.append(
            f"{cur}drawtext=fontfile={jost}:text='{txt}':fontsize=46:"
            f"fontcolor=0xB85C38:x=(w-text_w)/2:y=0.115*h:"
            f"shadowcolor=black@0.35:shadowx=0:shadowy=2:"
            f"alpha='if(lt(t\\,{st:.2f})\\,0\\,min(1\\,(t-{st:.2f})/0.5))'[vcta]")
        cur = "[vcta]"
    fc_parts.append(f"{cur}subtitles='{subs_esc}'[outv]")
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
         "-af", "loudnorm=I=-16:TP=-1.5:LRA=11:print_format=json",
         "-vn", "-f", "null", "-"],
        capture_output=True, text=True).stderr
    j0, j1 = meas.rfind("{"), meas.rfind("}")
    ln = "loudnorm=I=-16:TP=-1.5:LRA=11"
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
    # Clean up our own tempdir only. Batch runners must NOT glob-delete
    # /tmp/clip_<stem>_* — with parallel workers, the stem glob for
    # "X_sq" also matches a concurrently rendering "X" and destroys its
    # in-flight segments (this exact race shipped a 7s stub of a 19s clip).
    shutil.rmtree(work, ignore_errors=True)


if __name__ == "__main__":
    main()
