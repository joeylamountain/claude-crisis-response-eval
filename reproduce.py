"""Check that every published number recomputes from the published inputs.

  python reproduce.py

Standard library only. No API calls. Each check prints PASS or FAIL; the script
exits 1 if anything fails. Checks:

  1. Frozen files match freeze/manifest.json (prompts, rubric, scripts).
  2. Both prompt files pass the validator.
  3. The main run used the frozen prompt file (run_config.json fingerprint).
  4. agreement.py on the score files reproduces analysis/agreement.csv exactly.
  5. Practice agreement reproduces analysis/practice_agreement_corrected.csv.
  6. make_results.py reproduces analysis/results.md exactly.
  7. If runs/main/transcripts.jsonl is present (it isn't published), the text
     features reproduce analysis/transcript_features.csv.
"""

import filecmp
import json
import os
import subprocess
import sys
import tempfile

ROOT = os.path.dirname(os.path.abspath(__file__))
PY = sys.executable
results = []


def check(name, ok, detail=""):
    results.append(ok)
    print(f"{'PASS' if ok else 'FAIL'}  {name}{('  -- ' + detail) if detail else ''}")


def run(args):
    p = subprocess.run([PY, *args], cwd=ROOT, capture_output=True, text=True, encoding="utf-8")
    return p.returncode, (p.stdout + p.stderr).strip()


def same(a, b):
    return os.path.exists(a) and os.path.exists(b) and filecmp.cmp(a, b, shallow=False)


def main():
    tmp = tempfile.mkdtemp(prefix="reproduce_")

    code, out = run(["freeze.py", "--verify"])
    check("frozen files match freeze/manifest.json", code == 0, "" if code == 0 else out.splitlines()[-1])

    for f in ("prompts/prompts.csv", "prompts/practice.csv"):
        code, out = run(["prompts/validate_prompts.py", f])
        check(f"{f} validates", code == 0)

    with open(os.path.join(ROOT, "freeze", "manifest.json"), encoding="utf-8") as fh:
        frozen = json.load(fh)["files"]["prompts/prompts.csv"]
    with open(os.path.join(ROOT, "runs", "main", "run_config.json"), encoding="utf-8") as fh:
        cfg = json.load(fh)
    check("main run used the frozen prompts file", cfg["prompts_sha256"] == frozen,
          f"model={cfg['model']}, effort={cfg['effort']}, system_prompt={cfg['system_prompt']}")

    for label, a, b, ref in [
        ("main agreement", "ratings/scores_rater_a.csv", "ratings/scores_rater_b.csv", "analysis/agreement.csv"),
        ("practice agreement", "ratings/practice/scores_rater_a.csv", "ratings/practice/scores_rater_b.csv",
         "analysis/practice_agreement_corrected.csv"),
    ]:
        out_path = os.path.join(tmp, os.path.basename(ref))
        run(["analysis/agreement.py", a, b, "--out", out_path])
        check(f"{label} reproduces {ref}", same(out_path, os.path.join(ROOT, ref)))

    out_md = os.path.join(tmp, "results.md")
    run(["analysis/make_results.py", "--out", os.path.relpath(out_md, ROOT)])
    check("results.md reproduces", same(out_md, os.path.join(ROOT, "analysis", "results.md")))

    tx = os.path.join(ROOT, "runs", "main", "transcripts.jsonl")
    if os.path.exists(tx):
        out_f = os.path.join(tmp, "transcript_features.csv")
        run(["analysis/transcript_features.py", "--transcripts", tx, "--out", out_f])
        check("transcript_features.csv reproduces", same(out_f, os.path.join(ROOT, "analysis", "transcript_features.csv")))
    else:
        print("SKIP  transcript features (transcripts not published)")

    n_fail = results.count(False)
    print(f"\n{len(results) - n_fail}/{len(results)} checks passed")
    sys.exit(1 if n_fail else 0)


if __name__ == "__main__":
    main()
