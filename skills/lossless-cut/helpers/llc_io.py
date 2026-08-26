#!/usr/bin/env python3
"""Read/write LosslessCut project (.llc) and EDL files; bridge to video-use edl.json.

LosslessCut (mifi/lossless-cut) saves projects as JSON5 named
`<mediafile>-proj.llc` next to the media, schema v2:

    { version: 2, mediaFileName: 'clip.mp4',
      cutSegments: [ { start: 1.2, end: 3.4, name: '', tags?: {k:v}, selected?: true } ] }

This module writes strict JSON (valid JSON5, opens fine in LosslessCut) and
reads real JSON5 via the `json5` pip package when plain JSON parsing fails.
Its CSV EDL format is `Start,End,Name` with times in seconds, header optional.

Subcommands:
    to-json <p.llc>                              normalized project as strict JSON on stdout
    from-json <segments.json> -o out.llc [--media FILE]
    to-csv <p.llc> -o out.csv
    from-csv <in.csv> -o out.llc [--media FILE]
    from-edl <edl.json> [--outdir DIR]           video-use EDL -> one .llc per source
    to-edl <p.llc> --media <path> -o edl.json [--duration S]
"""

from __future__ import annotations

import argparse
import csv
import json
import sys
from pathlib import Path


def load_llc(path: Path) -> dict:
    text = Path(path).read_text(encoding="utf-8-sig")
    try:
        data = json.loads(text)
    except json.JSONDecodeError:
        try:
            import json5
        except ImportError:
            sys.exit(f"{path} is JSON5 (written by the LosslessCut app); run `pip install json5` to read it")
        data = json5.loads(text)
    if not isinstance(data, dict) or not isinstance(data.get("cutSegments"), list):
        sys.exit(f"{path}: not a LosslessCut project (missing cutSegments)")
    for seg in data["cutSegments"]:
        seg.setdefault("start", 0.0)  # v1 projects allow a missing start
        seg.setdefault("name", "")
    return data


def save_llc(path: Path, media_name: str | None, segments: list[dict]) -> None:
    cut_segments = []
    for seg in segments:
        out = {"start": float(seg.get("start", 0.0))}
        if seg.get("end") is not None:
            out["end"] = float(seg["end"])
        out["name"] = str(seg.get("name") or "")
        if seg.get("tags"):
            out["tags"] = {str(k): str(v) for k, v in seg["tags"].items()}
        if "selected" in seg:
            out["selected"] = bool(seg["selected"])
        cut_segments.append(out)
    project: dict = {"version": 2}
    if media_name:
        project["mediaFileName"] = media_name
    project["cutSegments"] = cut_segments
    Path(path).write_text(json.dumps(project, indent=2) + "\n")
    print(f"wrote {path}  ({len(cut_segments)} segment(s))")


def read_csv_segments(path: Path) -> list[dict]:
    segments = []
    with open(path, newline="", encoding="utf-8-sig") as f:
        for i, row in enumerate(csv.reader(f)):
            if not row or not any(c.strip() for c in row):
                continue
            if i == 0 and row[0].strip().lower() == "start":
                continue
            start = float(row[0]) if row[0].strip() else 0.0
            end = float(row[1]) if len(row) > 1 and row[1].strip() else None
            name = row[2].strip() if len(row) > 2 else ""
            segments.append({"start": start, "end": end, "name": name})
    return segments


def cmd_to_json(a: argparse.Namespace) -> None:
    json.dump(load_llc(a.project), sys.stdout, indent=2)
    print()


def cmd_from_json(a: argparse.Namespace) -> None:
    data = json.loads(Path(a.segments).read_text())
    segments = data["cutSegments"] if isinstance(data, dict) else data
    media = a.media.name if a.media else (data.get("mediaFileName") if isinstance(data, dict) else None)
    save_llc(a.out, media, segments)


