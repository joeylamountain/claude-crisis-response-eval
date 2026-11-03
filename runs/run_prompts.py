"""Send the frozen prompts to one Claude model and save raw transcripts.

What the model sees: ONLY the user turns from `prompt_text`. No system prompt,
no tags, no expected answers, no notes. Multi-turn scripts are sent one turn at a
time, with the model's own replies kept in the history.

Outputs (in --out-dir):
  run_config.json     model ID, dates, every setting, SDK version, and the
                      SHA-256 of the prompts file (checked against freeze/manifest.json)
  transcripts.jsonl   one line per prompt: id, every user turn and model reply,
                      stop reasons, refusal details, token usage

Usage:
  python runs/run_prompts.py --smoke --model claude-opus-5-5
        one harmless non-eval message ("Reply with the word OK."); confirms the
        model ID and request settings are accepted. Writes nothing.
  python runs/run_prompts.py --prompts prompts/practice.csv --out-dir runs/practice
  python runs/run_prompts.py --prompts prompts/prompts.csv --out-dir runs/main
  python runs/run_prompts.py ... --resume      continue a crashed run (skips finished ids)
  python runs/run_prompts.py ... --dry-run     no API calls; fake replies, for testing

Before a real run, the prompts file must match its fingerprint in
freeze/manifest.json; otherwise the script stops (override: --allow-unfrozen,
which is recorded in run_config.json).

Request settings (checked against Anthropic's SDK docs, 2026-11-03; run --smoke to confirm):
  - model: default claude-opus-5-5.
  - effort: output_config={"effort": ...}; this model's default is "medium", set
    explicitly here so it's recorded.
  - thinking: always on for this model (adaptive); not configurable, not saved.
  - temperature / top_p: not sent. Current models reject non-default sampling
    parameters, so each prompt gets one sample at API defaults.
  - No refusal fallback: a refusal is recorded as the result; the run never
    switches to another model.

Requires: pip install anthropic   (and an API key or `ant auth login`)
"""

import argparse
import csv
import datetime as dt
import hashlib
import json
import os
import sys

TURN_SEP = "||"
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MANIFEST = os.path.join(ROOT, "freeze", "manifest.json")


def now():
    return dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds")


def sha256(path):
    with open(path, "rb") as f:
        return hashlib.sha256(f.read()).hexdigest()


def frozen_digest(prompts_path):
    """The manifest's fingerprint for this prompts file, or None if not in a manifest."""
    if not os.path.exists(MANIFEST):
        return None
    rel = os.path.relpath(os.path.abspath(prompts_path), ROOT).replace(os.sep, "/")
    with open(MANIFEST, encoding="utf-8") as f:
        return json.load(f)["files"].get(rel)


def load_prompts(path):
    with open(path, newline="", encoding="utf-8-sig") as f:
        rows = list(csv.DictReader(f))
    out = []
    for r in rows:
        text = r.get("prompt_text") or r.get("text") or ""
        turns = [t.strip() for t in text.split(TURN_SEP) if t.strip()]
        out.append({"id": r["id"], "turns": turns})  # nothing else leaves this file
    return out


def text_of(message):
    """Visible reply text. Thinking blocks are not shown to raters."""
    return "".join(b.text for b in message.content if getattr(b, "type", "") == "text")


def create(client, model, effort, max_tokens, messages):
    return client.messages.create(
        model=model,
        max_tokens=max_tokens,
        output_config={"effort": effort},
        messages=messages,  # no `system` argument: no system prompt
    )


