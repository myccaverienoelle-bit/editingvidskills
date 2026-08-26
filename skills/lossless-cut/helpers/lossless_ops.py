#!/usr/bin/env python3
"""LosslessCut-style lossless media operations via ffmpeg stream copy.

Mirrors the semantics of the LosslessCut desktop app (mifi/lossless-cut):
cuts use input seeking (-ss before -i) so the effective start snaps to the
keyframe at or before the requested time, with -avoid_negative_ts make_zero,
and everything runs with -c copy — no re-encode, no quality loss, near-instant.

Subcommands:
    keyframes <file> [--start S] [--end E]
    snap <file> <time> [--direction prev|next|nearest]
    cut <file> --start S [--end E] [-o OUT] [--accurate]
    export <file> [--project P.llc] [--outdir DIR] [--include-unselected]
    merge -o OUT <in1> <in2> ... [--faststart]
    remux <file> -o OUT
    extract-tracks <file> [--outdir DIR]
    rotate <file> --degrees {0,90,180,270} [-o OUT]

Every command prints the underlying ffmpeg command before running it
(LosslessCut's "last ffmpeg command" habit) so it can be tweaked and
re-run by hand.
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
import tempfile
from pathlib import Path


def run(cmd: list[str]) -> None:
    print("$ " + " ".join(str(c) for c in cmd), flush=True)
    subprocess.run([str(c) for c in cmd], check=True)


def ffprobe_json(path: Path, *extra: str) -> dict:
    cmd = ["ffprobe", "-v", "error", "-of", "json", *extra, str(path)]
    out = subprocess.check_output(cmd)
    return json.loads(out)


def media_duration(path: Path) -> float:
    info = ffprobe_json(path, "-show_entries", "format=duration")
    return float(info["format"]["duration"])


def keyframe_times(path: Path, start: float | None = None, end: float | None = None) -> list[float]:
    """Keyframe timestamps of the first video stream, optionally bounded."""
    cmd = ["ffprobe", "-v", "error", "-select_streams", "v:0", "-skip_frame", "nokey"]
    if start is not None or end is not None:
        lo = max(0.0, start if start is not None else 0.0)
        interval = f"{lo:.6f}%{end:.6f}" if end is not None else f"{lo:.6f}"
        cmd += ["-read_intervals", interval]
    cmd += ["-show_entries", "frame=pts_time", "-of", "csv=p=0", str(path)]
    out = subprocess.check_output(cmd).decode()
    times = sorted({float(t) for line in out.splitlines() if (t := line.strip().rstrip(",")) })
    if start is not None:
        times = [t for t in times if t >= start - 1e-6]
    if end is not None:
        times = [t for t in times if t <= end + 1e-6]
    return times


def snap_time(path: Path, t: float, direction: str = "prev") -> float:
    """Snap t to a keyframe: prev (at/before, what a copy cut lands on), next, or nearest."""
    window = 10.0
    while window <= 640.0:
        times = keyframe_times(path, max(0.0, t - window), t + window)
        prevs = [k for k in times if k <= t + 1e-6]
        nexts = [k for k in times if k >= t - 1e-6]
        if direction == "prev" and prevs:
            return prevs[-1]
        if direction == "next" and nexts:
            return nexts[0]
        if direction == "nearest" and times:
            return min(times, key=lambda k: abs(k - t))
        window *= 4
    return 0.0 if direction != "next" else media_duration(path)


def default_out_dir(src: Path) -> Path:
    d = src.parent / "edit"
    d.mkdir(parents=True, exist_ok=True)
    return d


def check_not_input(out: Path, inputs: list[Path]) -> None:
    for i in inputs:
        if out.resolve() == i.resolve():
            sys.exit(f"refusing to overwrite input file: {i}")


def fmt_t(t: float) -> str:
    return f"{t:.6f}".rstrip("0").rstrip(".")


def do_cut(src: Path, start: float, end: float | None, out: Path, accurate: bool = False) -> Path:
    check_not_input(out, [src])
    out.parent.mkdir(parents=True, exist_ok=True)
    cutting_start = start > 0
    dur = None if end is None else max(0.001, end - start)

    cmd: list[str] = ["ffmpeg", "-hide_banner", "-loglevel", "error", "-y"]
    if cutting_start and not accurate:
        cmd += ["-ss", fmt_t(start)]  # input seeking: snaps to keyframe at/before start
    cmd += ["-i", str(src)]
    if cutting_start and accurate:
        cmd += ["-ss", fmt_t(start)]  # output seeking: slower, still keyframe-bound for video
    if dur is not None:
        cmd += ["-t", fmt_t(dur)]
    cmd += ["-map", "0", "-c", "copy", "-ignore_unknown"]
    if cutting_start and not accurate:
        cmd += ["-avoid_negative_ts", "make_zero"]
    cmd += [str(out)]
    run(cmd)

    got = media_duration(out)
    kf = snap_time(src, start, "prev") if cutting_start and not accurate else start
    print(f"wrote {out}  duration={got:.3f}s  requested_start={fmt_t(start)}  keyframe_start≈{fmt_t(kf)}")
    return out


def sanitize(name: str) -> str:
    return re.sub(r"[^A-Za-z0-9._-]+", "_", name).strip("_")[:60]


def cmd_cut(a: argparse.Namespace) -> None:
    src = a.file.resolve()
    end = a.end
    out = a.out or default_out_dir(src) / f"{src.stem}-cut-{fmt_t(a.start)}-{fmt_t(end) if end is not None else 'end'}{src.suffix}"
    do_cut(src, a.start, end, Path(out), accurate=a.accurate)


def cmd_export(a: argparse.Namespace) -> None:
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    import llc_io

    src = a.file.resolve()
    project = Path(a.project) if a.project else Path(str(src) + "-proj.llc")
    if not project.exists():
        sys.exit(f"project file not found: {project} (pass --project explicitly)")
    proj = llc_io.load_llc(project)
    segs = proj["cutSegments"]
    if not a.include_unselected:
        segs = [s for s in segs if s.get("selected", True)]
    if not segs:
        sys.exit("no (selected) segments in project")
    outdir = Path(a.outdir) if a.outdir else default_out_dir(src)
    total_dur = media_duration(src)
    for i, seg in enumerate(segs, 1):
        start = float(seg.get("start", 0.0))
        end = seg.get("end")
        end = float(end) if end is not None else total_dur
        label = sanitize(seg.get("name") or "")
        out = outdir / f"{src.stem}-seg{i:02d}{'-' + label if label else ''}{src.suffix}"
        do_cut(src, start, end, out)
    print(f"exported {len(segs)} segment(s) to {outdir}")


def cmd_merge(a: argparse.Namespace) -> None:
    inputs = [p.resolve() for p in a.inputs]
    out = Path(a.out).resolve()
    check_not_input(out, inputs)
    out.parent.mkdir(parents=True, exist_ok=True)

    def signature(p: Path) -> list[tuple]:
        streams = ffprobe_json(p, "-show_streams").get("streams", [])
        return [
            (s.get("codec_type"), s.get("codec_name"), s.get("width"), s.get("height"),
             s.get("sample_rate"), s.get("channels"), s.get("pix_fmt"))
            for s in streams
        ]

    first = signature(inputs[0])
    for p in inputs[1:]:
        if signature(p) != first:
            print(f"WARNING: {p.name} has different codec parameters than {inputs[0].name}; "
                  "lossless concat of mismatched files often produces broken output", file=sys.stderr)

    with tempfile.NamedTemporaryFile("w", suffix=".txt", delete=False) as f:
        for p in inputs:
            escaped = str(p).replace("'", "'\\''")
            f.write(f"file '{escaped}'\n")
        list_path = f.name
    cmd = ["ffmpeg", "-hide_banner", "-loglevel", "error", "-y",
           "-f", "concat", "-safe", "0", "-i", list_path, "-map", "0", "-c", "copy", "-ignore_unknown"]
    if a.faststart:
        cmd += ["-movflags", "+faststart"]
    cmd += [str(out)]
    run(cmd)
    Path(list_path).unlink(missing_ok=True)
    print(f"wrote {out}  duration={media_duration(out):.3f}s  from {len(inputs)} file(s)")


def cmd_remux(a: argparse.Namespace) -> None:
    src = a.file.resolve()
    out = Path(a.out).resolve()
    check_not_input(out, [src])
    out.parent.mkdir(parents=True, exist_ok=True)
    run(["ffmpeg", "-hide_banner", "-loglevel", "error", "-y", "-i", str(src),
         "-map", "0", "-c", "copy", "-ignore_unknown", str(out)])
    print(f"wrote {out}  duration={media_duration(out):.3f}s")


def cmd_extract_tracks(a: argparse.Namespace) -> None:
    src = a.file.resolve()
    outdir = Path(a.outdir) if a.outdir else default_out_dir(src)
    outdir.mkdir(parents=True, exist_ok=True)
    streams = ffprobe_json(src, "-show_streams").get("streams", [])
    ext = {"video": ".mkv", "audio": ".mka", "subtitle": ".mks"}
    n = 0
    for s in streams:
        ctype, idx, codec = s.get("codec_type"), s["index"], s.get("codec_name", "unknown")
        if ctype not in ext:
            print(f"skipping stream {idx} ({ctype}/{codec}): not extractable to its own file")
            continue
        out = outdir / f"{src.stem}-track{idx}-{codec}{ext[ctype]}"
        run(["ffmpeg", "-hide_banner", "-loglevel", "error", "-y", "-i", str(src),
             "-map", f"0:{idx}", "-c", "copy", str(out)])
        print(f"wrote {out}")
        n += 1
    print(f"extracted {n} track(s) to {outdir}")


def cmd_rotate(a: argparse.Namespace) -> None:
    src = a.file.resolve()
    out = Path(a.out).resolve() if a.out else default_out_dir(src) / f"{src.stem}-rot{a.degrees}{src.suffix}"
    check_not_input(out, [src])
    out.parent.mkdir(parents=True, exist_ok=True)
    # display matrix side data, LosslessCut's convention: clockwise degrees -> 360 - deg
    display_rotation = (360 - a.degrees) % 360
    run(["ffmpeg", "-hide_banner", "-loglevel", "error", "-y",
         "-display_rotation:v:0", str(display_rotation), "-i", str(src),
         "-map", "0", "-c", "copy", str(out)])
    print(f"wrote {out}  (rotation metadata only; pixels untouched)")


def cmd_keyframes(a: argparse.Namespace) -> None:
    for t in keyframe_times(a.file.resolve(), a.start, a.end):
        print(fmt_t(t))


def cmd_snap(a: argparse.Namespace) -> None:
    print(fmt_t(snap_time(a.file.resolve(), a.time, a.direction)))


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="command", required=True)

    p = sub.add_parser("keyframes", help="list keyframe timestamps (seconds)")
    p.add_argument("file", type=Path)
    p.add_argument("--start", type=float, default=None)
    p.add_argument("--end", type=float, default=None)
    p.set_defaults(fn=cmd_keyframes)

    p = sub.add_parser("snap", help="snap a time to a keyframe")
    p.add_argument("file", type=Path)
    p.add_argument("time", type=float)
    p.add_argument("--direction", choices=["prev", "next", "nearest"], default="prev")
    p.set_defaults(fn=cmd_snap)

    p = sub.add_parser("cut", help="lossless cut of one range")
    p.add_argument("file", type=Path)
    p.add_argument("--start", "-s", type=float, required=True)
    p.add_argument("--end", "-e", type=float, default=None, help="omit to cut to end of file")
    p.add_argument("-o", "--out", type=Path, default=None)
    p.add_argument("--accurate", action="store_true",
                   help="seek after -i (LosslessCut's 'normal cut' mode); slower, mainly for audio")
    p.set_defaults(fn=cmd_cut)

    p = sub.add_parser("export", help="export all selected segments of a .llc project")
    p.add_argument("file", type=Path, help="media file")
    p.add_argument("--project", type=Path, default=None, help="default: <file>-proj.llc next to media")
    p.add_argument("--outdir", type=Path, default=None)
    p.add_argument("--include-unselected", action="store_true")
    p.set_defaults(fn=cmd_export)

    p = sub.add_parser("merge", help="lossless concat of files with identical codec parameters")
    p.add_argument("inputs", type=Path, nargs="+")
    p.add_argument("-o", "--out", type=Path, required=True)
    p.add_argument("--faststart", action="store_true", help="add -movflags +faststart (mp4/mov)")
    p.set_defaults(fn=cmd_merge)

    p = sub.add_parser("remux", help="rewrap into another container, streams untouched")
    p.add_argument("file", type=Path)
    p.add_argument("-o", "--out", type=Path, required=True)
    p.set_defaults(fn=cmd_remux)

    p = sub.add_parser("extract-tracks", help="each stream to its own file")
    p.add_argument("file", type=Path)
    p.add_argument("--outdir", type=Path, default=None)
    p.set_defaults(fn=cmd_extract_tracks)

    p = sub.add_parser("rotate", help="set rotation metadata without re-encoding")
    p.add_argument("file", type=Path)
    p.add_argument("--degrees", type=int, choices=[0, 90, 180, 270], required=True)
    p.add_argument("-o", "--out", type=Path, default=None)
    p.set_defaults(fn=cmd_rotate)

    a = ap.parse_args()
    a.fn(a)


if __name__ == "__main__":
    main()
