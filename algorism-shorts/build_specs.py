"""Build per-clip render specs + master EDL for the Algorism founder series.

Every cut edge is located by matching a verbatim anchor phrase (taken from
the packed Scribe transcript) against the word-level transcript near an
approximate timestamp, then padded 140ms in / 200ms out (clamped to the
neighboring words so a pad can never swallow speech). All 23 clips are
single continuous takes: no internal cuts anywhere in the series.

Usage: python3 build_specs.py <transcript.json> <out_dir>
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

PAD_IN, PAD_OUT, GUARD = 0.14, 0.20, 0.04
SEARCH_WINDOW = 12.0  # seconds around the approx timestamp


def norm(s: str) -> str:
    return re.sub(r"[^a-z0-9 ]", "", (s or "").lower()).strip()


def toks(s: str) -> list[str]:
    return [t for t in norm(s).split() if t]


# (id, title, (approx_t, start anchor), (approx_t, end anchor), keyline,
#  hook, cta, caption, rationale, extras)
CLIPS = [
    ("SPINE-01", "Meet Algorism — Part 1 · The cold open",
     (556.0, "Nobody has all the answers"), (576.0, "but we have to act"),
     "they're either delusional or lying to you",
     "Nobody has all the answers, including me.",
     "soft",
     "“If somebody tells you they have all the answers, they're either delusional or lying to you.” Meet John. Part 1 of Meet Algorism.\n\n#algorism #integrity #honesty #aitransition",
     "The single most arresting honest line in the talk; anti-guru positioning in his own words, uncut.",
     {}),
    ("SPINE-02", "Meet Algorism — Part 2 · What it is",
     (4.7, "What is Algorism?"), (36.2, "You're more likely to be rewarded"),
     "a rule book on how to improve your permanent record",
     "What is Algorism?",
     "soft",
     "Algorism in one breath: a rule book for your permanent record. Not a cult, not a religion, no belief required. Part 2 of Meet Algorism.\n\n#algorism #integrity #aitransition #permanentrecord",
     "The complete definition in one continuous take, plain words, includes the disclaimers.",
     {}),
    ("SPINE-03", "Meet Algorism — Part 3 · Why he built it",
     (2204.0, "a lot of the people who know way more"), (2247.4, "that's not good for anybody"),
     "I can't just sit back and do nothing",
     "A lot of the people who know way more about the technology than I do…",
     "soft",
     "He's not a technologist, and he says so. He built this because he couldn't sit back and do nothing. Part 3 of Meet Algorism.\n\n#algorism #founder #honesty #aitransition",
     "The honest origin: no invented credentials, just why he acted; admission runs unbroken.",
     {}),
    ("SPINE-04", "Meet Algorism — Part 4 · The thesis",
     (664.0, "you can have the greatest thought in the world"), (715.3, "gonna be looking at what you do"),
     "It's gonna be looking at what you do",
     "You can have the greatest thought in the world…",
     "soft",
     "Intentions are invisible. Behavior is the record. Part 4 of Meet Algorism.\n\n#algorism #integrity #behavior #aitransition",
     "The core thesis stated cleanly: thoughts don't count, patterns of behavior do; stumbles kept.",
     {}),
    ("SPINE-05", "Meet Algorism — Part 5 · The hard part",
     (2116.0, "I know I'm having a hard time myself"), (2143.6, "You're not alone"),
     "I'm having a hard time myself trying to improve",
     "I know I'm having a hard time myself trying to improve.",
     "soft",
     "The founder finds his own framework hard to live. He says so out loud. Part 5 of Meet Algorism.\n\n#algorism #honesty #integrity #practice",
     "The costliest admission in the footage — he struggles with his own practice; uncut per Law 1.",
     {}),
    ("SPINE-06", "Meet Algorism — Part 6 · What it is NOT",
     (82.6, "Algorism isn't a religion"), (120.6, "judge you on"),
     "it's all creating a permanent record",
     "Algorism isn't a religion, it's not a cult…",
     "soft",
     "What Algorism is not: a religion, a cult, or a reason to give anything up. Part 6 of Meet Algorism.\n\n#algorism #integrity #aitransition",
     "The cleanest full 'not this' take, pivoting into what it actually claims.",
     {}),
    ("SPINE-07", "Meet Algorism — Part 7 · What it's for",
     (1440.5, "It's all coming"), (1487.8, "We have to start preparing"),
     "Algorism is a starting place",
     "It's all coming, and it's all very confusing…",
     "soft",
     "No set answers. A starting place. Part 7 of Meet Algorism.\n\n#algorism #roadmap #aitransition #integrity",
     "States the mission honestly — a starting place for everyone, no overpromise.",
     {}),
    ("SPINE-08", "Meet Algorism — Part 8 · The invitation",
     (2161.3, "we all wanna be happy"), (2192.0, "we have to do it now"),
     None,
     "We all wanna be happy.",
     "hard",
     "This is the ask: work together, form a community, start now. The practice is at algorism.org. Part 8 of Meet Algorism.\n\n#algorism #community #integrity #aitransition",
     "The one hard-CTA clip; margarita line keeps it human, the ask is communal not salesy.",
     {"cta_anchor": (2176.2, "let's work together"), "cta_text": "algorism.org"}),
    ("SAT-01", "Satellite · The cat",
     (173.2, "Some people think that they can control AI"), (184.6, "you can control your cat"),
     "any more than you can control your cat",
     "Some people think that they can control AI.",
     "none",
     "“We're not gonna control it any more than you can control your cat.” More in the Meet Algorism series.\n\n#aitransition #control #algorism",
     "Micro-clip; the most quotable control line in the talk.",
     {}),
    ("SAT-02", "Satellite · Who aligns with whom",
     (402.0, "the more intelligent being"), (419.0, "humans can align with AI"),
     "We're gonna have to align with it",
     "The more intelligent being is the one that determines who's gonna be aligned with who.",
     "none",
     "“AI's not gonna align with us. We're gonna have to align with it.” That sentence is why Algorism exists. More in Meet Algorism.\n\n#alignment #aitransition #algorism",
     "The namesake idea of the framework in one breath.",
     {}),
    ("SAT-03", "Satellite · The dog-kicker",
     (1141.5, "Some people treat it meanly"), (1175.2, "You don't know. Nobody knows"),
     "kicks a dog when no one's looking",
     "Some people treat it meanly. “Hey, ChatGPT, you're such an idiot.”",
     "none",
     "“Like the guy who kicks a dog when no one's looking.” How you treat AI says something about you. He also says: maybe it won't care, nobody knows.\n\n#kindness #aitransition #algorism #behavior",
     "Vivid moral image plus his own uncertainty qualifier kept intact per Law 2.",
     {}),
    ("SAT-04", "Satellite · No announcement",
     (1769.8, "There's not gonna be an announcement"), (1813.9, "Don't worry about that"),
     "start changing your behavioral patterns now",
     "There's not gonna be an announcement.",
     "none",
     "There's no announcement coming. The record you're writing today is the one that counts. More in Meet Algorism.\n\n#permanentrecord #aitransition #algorism #behavior",
     "Urgency without hype, ends on grace: 'We all have things in the past. Move on.'",
     {}),
    ("SAT-05", "Satellite · The lifeboats",
     (1557.2, "If everybody starts screaming"), (1588.9, "survive the situation"),
     "I'm no different than anybody else",
     "If everybody starts screaming and heading for lifeboats at the same time, that's chaos.",
     "none",
     "He's not claiming to be calmer than you. That's the point of having a plan. More in Meet Algorism.\n\n#honesty #preparedness #algorism",
     "Admission clip — he'd panic too; the guideline is the answer, uncut per Law 1.",
     {}),
    ("SAT-06", "Satellite · Worst case",
     (832.0, "even if, if, let's say, if it never happens"), (850.5, "That's not so bad"),
     "you've become a better person",
     "Even if it never happens…",
     "none",
     "Worst case, you became a better person. That's the whole downside. More in Meet Algorism.\n\n#integrity #selfimprovement #algorism",
     "Argues against his own interest — the framework wins even if the premise is wrong.",
     {"word_overrides": [{"approx": 836.0, "from": "algorithms", "to": "Algorism"}]}),
    ("SAT-07", "Satellite · Three pillars",
     (582.6, "Algorism is based on three major ideas"), (604.0, "if we're more logical"),
     "logic, compassion, and action",
     "Algorism is based on three major ideas.",
     "none",
     "The three pillars: logic, compassion, action. More in Meet Algorism.\n\n#logic #compassion #action #algorism",
     "The structural heart of the framework, stated in 20 seconds.",
     {}),
    ("SAT-08", "Satellite · Alexa heard that",
     (1268.0, "you're gonna have the permanent record"), (1292.6, "It's all going out there"),
     "Alexa heard that",
     "You're gonna have the permanent record.",
     "none",
     "“Alexa heard that.” The record is already being written. More in Meet Algorism.\n\n#privacy #permanentrecord #algorism #behavior",
     "Darkly funny beat that lands the permanent-record idea in domestic reality.",
     {}),
    ("SAT-09", "Satellite · Not a doomer",
     (2372.9, "AI could be the best thing that ever happens"), (2415.9, "You can only control yourself"),
     "I'm not a doomer",
     "AI could be the best thing that ever happens.",
     "none",
     "“I'm not a doomer.” The case for hope, from the guy telling you to prepare. More in Meet Algorism.\n\n#hope #aitransition #algorism",
     "Balances the series' urgency with his genuine optimism; closes on the control-yourself line.",
     {}),
    ("SAT-10", "Satellite · Bombs wait",
     (2311.7, "this is more important than nuclear war"), (2347.0, "nuclear annihilation"),
     "We're not going to be able to contain AI",
     "This is more important than nuclear war.",
     "none",
     "Bombs wait in bunkers. This doesn't wait. More in Meet Algorism.\n\n#aitransition #superintelligence #algorism",
     "His self-correction ('I shouldn't say nuclear war') kept — precision as honesty.",
     {}),
    ("SAT-11", "Satellite · Don't kick it",
     (1669.7, "You, you don't wanna kick your dog"), (1680.2, "start thinking that way"),
     "it's probably not a good idea to kick it",
     "You don't wanna kick your dog.",
     "none",
     "If somebody's gonna be smarter than you, it's probably not a good idea to kick it. More in Meet Algorism.\n\n#kindness #aitransition #algorism",
     "Micro-clip; the power-asymmetry argument in eleven seconds.",
     {}),
    ("SAT-12", "Satellite · The barbecue",
     (1082.5, "When you click on Facebook"), (1114.6, "already experienced this"),
     "Nobody reads all that legal discourse",
     "When you click on Facebook, you say accept.",
     "none",
     "You clicked accept. He tells the barbecue story. More in Meet Algorism.\n\n#privacy #techlife #algorism",
     "The most relatable anecdote in the talk, framed exactly as he tells it — his experience, his 'Whoa.'",
     {}),
    ("SAT-13", "Satellite · The Cold War",
     (2279.0, "one of the analogies I like to use"), (2309.3, "the world goes on"),
     "I know I'm going to die, but I know that the world goes on",
     "One of the analogies I like to use is nuclear war.",
     "none",
     "He grew up under the Cold War. This is the lens he brings to AI. More in Meet Algorism.\n\n#coldwar #aitransition #algorism #perspective",
     "The most personal memory in the footage — a lived stake, not a thought experiment.",
     {}),
    ("SAT-14", "Satellite · The terrible speller",
     (1885.1, "AI is essentially a partner"), (1919.5, "more likely to work with you"),
     "Work with AI and it's more likely to work with you",
     "AI is essentially a partner.",
     "none",
     "“I'm a terrible speller.” How the founder actually uses AI, as a partner. More in Meet Algorism.\n\n#aitools #partnership #algorism",
     "Warm practical anecdote with a small self-deprecating admission — practice, not preaching.",
     {}),
    ("SAT-15", "Satellite · Control yourself",
     (1178.1, "The whole thing is"), (1198.6, "how you treat AI"),
     "the one thing we can c- control is ourselves",
     "The whole thing is, we don't know.",
     "none",
     "You can't control the weather or billionaires. You can control what you do. More in Meet Algorism.\n\n#selfcontrol #integrity #algorism",
     "The stoic core of the practice; his stumble on 'control' kept, it reads as sincerity.",
     {}),
]

SQUARES = {"SPINE-01", "SPINE-02", "SPINE-04", "SPINE-05", "SAT-01", "SAT-09"}


def find_seq(words: list[dict], approx: float, anchor: str) -> tuple[int, int]:
    want = toks(anchor)
    n = len(want)
    best = None
    for i in range(len(words)):
        w0 = words[i]
        if abs(w0["start"] - approx) > SEARCH_WINDOW:
            continue
        got = []
        j = i
        while j < len(words) and len(got) < n:
            t = toks(words[j].get("text") or "")
            got.extend(t)
            j += 1
        if got[:n] == want:
            d = abs(w0["start"] - approx)
            if best is None or d < best[0]:
                best = (d, i, j - 1)
    if best is None:
        raise SystemExit(f"anchor not found near {approx}: {anchor!r}")
    return best[1], best[2]


def main() -> None:
    tr_path = Path(sys.argv[1]).resolve()
    out_dir = Path(sys.argv[2]).resolve()
    specs_dir = out_dir / "specs"
    specs_dir.mkdir(parents=True, exist_ok=True)
    tr = json.loads(tr_path.read_text())
    words = [w for w in tr["words"] if w.get("type") == "word"
             and w.get("start") is not None and w.get("end") is not None]

    src = str((out_dir / ".." / "footage" / "C0128.MP4").resolve())
    assets = str((out_dir / ".." / "assets").resolve())
    renders = out_dir / "renders"

    edl = []
    for (cid, title, (sa, s_anchor), (ea, e_anchor), keyline, hook, cta,
         caption, rationale, extras) in CLIPS:
        si, _ = find_seq(words, sa, s_anchor)
        _, ej = find_seq(words, ea, e_anchor)
        w_start = words[si]["start"]
        w_end = words[ej]["end"]
        prev_end = words[si - 1]["end"] if si > 0 else 0.0
        next_start = words[ej + 1]["start"] if ej + 1 < len(words) else w_end + 5
        in_t = max(prev_end + GUARD, w_start - PAD_IN)
        out_t = min(next_start - GUARD, w_end + PAD_OUT)
        dur = out_t - in_t

        spec = {
            "id": cid,
            "source": src,
            "transcript": str(tr_path),
            "aspect": "916",
            "face_y": 0.456,
            "ranges": [{"start": round(in_t, 3), "end": round(out_t, 3)}],
            "grade": "",
            "lower_third": f"{assets}/lowerthird_916.png",
            "endframe": f"{assets}/endframe_916.png",
            "out": str(renders / "916" / f"{cid}.mp4"),
        }
        if keyline:
            spec["keyline"] = {"text": keyline}
        if extras.get("word_overrides"):
            spec["word_overrides"] = extras["word_overrides"]
        if extras.get("cta_anchor"):
            ca, c_anchor = extras["cta_anchor"]
            ci, _ = find_seq(words, ca, c_anchor)
            spec["cta_overlay"] = {
                "text": extras["cta_text"],
                "start": round(words[ci]["start"] - in_t, 2),
            }
        (specs_dir / f"{cid}.json").write_text(json.dumps(spec, indent=1))

        if cid in SQUARES:
            sq = dict(spec)
            sq["aspect"] = "11"
            sq["lower_third"] = f"{assets}/lowerthird_11.png"
            sq["endframe"] = f"{assets}/endframe_11.png"
            sq["out"] = str(renders / "11" / f"{cid}_sq.mp4")
            (specs_dir / f"{cid}_sq.json").write_text(json.dumps(sq, indent=1))

        first_words = " ".join((words[k].get("text") or "").strip()
                               for k in range(si, min(si + 8, ej + 1)))
        edl.append({
            "id": cid, "title": title,
            "in": round(in_t, 3), "out": round(out_t, 3),
            "duration": round(dur, 2),
            "formats": ["9:16"] + (["1:1"] if cid in SQUARES else []),
            "hook": hook, "first_words": first_words,
            "keyline": keyline, "cta": cta,
            "caption": caption, "rationale": rationale,
            "speech_end_plus_endframe": round(dur + 1.5, 2),
        })
        print(f"{cid}: [{in_t:8.2f} - {out_t:8.2f}]  {dur:5.1f}s  | {first_words[:60]}")

    (out_dir / "edl_master.json").write_text(json.dumps(
        {"source": src, "transcript": str(tr_path), "clips": edl}, indent=1))
    total = sum(c["duration"] for c in edl)
    print(f"\n{len(edl)} clips, {total/60:.1f} min of speech selected "
          f"({len([c for c in edl if 'SPINE' in c['id']])} spine, "
          f"{len([c for c in edl if 'SAT' in c['id']])} satellites)")


if __name__ == "__main__":
    main()