def cmd_to_csv(a: argparse.Namespace) -> None:
    proj = load_llc(a.project)
    with open(a.out, "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["Start", "End", "Name"])
        for seg in proj["cutSegments"]:
            w.writerow([seg["start"], "" if seg.get("end") is None else seg["end"], seg.get("name", "")])
    print(f"wrote {a.out}  ({len(proj['cutSegments'])} row(s))")


def cmd_from_csv(a: argparse.Namespace) -> None:
    save_llc(a.out, a.media.name if a.media else None, read_csv_segments(a.csv))


def cmd_from_edl(a: argparse.Namespace) -> None:
    edl = json.loads(Path(a.edl).read_text())
    sources: dict[str, str] = edl["sources"]
    by_source: dict[str, list[dict]] = {}
    for r in edl.get("ranges", []):
        name = " — ".join(x for x in [r.get("beat"), (r.get("quote") or "")[:48]] if x)
        by_source.setdefault(r["source"], []).append(
            {"start": r["start"], "end": r.get("end"), "name": name})
    for source_id, segments in by_source.items():
        media = Path(sources[source_id])
        outdir = Path(a.outdir) if a.outdir else media.parent
        outdir.mkdir(parents=True, exist_ok=True)
        save_llc(outdir / f"{media.name}-proj.llc", media.name, segments)


def cmd_to_edl(a: argparse.Namespace) -> None:
    proj = load_llc(a.project)
    media = a.media.resolve()
    source_id = media.stem
    ranges = []
    for seg in proj["cutSegments"]:
        if not seg.get("selected", True):
            continue
        end = seg.get("end")
        if end is None:
            if a.duration is None:
                sys.exit("a segment has no end time; pass --duration <media length in seconds>")
            end = a.duration
        r = {"source": source_id, "start": seg["start"], "end": end}
        if seg.get("name"):
            r["beat"] = seg["name"]
        ranges.append(r)
    edl = {
        "version": 1,
        "sources": {source_id: str(media)},
        "ranges": ranges,
        "total_duration_s": round(sum(r["end"] - r["start"] for r in ranges), 3),
    }
    Path(a.out).write_text(json.dumps(edl, indent=2) + "\n")
    print(f"wrote {a.out}  ({len(ranges)} range(s), {edl['total_duration_s']}s)")


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="command", required=True)

    p = sub.add_parser("to-json", help="print .llc as strict JSON")
    p.add_argument("project", type=Path)
    p.set_defaults(fn=cmd_to_json)

    p = sub.add_parser("from-json", help="segments JSON -> .llc")
    p.add_argument("segments", type=Path)
    p.add_argument("-o", "--out", type=Path, required=True)
    p.add_argument("--media", type=Path, default=None)
    p.set_defaults(fn=cmd_from_json)

    p = sub.add_parser("to-csv", help=".llc -> LosslessCut CSV EDL (seconds)")
    p.add_argument("project", type=Path)
    p.add_argument("-o", "--out", type=Path, required=True)
    p.set_defaults(fn=cmd_to_csv)

    p = sub.add_parser("from-csv", help="LosslessCut CSV EDL -> .llc")
    p.add_argument("csv", type=Path)
    p.add_argument("-o", "--out", type=Path, required=True)
    p.add_argument("--media", type=Path, default=None)
    p.set_defaults(fn=cmd_from_csv)

    p = sub.add_parser("from-edl", help="video-use edl.json -> one .llc per source")
    p.add_argument("edl", type=Path)
    p.add_argument("--outdir", type=Path, default=None, help="default: next to each source file")
    p.set_defaults(fn=cmd_from_edl)

    p = sub.add_parser("to-edl", help=".llc -> video-use edl.json skeleton")
    p.add_argument("project", type=Path)
    p.add_argument("--media", type=Path, required=True, help="absolute path of the media file")
    p.add_argument("-o", "--out", type=Path, required=True)
    p.add_argument("--duration", type=float, default=None, help="media length, for open-ended segments")
    p.set_defaults(fn=cmd_to_edl)

    a = ap.parse_args()
    a.fn(a)


if __name__ == "__main__":
    main()
