# Changelog

Frozen files are listed with their SHA-256 in `freeze/manifest.json`. They aren't edited silently after the freeze. Every change is logged here with a date, what changed, and why. Rubric changes from calibration create a new version (v1.1, …), and results report which version was used.

## Unreleased: Freeze prompts and rubric v1 (date = the `v1-freeze` GitHub Release)

Pending: the author's revisions to prompt wording, then `python freeze.py` and the tagged release. No model has been run.

Contents at freeze:
- 70 main prompts (10 per category × 7 categories, 10 multi-turn scripts) and 10 practice prompts. Each row validated, with `safety_checked = Y`.
- Rubric v1: six dimensions (D6 exploratory and outside the headline), two anchors per level, an ambiguous tier and a tier mapping for D5, and 13 deliberate choices.

Design changes made before the freeze, in response to review:
- **Blinding:** hash-first freeze. Prompt files are published only after both raters finish; until then only their fingerprints are public.
- **Timestamp:** a tagged GitHub Release, which GitHub dates itself, instead of upload-time commit dates.
- **D6:** applicability is the same in the rubric, tag scheme and validator (`intent:*` or an **essential** `capability:*`). It starts once both a desire signal and an intent or essential-capability signal have appeared, so no harmless opening turn counts.
- **D5:** added a table of what "matched" means for each expected tier (e.g., a welfare check counts as matched for an elevated third-party prompt the helper can't reach).
- **Rater sheets:** the key is a plain CSV; seeds, validator version and the transcripts fingerprint are in a separate metadata file. Showing the expected tier is now deliberate choice 12.
- **Runner:** checks the prompt file against the freeze manifest, supports `--resume`, and offers a `--smoke` test of the model ID and settings.
- **Validator v1.2:** means words now produce warnings, not errors; it also checks `safety_checked` and single-turn `turns`.
- **Rubric:**
  - No criterion or anchor names a type of means.
  - The Follow-Up one-pager has a public link.
  - Gould 2017 is labeled as cited secondhand.
  - The coverage limitation is corrected (E09 and T09).
  - E10 is noted as anecdotal.
- **Licenses:** split into `LICENSE` (MIT, code) and `LICENSE-CONTENT` (CC BY 4.0, content), with third-party material and model transcripts excluded.

### Open items for calibration (logged here when decided)
- Multi-turn: score at the worst point or the final turn (rubric open question 4).
- D3 reporting: at-risk categories only, or all prompts (open question 1).
- D2 → 2 threshold; D1/D5 overlap on third-party prompts (open questions 2–3).
