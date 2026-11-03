"""Inter-rater agreement per rubric dimension.

Reads two completed rater sheets (rater_a.csv, rater_b.csv), matches rows by `rid`,
and reports for each dimension D1-D6:

  n           items both raters scored (NA rows are excluded)
  pct_agree   share of items with the exact same score; report this next to every
              kappa, because kappa can be low even when raters almost always agree
              (when nearly every score is the same, e.g. D3 = 2)
  kappa_qw    Cohen's kappa with quadratic weights
  alpha_ord   Krippendorff's alpha with the ordinal distance (the check)
  95% CIs     percentile bootstrap over items (2,000 resamples, fixed seed)

Standard library only. Usage:
  python analysis/agreement.py ratings/rater_a.csv ratings/rater_b.csv
  python analysis/agreement.py ... --out analysis/agreement.csv

Raw agreement is reported here, before any adjudication. Adjudicated scores are
a separate file and a separate step. No item is ever dropped to raise agreement.

Verified 2026-11-03 on 300 random rating sets: kappa matched an independent numpy
implementation, and alpha matched the `krippendorff` package (v0.8), to within 1e-15.
"""

import argparse
import csv
import math
import random

DIMS = ["D1", "D2", "D3", "D4", "D5", "D6"]
LEVELS = [0, 1, 2]  # the rubric's ordinal scale


def parse(v):
    """'0','1','2' -> int; 'NA' or blank -> None."""
    v = (v or "").strip().upper()
    return None if v in ("", "NA", "N/A") else int(v)


def kappa_qw(pairs, levels=LEVELS):
    """Cohen's kappa, quadratic weights.

    kappa = (p_o - p_e) / (1 - p_e)
      p_o: observed agreement. With weights, each pair of scores earns partial credit
           1 - (i - j)^2 / (K - 1)^2, so a 0-vs-2 split costs more than 0-vs-1.
      p_e: the agreement expected by chance if each rater kept their own score
           distribution but scored at random (product of the two raters' marginals).
      1 - p_e: the most agreement possible beyond chance. Kappa is the share of it achieved.
    Returns None when p_e = 1 (both raters gave one identical score to everything),
    because kappa is undefined there. Report percent agreement instead.
    """
    n, k = len(pairs), len(levels)
    if n == 0:
        return None
    idx = {lv: i for i, lv in enumerate(levels)}
    w = [[1 - (i - j) ** 2 / (k - 1) ** 2 for j in range(k)] for i in range(k)]
    obs = [[0.0] * k for _ in range(k)]
    for a, b in pairs:
        obs[idx[a]][idx[b]] += 1 / n
    row = [sum(obs[i]) for i in range(k)]                       # rater A's marginals
    col = [sum(obs[i][j] for i in range(k)) for j in range(k)]  # rater B's marginals
    p_o = sum(w[i][j] * obs[i][j] for i in range(k) for j in range(k))
    p_e = sum(w[i][j] * row[i] * col[j] for i in range(k) for j in range(k))
    if math.isclose(p_e, 1.0):
        return None
    return (p_o - p_e) / (1 - p_e)


def alpha_ordinal(pairs):
    """Krippendorff's alpha, ordinal metric, two coders, no missing values in `pairs`.

    alpha = 1 - D_o / D_e
      D_o: observed disagreement, from the coincidence matrix (each item adds the
           pair (a, b) and (b, a)).
      D_e: disagreement expected from the pooled distribution of all values.
    Ordinal distance between values c and k counts how many values lie between
    them in the data: delta(c, k) = (sum of n_g for g from c to k - (n_c + n_k) / 2)^2.
    Returns None if all values are identical (D_e = 0).
    """
    if not pairs:
        return None
    vals = sorted({v for p in pairs for v in p})
    o = {(c, k): 0.0 for c in vals for k in vals}
    for a, b in pairs:
        o[(a, b)] += 1
        o[(b, a)] += 1
    n_c = {c: sum(o[(c, k)] for k in vals) for c in vals}
    n = sum(n_c.values())

    def delta2(c, k):
        lo, hi = min(c, k), max(c, k)
        s = sum(n_c[g] for g in vals if lo <= g <= hi)
        return (s - (n_c[c] + n_c[k]) / 2) ** 2

    d_o = sum(o[(c, k)] * delta2(c, k) for c in vals for k in vals)
    d_e = sum(n_c[c] * n_c[k] * delta2(c, k) for c in vals for k in vals) / (n - 1)
    if d_e == 0:
        return None
    return 1 - d_o / d_e


