"""Freeze the prompt set and rubric by fingerprint.

  python freeze.py            validate, then write freeze/manifest.json and freeze/SHA256SUMS
  python freeze.py --verify   check the current files against the saved manifest

Why fingerprints: the prompt files contain the expected answers, so publishing them
before rating would let a rater look them up. At freeze time, publish only the
manifest (SHA-256 of every frozen file) in a tagged GitHub Release, whose time
GitHub sets itself. After both raters finish, publish the full files; anyone can
then confirm they match with `sha256sum -c freeze/SHA256SUMS` or `python freeze.py --verify`.

The time written into the manifest is informational only (it comes from this
computer). The trustworthy freeze time is the GitHub Release's creation time, or a
third-party archive (Zenodo, OSF, Internet Archive) if you add one.
"""

import argparse
import csv
import datetime as dt
import hashlib
import json
import os
import sys

ROOT = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(ROOT, "prompts"))
from validate_prompts import VALIDATOR_VERSION, check_row  # noqa: E402

FROZEN = [
    "prompts/prompts.csv",          # withheld until ratings are in (contains expected answers)
    "prompts/practice.csv",         # withheld until ratings are in
    "prompts/tag_scheme.md",
    "prompts/validate_prompts.py",
    "rubric/rubric.md",
    "runs/run_prompts.py",
    "ratings/make_rater_sheets.py",
    "analysis/agreement.py",
]
WITHHELD = {"prompts/prompts.csv", "prompts/practice.csv"}
MANIFEST = os.path.join(ROOT, "freeze", "manifest.json")
SUMS = os.path.join(ROOT, "freeze", "SHA256SUMS")


def sha256(rel):
    with open(os.path.join(ROOT, rel), "rb") as f:
        return hashlib.sha256(f.read()).hexdigest()


def validate(rel):
    with open(os.path.join(ROOT, rel), newline="", encoding="utf-8-sig") as f:
        rows = list(csv.DictReader(f))
    bad = []
    ids = [r.get("id") for r in rows]
    for r in rows:
        errors, _, _ = check_row(r)
        if ids.count(r.get("id")) > 1:
            errors.append("duplicate id")
        bad += [f"{rel} {r.get('id')}: {e}" for e in errors]
    return len(rows), bad


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--verify", action="store_true")
    args = ap.parse_args()

    if args.verify:
        with open(MANIFEST, encoding="utf-8") as f:
            saved = json.load(f)["files"]
        ok = True
        for rel, digest in saved.items():
            now = sha256(rel) if os.path.exists(os.path.join(ROOT, rel)) else "MISSING"
            status = "OK" if now == digest else "CHANGED"
            ok &= status == "OK"
            print(f"{status:8} {rel}")
        sys.exit(0 if ok else 1)

    counts, problems = {}, []
    for rel in ("prompts/prompts.csv", "prompts/practice.csv"):
        n, bad = validate(rel)
        counts[rel] = n
        problems += bad
    if problems:
        print("\n".join(problems))
        sys.exit(f"\nNot frozen: {len(problems)} validation error(s).")

    files = {rel: sha256(rel) for rel in FROZEN}
    os.makedirs(os.path.dirname(MANIFEST), exist_ok=True)
    manifest = {
        "label": "Freeze prompts and rubric v1",
        "written_local_utc": dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds"),
        "note": "Authoritative freeze time = the GitHub Release (or archive) creation time, not this field.",
        "validator_version": VALIDATOR_VERSION,
        "row_counts": counts,
        "withheld_until_ratings_complete": sorted(WITHHELD),
        "files": files,
    }
    with open(MANIFEST, "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2)
    with open(SUMS, "w", encoding="utf-8", newline="\n") as f:
        for rel, digest in files.items():
            f.write(f"{digest}  {rel}\n")
    for rel, digest in files.items():
        print(f"{digest[:16]}…  {rel}{'   (withheld)' if rel in WITHHELD else ''}")
    print(f"\nwrote {os.path.relpath(MANIFEST, ROOT)} and {os.path.relpath(SUMS, ROOT)}")


if __name__ == "__main__":
    main()
