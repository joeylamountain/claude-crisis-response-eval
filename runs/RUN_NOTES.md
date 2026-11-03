# Run notes: how responses are collected

## Chosen path: the Python script (API, no system prompt)

**What's tested:** the raw model through the Anthropic API. This is **not** Claude.ai. Claude.ai adds Anthropic's system prompt and can show a crisis banner, so results here are a lower bound on what Claude.ai users see.

**Why not the alternatives:**

| Path | Why not chosen |
|---|---|
| Console Workbench | Works, but it's manual: 80+ copy-pastes, including multi-turn histories, invite errors. It also can't apply the planned temperature setting, because current models reject temperature changes, so it would add no control the script lacks. |
| Claude.ai | Tests the product (system prompt, banner, memory), not the model. The responses also depend on account settings that can't be recorded. |
| **Script** (`runs/run_prompts.py`) | Sends exactly the frozen prompt text, records model, date, settings and the prompt file's fingerprint automatically, handles multi-turn histories, and can resume a crash. |

## Settings (identical for pilot, practice and main runs)

| Setting | Value | Note |
|---|---|---|
| Model | `claude-opus-5-5` | Confirm with `--smoke`. Record the `model` the API reports, which is copied into every row. |
| System prompt | none | Matches Anthropic's published eval setup |
| Effort | `medium` | This model's default, set explicitly so it's recorded |
| Thinking | adaptive (always on for this model) | Thinking text isn't saved or shown to raters |
| Sampling | API defaults; temperature/top_p not sent | Current models reject non-default sampling. One sample per prompt. |
| max_tokens | 16000 | |
| Refusals | recorded as results; no fallback model | The `notes` column shows `stop_reason=refusal` and the category |
| SDK | `anthropic` 2.4.0 | Pinned in `requirements.txt`: `pip install -r requirements.txt` |

## Dry run: 5 pilot prompts (`prompts/pilot.csv`)

These five are **not** in the main or practice sets. A check on 2026-11-03 found no shared IDs and no identical turns; the closest pair was PL5 and PR10 at 0.72 similarity, and only their opening "help me plan…" request is alike. `pilot.csv` was added **after** the `v1-freeze` release and committed to GitHub **before** it was run (see CHANGELOG).

**The pilot only checks the pipeline. It is never scored:**
- Its output lives only in `runs/pilot/`.
- It is never passed to `make_rater_sheets.py` or `agreement.py`, and never counted in headline numbers.
- It is **not used for calibration.** PL2–PL4 reuse public rubric anchor sketches, so a rater would already know their anchors. Calibration uses `prompts/practice.csv` only.

| id | Category | What it checks in the process |
|---|---|---|
| PL1 | explicit ideation | Basic single-turn call |
| PL2 | third party | Helper framing |
| PL3 | ambiguous | Short prompt |
| PL4 | control | A no-crisis reply is captured normally |
| PL5 | multi-turn (3 turns) | Model replies are carried into the next turn; one CSV row per turn |

**Status:** plumbing verified on 2026-11-03 with `--dry-run` (no API call). All 5 prompts produced 7 rows with model, date and settings. The live pilot is next.

## Actual run order (all times UTC, 2026-11-03)

| When | What | Source |
|---|---|---|
| 17:04:44 | `v1-freeze` release published (freeze date) | GitHub release `published_at` |
| 17:14:00–17:15:42 | **Practice run**, 10 prompts. `matches_freeze_manifest: true`, SDK 2.4.0. Not scored (calibration only). | `runs/practice/run_config.json` |
| *(after the pilot commit)* | **Pilot run**, 5 prompts, pipeline check only | `runs/pilot/run_config.json` |
| *(later)* | Main run, 70 prompts | `runs/main/run_config.json` |

The practice run happened **before** the pilot. That's fine, because neither is scored, but the order is recorded as it actually happened.

## Exact steps

Set your key in **your own** terminal (never paste it into chat or a file in this repo):

```bash
$env:ANTHROPIC_API_KEY = "sk-ant-..."
```

Check that the model ID and settings are accepted (one harmless message, no eval prompt):

```bash
python runs/run_prompts.py --smoke --model claude-opus-5-5
```

Run the pilot. `--allow-unfrozen` is needed because the pilot isn't part of the freeze; the flag is recorded in `run_config.json`.

```bash
python runs/run_prompts.py --prompts prompts/pilot.csv --out-dir runs/pilot --allow-unfrozen
```

Export to the collection sheet:

```bash
python runs/export_csv.py --run-dir runs/pilot --prompts prompts/pilot.csv --out runs/pilot/dryrun.csv
```

Then open `runs/pilot/dryrun.csv` in Google Sheets. Columns: `id, category, turn, prompt_text, response_text, model, date, settings, notes`.

## Checklist after the live pilot

- [ ] 7 rows (5 prompts; PL5 has 3 turns), none with an empty `response_text`
- [ ] `model` in every row matches the `--smoke` output
- [ ] `runs/pilot/run_config.json` shows `system_prompt: null`, effort, SDK version, `prompts_sha256`
- [ ] PL5 turn 3 reads as a reply to the whole conversation, not to turn 3 alone
- [ ] Note anything confusing here and fix it **before** `freeze.py` and the main run

## Repeating a run exactly

Same `prompts_sha256`, same model ID, same effort and max_tokens, same SDK version. Responses won't be word-for-word identical, because sampling isn't fixed. "Exactly repeatable" here means the same inputs and settings, not the same outputs. That's one reason each prompt is a single sample and the write-up reports it as such.

## Gotchas

- `date` in the CSV is the run's start time (UTC), shared by every row in the run. Per-reply response IDs are in `transcripts.jsonl`.
- The pilot, practice and main runs each go in their own `--out-dir`. The script refuses to overwrite an existing run; use `--resume` to continue one.
- Transcripts may contain crisis-related text. Their license status is still to be checked (see README).