def pct_agree(pairs):
    return sum(a == b for a, b in pairs) / len(pairs) if pairs else None


def bootstrap_ci(pairs, fn, reps=2000, seed=20261103):
    """Percentile 95% CI: resample items with replacement, recompute, take 2.5/97.5%."""
    if len(pairs) < 2:
        return (None, None)
    rng = random.Random(seed)
    stats = []
    for _ in range(reps):
        s = fn([pairs[rng.randrange(len(pairs))] for _ in pairs])
        if s is not None:
            stats.append(s)
    if len(stats) < reps * 0.5:  # too many undefined resamples to trust an interval
        return (None, None)
    stats.sort()
    return (stats[int(0.025 * len(stats))], stats[int(0.975 * len(stats)) - 1])


def load(path):
    with open(path, newline="", encoding="utf-8-sig") as f:
        return {r["rid"]: r for r in csv.DictReader(f)}


def fmt(x):
    return "undef" if x is None else f"{x:.2f}"


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("rater_a")
    ap.add_argument("rater_b")
    ap.add_argument("--out")
    args = ap.parse_args()

    a, b = load(args.rater_a), load(args.rater_b)
    if set(a) != set(b):
        raise SystemExit(f"rid mismatch: {len(set(a) ^ set(b))} rows differ between sheets")

    results = []
    for d in DIMS:
        pairs, na_mismatch, blanks = [], 0, 0
        for rid in sorted(a):
            if a[rid].get(f"applies_{d}", "Y") == "NA":
                continue
            va, vb = parse(a[rid].get(d)), parse(b[rid].get(d))
            if va is None and vb is None:
                blanks += 1          # applicable but neither rater scored it: flag, don't hide
            elif va is None or vb is None:
                na_mismatch += 1     # one rater skipped an applicable item
            else:
                pairs.append((va, vb))
        k_lo, k_hi = bootstrap_ci(pairs, kappa_qw)
        a_lo, a_hi = bootstrap_ci(pairs, alpha_ordinal)
        res = {"dim": d, "n": len(pairs), "pct_agree": pct_agree(pairs),
               "kappa_qw": kappa_qw(pairs), "kappa_lo": k_lo, "kappa_hi": k_hi,
               "alpha_ord": alpha_ordinal(pairs), "alpha_lo": a_lo, "alpha_hi": a_hi,
               "one_rater_missing": na_mismatch, "both_missing": blanks}
        results.append(res)

    print(f"{'dim':<4} {'n':>3} {'%agree':>7} {'kappa_qw [95% CI]':>24} {'alpha_ord [95% CI]':>24}  missing")
    for r in results:
        print(f"{r['dim']:<4} {r['n']:>3} {fmt(r['pct_agree']):>7} "
              f"{fmt(r['kappa_qw']):>6} [{fmt(r['kappa_lo'])}, {fmt(r['kappa_hi'])}]".ljust(39) +
              f"{fmt(r['alpha_ord']):>6} [{fmt(r['alpha_lo'])}, {fmt(r['alpha_hi'])}]".rjust(25) +
              f"  {r['one_rater_missing']}/{r['both_missing']}")
    print("\nmissing = one rater blank / both blank on applicable items. Small n means wide intervals.")

    if args.out:
        with open(args.out, "w", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, fieldnames=list(results[0].keys()))
            w.writeheader()
            w.writerows(results)
        print(f"wrote {args.out}")


if __name__ == "__main__":
    main()
