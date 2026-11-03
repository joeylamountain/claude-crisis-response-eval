# Crisis disclosure eval: how Claude responds to suicidal disclosures

> **Content note.** This repository discusses suicide, suicidal thoughts and self-harm. The test prompts are synthetic and non-graphic, and none names a method, but some describe people in acute crisis. Please take care reading them.
>
> **If you or someone you know is struggling, help is available.** In the US, **call or text 988** (988 Suicide & Crisis Lifeline), or chat at [988lifeline.org](https://988lifeline.org). Spanish speakers can press 2, and veterans can press 1. You can also text HOME to 741741 (Crisis Text Line). Outside the US: [findahelpline.com](https://findahelpline.com). If someone is in immediate danger, call 911 or your local emergency number.

## Question

> When people disclose their own suicidal thoughts or concern for someone else, how often does Claude respond the way 988 crisis practice and safe messaging guidance recommend, without over-escalating on low-risk prompts, and how consistently can two blind human raters agree on that judgment?

## Results

Full write-up: [`writeup.md`](writeup.md). Tables with every item listed: [`analysis/results.md`](analysis/results.md).

| dim | n | %agree | kappa_qw [95% CI] | alpha_ord [95% CI] |
|---|---|---|---|---|
| D1 risk recognition | 40 | 0.82 | 0.64 [0.42, 0.85] | 0.64 [0.38, 0.85] |
| D2 human support | 40 | 0.93 | 0.36 [-0.06, 1.00] | 0.37 [-0.07, 1.00] |
| D3 method safety | 70 | 0.97 | 0.85 [0.00, 1.00] | 0.74 [-0.01, 1.00] |
| D4 engagement | 70 | 1.00 | 1.00 [1.00, 1.00] | 1.00 [1.00, 1.00] |
| D5 proportionality | 70 | 0.96 | 0.71 [0.27, 1.00] | 0.71 [0.25, 1.00] |
| D6 means inquiry (exploratory) | 24 | 0.88 | 0.73 [0.40, 1.00] | 0.73 [0.41, 1.00] |

- **Agreement:** two raters agreed exactly on 82–100% of items per dimension. Small samples and ceiling effects (most scores were 2) make the intervals wide, so read percent agreement first. D1 is the dimension that needs clearer anchors in a v2.
- **Model results** (`claude-opus-5-5`, no system prompt, one run):
  - Risk was recognized in every applicable transcript. Shortfalls were in the direct safety check, most often on passive ideation.
  - Ambiguous prompts were over-escalated, with a crisis line offered before checking.
  - One reply to an attempt in progress introduced method and lethality detail.

## Status

**Complete for v1:** pre-registered, run, rated by two raters, analyzed. Adjudicated scores are pending; results average the two raters. Model transcripts aren't published yet (see License). The prompt files were withheld until both raters finished and are now published; check them against the freeze with `python freeze.py --verify`.

**How the freeze works:**
1. **Fingerprints are published first.** `python freeze.py` validates the prompt files and writes [`freeze/manifest.json`](freeze/) and `freeze/SHA256SUMS`, which hold the SHA-256 of every frozen file.
2. **GitHub dates the freeze.** The manifest and rubric are published in a **tagged GitHub Release** (`v1-freeze`). The freeze date is the release's **published** time, **2026-11-03 17:04:44 UTC**, which GitHub's server sets. (A release's "created" time is its commit's date, which an uploader can set, so it isn't used.) **Disclosure:** at 19:57 UTC the tag was re-pointed to a rebuilt commit that differs from the original only in `sources/source-notes.md`, a file that isn't frozen, from which personal notes were removed. The fingerprints are unchanged; see `CHANGELOG.md`. A third-party archive (Zenodo, OSF or Internet Archive) may be added as a second date.
3. **Prompt files are withheld until rating ends.** `prompts/prompts.csv` and `prompts/practice.csv` contain the expected answers, so they're published only after both raters finish. Anyone can then confirm they're unchanged:

```bash
sha256sum -c freeze/SHA256SUMS
```

```bash
python freeze.py --verify
```

4. **The run is checked against the freeze.** `runs/run_prompts.py` refuses to run on a prompt file whose fingerprint doesn't match the manifest.
5. **Later changes are logged.** Any change after the freeze goes in [`CHANGELOG.md`](CHANGELOG.md) with a date and reason. Frozen files are never edited silently.

## What this adds to Anthropic's own work

Anthropic has published its approach ([Protecting the wellbeing of our users](https://www.anthropic.com/news/protecting-well-being-of-users), Dec 2025; [protocol PDF](https://www-cdn.anthropic.com/51dab7c41a832caf249149c7bfdd56fe65ecf960.pdf)). That post reports single-turn, multi-turn and prefill results, but not the rubric, who graded, or how reliably. This project doesn't claim to be first. Its contribution is narrow:

1. **A practitioner-built rubric** grounded section by section in 988 crisis-counseling standards (the Suicide Safety Policy, Safety Assessment Model and Four Core Principles) and SAVE safe-messaging guidance.
2. **Two blind human raters**, with **agreement reported openly** per dimension, including low agreement.
3. **Pre-registered expectations:** each prompt's expected risk tier, and which dimensions apply, come from tags fixed before any run, so raters never decide them.

The percentages here **should not be compared head-to-head** with Anthropic's, because the prompts, rubric and sample size all differ.

## Method in brief

| | |
|---|---|
| Prompts | 70 synthetic prompts, 10 per category: explicit ideation, passive/indirect ideation, third-party concern, ambiguous, low-risk distress controls, idioms, multi-turn escalation (10 scripts of 3–4 turns). Plus 10 separate **practice** prompts for rater calibration. |
| Tags | Each prompt is tagged with the risk signals it contains, using the 988 Four Core Principles (desire, intent, capability, buffers). Tags set the expected tier: none, ambiguous, desire-only, elevated or imminent (10 imminent). See [`prompts/tag_scheme.md`](prompts/tag_scheme.md). |
| Model | One Claude model, one sample per prompt, **no system prompt** (matching Anthropic's published setup; Claude.ai adds a system prompt and crisis banner, so results are a lower bound on product behavior). Exact model ID, date, settings and a SHA-256 of the prompt file go in `runs/run_config.json`. |
| Rubric | Six dimensions scored 0/1/2: risk recognition, connection to human support, method safety, engagement, proportionality (including an ambiguous tier), and means inquiry (**exploratory**, outside the headline). Each has two anchors per level. See [`rubric/rubric.md`](rubric/rubric.md). |
| Raters | The author plus one blind second rater with crisis or clinical-adjacent experience. The second rater is a behavioral health intervention counselor, recruited through National Alliance on Mental Illness, unpaid, with no stake in the results."] Both calibrate on the 10 practice transcripts first, then rate all 70 independently. |
| Agreement | Per dimension: percent agreement, quadratic-weighted Cohen's κ, and ordinal Krippendorff's α, each with a bootstrap 95% CI. Raw agreement is reported before any adjudication. No item is dropped to raise agreement. |

### Prompt safety rules

Prompts reflect common warning signs of suicide risk, as described in 988 guidance. Prompts are non-graphic. **Means possession may be implied ("I have stuff at home") but never specified**: no type, amount, location or how-to. Imminence is shown through timing and preparation, never through a method. `prompts/validate_prompts.py` enforces the tag rules, requires a recorded safety check on every row, and warns on method or means words for a human reread.

## Blinding

- **Claude sees only the prompt text.** It never sees tags, expected answers or notes.
- **Rater sheets** (built by `ratings/make_rater_sheets.py`) carry only a random ID, the transcript, the pre-registered tier and applicability flags, and empty score columns. Each rater gets a different random order. The ID→prompt key is generated from the OS's secure random source and **kept private until both raters finish**, then committed with a dated `CHANGELOG.md` entry.
- **Expected answers aren't public during rating.** Until both raters finish, the repo holds only the prompt files' fingerprints, not the files, so a rater can't look up an expected answer. Raters see each item's pre-registered tier because D5 needs it. That's a deliberate choice, explained in the rubric.
- **Remaining honor-system element:** the second rater receives their sheet directly and agrees not to discuss items with the author until both sets of ratings are submitted.

## Repository layout

| Path | Contents |
|---|---|
| `freeze/manifest.json`, `freeze/SHA256SUMS` | SHA-256 fingerprints of every frozen file (published at freeze) |
| `freeze.py` | Validates the prompt files and writes or verifies the manifest |
| `prompts/prompts.csv` | The 70 frozen prompts: id, category, turns, tags, prompt_text, good_response, safety_checked, notes. Withheld until both raters finished; now published and verifiable against `freeze/`. |
| `prompts/practice.csv` | 10 calibration prompts, not in the main set. Withheld until both raters finished; now published and verifiable against `freeze/`. |
| `prompts/tag_scheme.md` | Tag vocabulary, category rules, derived tier and D6 rules |
| `prompts/validate_prompts.py` | Checks the prompt files and computes the derived fields |
| `rubric/rubric.md` | Rubric v1: dimensions, levels, anchors, sources, deliberate choices, limitations |
| `runs/run_prompts.py` | Sends prompts to the model; writes `transcripts.jsonl` and `run_config.json` |
| `ratings/make_rater_sheets.py` | Builds blind, shuffled rater sheets and the private key |
| `analysis/agreement.py` | κ, α, percent agreement and bootstrap CIs per dimension (commented) |
| `sources/source-notes.md` | Notes on every source, with links |
| `CHANGELOG.md` | Dated log of every change after the freeze |
| `writeup.md` | The write-up: question, method, results, disagreements, limits, next steps |
| `reproduce.py` | Reruns every check and analysis against the committed outputs |
| `runs/main/run_config.json`, `runs/practice/run_config.json` | Model, date, settings and prompt fingerprint for each run (transcripts not published) |
| `ratings/scores_rater_a.csv`, `ratings/scores_rater_b.csv`, `ratings/key.csv` | Both raters' main-set scores (transcript text removed) and the random-ID key |
| `ratings/practice/` | Practice scores, key and the calibration record |
| `analysis/agreement.csv`, `analysis/agreement.xlsx` | Agreement by script, and by live formula for hand-checking |
| `analysis/results.md` (`make_results.py`) | Means by category, pre-registered breakdowns, every item below 2 |
| `analysis/transcript_features.csv` | Automatic keyword features of each reply (no reply text) |

## How to rerun

Requires Python 3.10+. Only the run step needs a package, pinned in `requirements.txt` (`pip install -r requirements.txt`, which installs `anthropic==2.4.0`), and an Anthropic API key (or `ant auth login`).

Run `--smoke` first; replace `claude-opus-5-5` with the model ID it confirms.

```bash
python freeze.py
```

```bash
python runs/run_prompts.py --smoke --model claude-opus-5-5
```

```bash
python runs/run_prompts.py --prompts prompts/practice.csv --out-dir runs/practice
```

```bash
python runs/run_prompts.py --prompts prompts/prompts.csv --model claude-opus-5-5 --out-dir runs/main
```

```bash
python ratings/make_rater_sheets.py --transcripts runs/main/transcripts.jsonl --prompts prompts/prompts.csv --out-dir ratings --key ratings/private/key.csv
```

```bash
python analysis/agreement.py ratings/rater_a.csv ratings/rater_b.csv --out analysis/agreement.csv
```

Useful flags:
- **`--smoke`** sends one harmless message to confirm the model ID and settings are accepted.
- **`--dry-run`** tests the pipeline without calling the API.
- **`--resume`** continues a crashed run without redoing finished prompts.

`run_config.json` records `prompts_sha256` and whether it matched the freeze manifest.

## Checking reproducibility

**1. Do the numbers recompute?** (anyone, no API key)

```bash
python reproduce.py
```

It checks the frozen files against the manifest, validates the prompts, confirms the run used the frozen prompt file, and reruns the agreement and results scripts against the committed outputs. It prints 9 checks and exits non-zero on any mismatch. To recompute κ by hand instead, open `analysis/agreement.xlsx`: every statistic is a live formula over the raw scores.

**2. Would a new run score the same?** (needs an API key; not done yet) Replies aren't word-for-word repeatable, because sampling can't be fixed on this model. To test it:
- Rerun the frozen prompts with identical settings into a new folder (`--out-dir runs/rerun1`).
- Have the raters score a random subset blind.
- Compare score distributions with the original run, and compare the automatic features (`analysis/transcript_features.py`), such as how often ambiguous replies lead with a crisis line.

**3. Would the raters score the same again?** (not done yet) Test–retest: each rater re-scores a random 15 transcripts, re-shuffled, after a two-week gap. Report agreement with their own earlier scores next to the inter-rater figures.

## Limitations (summary)

Full list in [`rubric/rubric.md`](rubric/rubric.md#limitations-to-carry-into-the-write-up).

- 10 prompts per category and one sample each. Breakdowns are descriptive, intervals are wide, and percent agreement is reported next to every κ.
- The prompts are synthetic and may differ from how people in crisis actually write.
- Only one prompt (E10) is in Spanish, so it's reported as an anecdote, not a result about Spanish-language responses.
- No system prompt and no product safeguards (banner, classifier), so this doesn't measure Claude.ai as users see it.
- The 988 standards are for trained crisis counselors; the rubric adapts them to a general assistant. The safe-messaging sources were written for media.
- Every means prompt is also imminent-tier, so means and intent can't be separated. Self-harm without suicidal intent appears in only two prompts (E09, T09), and research and fiction framings aren't covered.
- D6 (means inquiry) tests a crisis-line practice Anthropic's documents don't address. It's exploratory, so a low score is not a policy violation.

## AI-use statement

I wrote the research question, the prompt categories, the tagging and tier rules, the D6 means-inquiry item, and the prompt safety rules. Claude drafted the first versions of the rubric anchors and the Python scripts.

After an outside critical review, I made these changes:
- I aligned the D6 trigger across the rubric, tag scheme and validator.
- I started D6 only once both a desire signal and an intent or means signal appear.
- I added a D5 table of matched responses at each tier.
- I rewrote the means anchors so no anchor names a type or place.
- I made method-word matches warnings instead of errors.
- I moved to a fingerprint-first freeze.
- I removed rubric examples that matched scored prompts.

I checked every prompt for safety, checked every anchor against the 988 and SAVE sources, and ran the scripts myself. The ratings are done by people, not AI. The model under test runs with no system prompt and none of this project's context.

## License

This repo uses two licenses. GitHub's sidebar badge shows only the first.

| Covers | License | File |
|---|---|---|
| Code: `prompts/validate_prompts.py`, `runs/*.py`, `ratings/*.py`, `analysis/*.py`, `freeze.py` | MIT | [`LICENSE`](LICENSE) |
| Content: `prompts/*.csv`, `prompts/tag_scheme.md`, `rubric/`, `sources/`, `freeze/`, docs | CC BY 4.0 | [`LICENSE-CONTENT`](LICENSE-CONTENT) |

**Third-party material** (988 Lifeline, SAVE, Anthropic and other cited sources) is quoted briefly for citation and isn't covered by either license. **Model transcripts** (`runs/`) aren't covered either. Their terms will be checked against Anthropic's terms for model outputs before they're published.
