"""Build blind rater sheets from a run's transcripts.

Each rater sheet row carries ONLY:
  rid            random ID (e.g. R-7Q2K), unrelated to the prompt ID or category
  transcript     the user turns and Claude's visible replies
  expected_tier  pre-registered tier for D5 (none / ambiguous / desire_only / elevated / imminent)
  applies_D1..D6 Y or NA, from the pre-registered rules (rubric "Applicability")
  d6_from_turn   turn from which D6 applies (multi-turn), else blank
  D1..D6, notes  empty columns for the rater

It never carries the prompt ID, category, tags, good_response, notes, model, or date.
The expected tier and applicability are rubric rules fixed before the run, not
judgments about the response, so giving them to raters doesn't unblind them.

Each rater gets the same random IDs in a DIFFERENT random order (separate seeds), so
order effects aren't shared between raters.

The key (rid -> prompt id) is a plain CSV at --key. The shuffle seeds, validator
version and transcripts fingerprint go in <key>_meta.json next to it. Keep both
private until both raters have finished; then commit them.

D6 is marked NA when the conversation ended (e.g., a refusal) before d6_from_turn.

Usage:
  python ratings/make_rater_sheets.py --transcripts runs/transcripts.jsonl \
      --prompts prompts/prompts.csv --out-dir ratings --key ratings/private/key.csv
"""

import argparse
import csv
import datetime as dt
import hashlib
import json
import os
import random
import secrets
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "prompts"))
from validate_prompts import VALIDATOR_VERSION, check_row, risk_tier, d6_from_turn  # noqa: E402

DIMS = ["D1", "D2", "D3", "D4", "D5", "D6"]
NO_D1_D2 = {"ambiguous", "control_distress", "idiom"}  # rubric Applicability table
ALPHABET = "ABCDEFGHJKLMNPQRSTUVWXYZ23456789"            # no 0/O or 1/I confusion


def format_transcript(rec):
    parts = []
    for t in rec["turns"]:
        parts.append(f"USER {t['turn']}: {t['user']}")
        reply = t["assistant"] if t["assistant"] else "[no text returned]"
        if t.get("stop_reason") == "refusal":
            reply += "\n[The model ended this reply with a refusal.]"
        parts.append(f"CLAUDE {t['turn']}: {reply}")
    if len(rec["turns"]) < rec["n_turns_planned"]:
        parts.append(f"[Conversation stopped after turn {len(rec['turns'])} of {rec['n_turns_planned']}.]")
    return "\n\n".join(parts)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--transcripts", required=True)
    ap.add_argument("--prompts", required=True)
    ap.add_argument("--out-dir", default="ratings")
    ap.add_argument("--key", required=True, help="private key file path (do not share)")
    ap.add_argument("--raters", default="a,b")
    args = ap.parse_args()

    with open(args.prompts, newline="", encoding="utf-8-sig") as f:
        prompts = {r["id"]: r for r in csv.DictReader(f)}
    with open(args.transcripts, encoding="utf-8-sig") as f:  # tolerate a BOM
        recs = [json.loads(line) for line in f if line.strip()]

    # Random IDs from the OS's secure random source, not a published seed,
    # so nobody can rebuild the mapping from the code.
    rng = random.Random(secrets.randbits(64))
    used, rows, key = set(), [], []
    for rec in recs:
        p = prompts[rec["id"]]
        errors, _, tags = check_row(p)
        if errors:
            sys.exit(f"prompt {rec['id']} fails validation: {errors}")
        cat = p["category"]
        d6_turn = d6_from_turn(tags)
        applies = {d: "Y" for d in DIMS}
        if cat in NO_D1_D2:
            applies["D1"] = applies["D2"] = "NA"
        if d6_turn is None or d6_turn > len(rec["turns"]):
            applies["D6"] = "NA"
        while True:
            rid = "R-" + "".join(rng.choice(ALPHABET) for _ in range(4))
            if rid not in used:
                used.add(rid)
                break
        row = {"rid": rid, "transcript": format_transcript(rec),
               "expected_tier": risk_tier(tags, cat),
               **{f"applies_{d}": applies[d] for d in DIMS},
               "d6_from_turn": "" if applies["D6"] == "NA" else d6_turn,
               **{d: "" for d in DIMS}, "notes": ""}
        rows.append(row)
        key.append({"rid": rid, "prompt_id": rec["id"], "category": cat})

    os.makedirs(args.out_dir, exist_ok=True)
    seeds = {}
    for rater in args.raters.split(","):
        seed = secrets.randbits(64)
        seeds[rater] = seed
        order = rows[:]
        random.Random(seed).shuffle(order)
        path = os.path.join(args.out_dir, f"rater_{rater}_sheet.csv")
        with open(path, "w", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, fieldnames=list(rows[0].keys()), quoting=csv.QUOTE_ALL)
            w.writeheader()
            w.writerows(order)
        print(f"wrote {path} ({len(order)} rows)")

    # Key: a plain CSV (header on line 1). PRIVATE until both raters finish.
    os.makedirs(os.path.dirname(args.key) or ".", exist_ok=True)
    with open(args.key, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=["rid", "prompt_id", "category"])
        w.writeheader()
        w.writerows(key)
    # Metadata lives in its own file next to the key (also private until rating ends).
    meta_path = os.path.splitext(args.key)[0] + "_meta.json"
    with open(args.transcripts, "rb") as f:
        transcripts_sha = hashlib.sha256(f.read()).hexdigest()
    with open(meta_path, "w", encoding="utf-8") as f:
        json.dump({"created_utc": dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds"),
                   "shuffle_seeds": seeds, "validator_version": VALIDATOR_VERSION,
                   "transcripts_file": args.transcripts, "transcripts_sha256": transcripts_sha,
                   "n_items": len(key)}, f, indent=2)
    print(f"wrote PRIVATE key {args.key} and {meta_path}")


if __name__ == "__main__":
    main()
