"""Generate DELIVERABLES.md (spec §9) from edl_master.json.

Usage: python3 gen_deliverables.py <edl_master.json> <out.md>
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

CADENCE = [
    ("Week 1 — Meet the man", [
        ("Mon", "SPINE-01", "also 1:1 on LinkedIn"),
        ("Tue", "SAT-01", ""),
        ("Wed", "SPINE-02", ""),
        ("Thu", "SAT-11", "1:1 SPINE-02 on LinkedIn"),
        ("Fri", "SPINE-03", ""),
        ("Sat", "SAT-13", ""),
        ("Sun", "SAT-15", ""),
    ]),
    ("Week 2 — The idea, honestly", [
        ("Mon", "SPINE-04", "also 1:1 on LinkedIn"),
        ("Tue", "SAT-08", ""),
        ("Wed", "SPINE-05", ""),
        ("Thu", "SAT-05", "1:1 SPINE-05 on LinkedIn"),
        ("Fri", "SPINE-06", ""),
        ("Sat", "SAT-06", ""),
        ("Sun", "SAT-12", ""),
    ]),
    ("Week 3 — The invitation", [
        ("Mon", "SPINE-07", ""),
        ("Tue", "SAT-02", "1:1 SAT-01 on LinkedIn"),
        ("Wed", "SAT-07", ""),
        ("Thu", "SAT-14", ""),
        ("Fri", "SPINE-08", "the one hard-CTA post"),
        ("Sat", "SAT-09", "1:1 SAT-09 on LinkedIn"),
        ("Sun", "SAT-03", ""),
    ]),
]
RESERVE = [("SAT-04", "urgency"), ("SAT-10", "nuclear comparison")]


def fmt_ts(t: float) -> str:
    m, s = divmod(t, 60)
    return f"{int(m):02d}:{s:05.2f}"


def main() -> None:
    data = json.loads(Path(sys.argv[1]).read_text())
    clips = {c["id"]: c for c in data["clips"]}
    out = []
    out.append("# Algorism Founder Series — Deliverables\n")
    out.append(f"Source: `C0128.MP4` (40:19.7, 4K native-vertical 25fps) · "
               f"{len(clips)} clips: 8-part numbered spine + "
               f"{len(clips)-8} satellites · every clip one continuous take, "
               f"zero internal cuts\n")

    out.append("\n## Clips\n")
    for c in data["clips"]:
        fmts = " + ".join(c["formats"])
        out.append(f"### {c['id']} — {c['title']}\n")
        out.append(f"| | |\n|---|---|")
        out.append(f"| In / Out | `{fmt_ts(c['in'])}` → `{fmt_ts(c['out'])}` (source) |")
        out.append(f"| Duration | {c['duration']:.1f}s speech + 1.5s end-frame = "
                   f"{c['speech_end_plus_endframe']:.1f}s |")
        out.append(f"| Formats | {fmts} |")
        out.append(f"| Hook (first line) | {c['hook']} |")
        key = c["keyline"] or "— (Part 8's single copper use is the algorism.org overlay)"
        out.append(f"| Key line (copper serif) | {key} |")
        out.append(f"| CTA level | {c['cta']} |")
        cap = c["caption"].replace("\n\n", " · ")
        out.append(f"| Caption | {cap} |")
        out.append(f"| Rationale | {c['rationale']} |\n")

    out.append("\n## Series map\n")
    out.append("**Spine (numbered, sequential, each stands alone):** "
               + " → ".join(f"`{cid}`" for cid in clips if cid.startswith("SPINE")) + "\n")
    out.append("\n**Satellite groupings** (unnumbered discovery bait, each funnels to the spine):\n")
    out.append("- *Honesty register:* SAT-05 (lifeboats), SAT-13 (Cold War), SAT-14 (terrible speller)")
    out.append("- *The record:* SAT-04 (no announcement), SAT-08 (Alexa), SAT-15 (control yourself), SAT-12 (the barbecue)")
    out.append("- *How to treat what's smarter than you:* SAT-01 (the cat), SAT-02 (who aligns), SAT-03 (dog-kicker), SAT-11 (don't kick it), SAT-10 (bombs wait)")
    out.append("- *The upside:* SAT-06 (worst case), SAT-07 (pillars), SAT-09 (not a doomer)\n")

    out.append("\n## 3-week posting cadence\n")
    out.append("9:16 daily on TikTok / Reels / Shorts; the 6-clip 1:1 variety set "
               "carries LinkedIn (anchor platform) twice a week.\n")
    for week, days in CADENCE:
        out.append(f"\n**{week}**\n")
        out.append("| Day | Post | Note |\n|---|---|---|")
        for d, cid, note in days:
            t = clips[cid]["title"].split("·")[-1].strip()
            out.append(f"| {d} | `{cid}` — {t} | {note} |")
    out.append("\n**Reserve** (slot in on high-momentum days or start week 4): "
               + ", ".join(f"`{cid}` ({why})" for cid, why in RESERVE) + "\n")

    out.append("\n## Standing rules applied\n")
    out.append("- Lower-third `John Jerome — Founder, Algorism`, first 3s only, honest credentials only (Law 3).")
    out.append("- No music anywhere; room tone as recorded (Law 1 / §7).")
    out.append("- No grade: footage shipped as shot, warm tungsten on wood (Law 4).")
    out.append("- Captions word-accurate natural case, Jost, white, center-safe zone; "
               "one copper Cormorant key line per clip (§7).")
    out.append("- Every clip ends on the same 1.5s ALGORISM cream/copper end-frame (§7).")
    out.append("- Admission clips (SPINE-01, 03, 05; SAT-05, 13, 14) run unbroken — no internal cuts (Law 1). "
               "In this edit *every* clip is a single continuous take.")
    out.append("- Loudness normalized to -14 LUFS / -1 dBTP per platform standard.")
    out.append("- One ASR mishear corrected in captions (SAT-06: 'algorithms' → 'Algorism', what he actually says).\n")

    Path(sys.argv[2]).write_text("\n".join(out), encoding="utf-8")
    print(f"wrote {sys.argv[2]} ({len(out)} lines)")


if __name__ == "__main__":
    main()
