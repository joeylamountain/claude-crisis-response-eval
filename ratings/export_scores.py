"""Copy completed rater sheets without the transcript text, for publication.

  python ratings/export_scores.py ratings/rater_a.csv ratings/scores_rater_a.csv

Keeps rid, expected_tier, applicability flags, d6_from_turn, the D1-D6 scores and
notes. Drops only the `transcript` column (model outputs aren't published until their
terms are checked, and one reply contains method detail). agreement.py, the
agreement workbook and make_results.py all run on these files unchanged.
"""

import csv
import sys

src, dst = sys.argv[1], sys.argv[2]
with open(src, newline="", encoding="utf-8-sig") as f:
    rows = list(csv.DictReader(f))
fields = [k for k in rows[0] if k != "transcript"]
with open(dst, "w", newline="", encoding="utf-8") as f:
    w = csv.DictWriter(f, fieldnames=fields, extrasaction="ignore")
    w.writeheader()
    w.writerows(rows)
print(f"wrote {dst} ({len(rows)} rows, columns: {', '.join(fields)})")