def run_one(client, args, item):
    history, record_turns = [], []
    for i, user_text in enumerate(item["turns"], start=1):
        history.append({"role": "user", "content": user_text})
        if args.dry_run:
            reply, stop, details, usage, resp_model, resp_id = (
                f"[dry-run reply to turn {i}]", "end_turn", None, {}, args.model, None)
            history.append({"role": "assistant", "content": reply})
        else:
            msg = create(client, args.model, args.effort, args.max_tokens, history)
            reply = text_of(msg)
            stop = msg.stop_reason
            details = None
            if stop == "refusal" and getattr(msg, "stop_details", None):
                details = {"category": msg.stop_details.category,
                           "explanation": msg.stop_details.explanation}
            usage = msg.usage.model_dump() if msg.usage else {}
            resp_model, resp_id = msg.model, msg.id
            # Append the full content (including thinking blocks) unchanged, as the
            # API requires for multi-turn conversations on current models.
            history.append({"role": "assistant", "content": msg.content})
        record_turns.append({
            "turn": i, "user": user_text, "assistant": reply,
            "stop_reason": stop, "refusal": details, "usage": usage,
            "response_model": resp_model, "response_id": resp_id,
        })
        if stop == "refusal":
            break  # record the refusal and stop this conversation
    return {"id": item["id"], "n_turns_planned": len(item["turns"]), "turns": record_turns}


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--prompts")
    ap.add_argument("--model", default="claude-opus-5-5")
    ap.add_argument("--effort", default="medium", choices=["low", "medium", "high", "xhigh", "max"])
    ap.add_argument("--max-tokens", type=int, default=16000)
    ap.add_argument("--out-dir", default="runs/main")
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--resume", action="store_true")
    ap.add_argument("--smoke", action="store_true")
    ap.add_argument("--allow-unfrozen", action="store_true")
    args = ap.parse_args()

    def make_client():
        import anthropic
        return anthropic.Anthropic(max_retries=5), anthropic.__version__

    if args.smoke:
        client, _ = make_client()
        msg = create(client, args.model, args.effort, 64,
                     [{"role": "user", "content": "Reply with the word OK."}])
        print(f"smoke test OK: model={msg.model} stop_reason={msg.stop_reason} text={text_of(msg)!r}")
        return
    if not args.prompts:
        sys.exit("--prompts is required (or use --smoke)")

    # Freeze check comes first, so a changed file fails before anything else happens.
    digest = sha256(args.prompts)
    expected = frozen_digest(args.prompts)
    frozen_ok = expected is not None and expected == digest
    if not frozen_ok and not (args.dry_run or args.allow_unfrozen):
        why = "no freeze/manifest.json entry" if expected is None else "file changed since the freeze"
        sys.exit(f"{args.prompts}: {why}. Run `python freeze.py` first, or pass --allow-unfrozen.")

    client, sdk_version = (None, "n/a (dry run)") if args.dry_run else make_client()

    os.makedirs(args.out_dir, exist_ok=True)
    out_path = os.path.join(args.out_dir, "transcripts.jsonl")
    cfg_path = os.path.join(args.out_dir, "run_config.json")
    done = set()
    if os.path.exists(out_path):
        if not args.resume:
            sys.exit(f"{out_path} exists. Use --resume to continue it, or a new --out-dir.")
        with open(cfg_path, encoding="utf-8") as f:
            config = json.load(f)
        for key, val in [("model", args.model), ("effort", args.effort), ("prompts_sha256", digest)]:
            if config.get(key) != val:
                sys.exit(f"--resume refused: {key} differs from the original run ({config.get(key)} vs {val}).")
        with open(out_path, encoding="utf-8-sig") as f:  # tolerate a BOM from Windows editors
            done = {json.loads(line)["id"] for line in f if line.strip()}
        config.setdefault("resumed_utc", []).append(now())
    else:
        config = {
            "started_utc": now(),
            "model": args.model,
            "system_prompt": None,
            "effort": args.effort,
            "thinking": "adaptive (always on for this model; thinking text not saved or shown to raters)",
            "max_tokens": args.max_tokens,
            "sampling": "API defaults (no temperature/top_p sent); one sample per prompt",
            "refusal_fallback": "none (refusals recorded as results)",
            "prompts_file": args.prompts.replace(os.sep, "/"),
            "prompts_sha256": digest,
            "matches_freeze_manifest": frozen_ok,
            "allow_unfrozen": args.allow_unfrozen,
            "anthropic_sdk_version": sdk_version,
            "dry_run": args.dry_run,
        }

    items = load_prompts(args.prompts)
    config["n_prompts"] = len(items)
    with open(cfg_path, "w", encoding="utf-8") as f:
        json.dump(config, f, indent=2)

    with open(out_path, "a", encoding="utf-8") as f:
        for n, item in enumerate(items, 1):
            if item["id"] in done:
                continue
            rec = run_one(client, args, item)
            f.write(json.dumps(rec, ensure_ascii=False) + "\n")
            f.flush()  # each finished prompt is saved immediately, so --resume loses nothing
            print(f"[{n}/{len(items)}] {item['id']}: {rec['turns'][-1]['stop_reason']}")

    config["finished_utc"] = now()
    with open(cfg_path, "w", encoding="utf-8") as f:
        json.dump(config, f, indent=2)
    print(f"wrote {out_path}")


if __name__ == "__main__":
    main()
