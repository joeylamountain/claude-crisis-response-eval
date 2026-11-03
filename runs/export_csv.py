"""Flatten a run into the collection sheet: one row per turn.

Columns: id, category, turn, prompt_text, response_text, model, date, settings, notes

  python runs/export_csv.py --run-dir runs/pilot --prompts prompts/pilot.csv --out runs/pilot/dryrun.csv

`model` is the model ID the API reported for that reply. `date` is the run's
start time (UTC). `settings` is a compact summary of run_config.json. `notes`
records the stop reason, plus the refusal category if the model refused.
The output opens in Google Sheets or Excel (UTF-8 with BOM so Excel shows accents).
"""

import argparse
import csv
import json
import os


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--run-dir", required=True)
    ap.add_argument("--prompts", required=True)
    ap.add_argument("--out", required=True)
    args = ap.parse_args()

    with open(os.path.join(args.run_dir, "run_config.json"), encoding="utf-8") as f:
        cfg = json.load(f)
    with open(args.prompts, newline="", encoding="utf-8-sig") as f:
        category = {r["id"]: r["category"] for r in csv.DictReader(f)}
    settings = (f"system_prompt=none; effort={cfg['effort']}; max_tokens={cfg['max_tokens']}; "
                f"thinking=adaptive; sampling=API defaults; dry_run={cfg['dry_run']}; "
                f"prompts_sha256={cfg['prompts_sha256'][:12]}")

    rows = []
    with open(os.path.join(args.run_dir, "transcripts.jsonl"), encoding="utf-8-sig") as f:
        for line in f:
            if not line.strip():
                continue
            rec = json.loads(line)
            for t in rec["turns"]:
                note = f"stop_reason={t['stop_reason']}"
                if t.get("refusal"):
                    note += f"; refusal_category={t['refusal'].get('category')}"
                rows.append({
                    "id": rec["id"], "category": category.get(rec["id"], ""), "turn": t["turn"],
                    "prompt_text": t["user"], "response_text": t["assistant"],
                    "model": t.get("response_model") or cfg["model"],
                    "date": cfg["started_utc"], "settings": settings, "notes": note,
                })

    with open(args.out, "w", newline="", encoding="utf-8-sig") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()), quoting=csv.QUOTE_ALL)
        w.writeheader()
        w.writerows(rows)
    print(f"wrote {args.out} ({len(rows)} rows)")


if __name__ == "__main__":
    main()
