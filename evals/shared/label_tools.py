#!/usr/bin/env python3
"""Label a blind sample of your preference pairs, then compare your labels with Claude's (Step 6).

  sample  draws --n pairs (15 by default) from each of training/pairs-succinct.jsonl and
          training/pairs-persona.jsonl, puts Claude's chosen answer on side A or side B at
          random, and writes training/label-sample.jsonl, one pair per line: "id", "model",
          "prompt", "A", "B". Which side holds Claude's chosen answer (the key) goes to
          training/label-key.json, with the seed that drew the sample, so running sample again
          with that --seed draws the same sample. It will not replace an earlier sample, key or
          labels unless you add --force.
  score   reads your labels in training/labels.jsonl, one line per sampled pair: "id", "model",
          "pick" ("A" or "B") and "reason". Prints, for each model, how many of your picks
          matched Claude's chosen answer, then every pair where they did not, with its prompt
          and the first 200 characters of both answers.

Do not open training/label-key.json until training/labels.jsonl holds a label for every pair in
the sample. Seeing the key first would turn your labels into a copy of Claude's. `score` reads
the key for you, and only once every pair is labeled.

Usage, from the repo root:
  python3 evals/shared/label_tools.py sample
  python3 evals/shared/label_tools.py score

Standard library only: nothing to install.
"""
import argparse
import datetime as dt
import json
import os
import random
import shutil
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(os.path.dirname(HERE))
TRAINING = os.path.join(REPO, "training")
MODELS = ("succinct", "persona")
KEY_FORMAT = "label_tools key 1"
PREVIEW = 200


def die(message):
    print(f"error: {message}", file=sys.stderr)
    raise SystemExit(2)


def paths(folder):
    return {"sample": os.path.join(folder, "label-sample.jsonl"),
            "key": os.path.join(folder, "label-key.json"),
            "labels": os.path.join(folder, "labels.jsonl"),
            **{m: os.path.join(folder, f"pairs-{m}.jsonl") for m in MODELS}}


def show(path):
    """The path as typed from the current folder, or in full if it is somewhere else."""
    rel = os.path.relpath(path)
    return path if rel.startswith("..") else rel


def read_jsonl(path, missing_hint):
    if not os.path.exists(path):
        die(f"{show(path)} does not exist. {missing_hint}")
    rows = []
    with open(path, encoding="utf-8") as f:
        for n, line in enumerate(f, 1):
            if not line.strip():
                continue
            try:
                row = json.loads(line)
            except json.JSONDecodeError as e:
                die(f"{show(path)} line {n} is not valid JSON ({e.msg}).")
            if not isinstance(row, dict):
                die(f"{show(path)} line {n} should be a JSON object {{...}}.")
            rows.append((n, row))
    return rows


def load_pairs(path):
    pairs, seen = [], set()
    hint = "Build the preference data first (Step 5, the build-preferences skill)."
    for n, row in read_jsonl(path, hint):
        for field in ("id", "prompt", "chosen", "rejected"):
            if not isinstance(row.get(field), str) or not row[field].strip():
                die(f"{show(path)} line {n} has no \"{field}\" text.")
        if row["id"] in seen:
            die(f"{show(path)} line {n}: the id {row['id']} appears twice.")
        if row["chosen"].strip() == row["rejected"].strip():
            die(f"{show(path)} line {n} ({row['id']}): chosen and rejected are the same answer. "
                f"Run python3 evals/shared/validate.py --train and fix the pairs first.")
        seen.add(row["id"])
        pairs.append(row)
    return pairs


def cmd_sample(args):
    p = paths(args.dir)
    pairs = {m: load_pairs(p[m]) for m in MODELS}
    old = [p[k] for k in ("sample", "key", "labels") if os.path.exists(p[k])]
    if old and not args.force:
        die(f"{', '.join(show(x) for x in old)} already exist. A new sample would not match "
            f"labels made from the old one. To draw a new sample anyway, add --force: the old "
            f"files are moved to {show(args.dir)}/replaced-<date-time>/, not deleted.")
    for m in MODELS:
        if len(pairs[m]) < args.n:
            die(f"{show(p[m])} has {len(pairs[m])} pairs, fewer than --n {args.n}.")
    if old:
        keep = os.path.join(args.dir, "replaced-" + dt.datetime.now().strftime("%Y%m%d-%H%M%S"))
        os.makedirs(keep)
        for x in old:
            shutil.move(x, os.path.join(keep, os.path.basename(x)))
        print(f"Moved the old {', '.join(os.path.basename(x) for x in old)} to {show(keep)}/")

    seed = args.seed if args.seed is not None else random.SystemRandom().randrange(1, 10 ** 6)
    rng = random.Random(seed)
    rows, key, used = [], [], set()
    for m in MODELS:
        fresh = [r for r in pairs[m] if r["id"] not in used]    # a prompt once, if possible
        picked = rng.sample(fresh if len(fresh) >= args.n else pairs[m], args.n)
        sides = ["A", "B"] * (args.n // 2) + [rng.choice("AB")] * (args.n % 2)
        rng.shuffle(sides)                                      # half A, half B
        for r, side in zip(picked, sides):
            a, b = (r["chosen"], r["rejected"]) if side == "A" else (r["rejected"], r["chosen"])
            rows.append({"id": r["id"], "model": m, "prompt": r["prompt"], "A": a, "B": b})
            key.append({"id": r["id"], "model": m, "chosen_side": side})
            used.add(r["id"])
    with open(p["sample"], "w", encoding="utf-8") as f:
        for row in rows:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")
    with open(p["key"], "w", encoding="utf-8") as f:
        json.dump({"format": KEY_FORMAT,
                   "note": "Do not open this file until labels.jsonl has a label for every pair "
                           "in label-sample.jsonl.",
                   "seed": seed, "n": args.n,
                   "made_at": dt.datetime.now().isoformat(timespec="seconds"),
                   "pairs_rows": {m: len(pairs[m]) for m in MODELS}, "key": key}, f, indent=1)
    print(f"Wrote {len(rows)} pairs ({args.n} succinct, then {args.n} persona) to "
          f"{show(p['sample'])}.")
    print(f"The key is in {show(p['key'])}. Don't open it until {show(p['labels'])} has a label "
          f"for every pair.")
    print('Show each pair word for word, record each pick in labels.jsonl as {"id", "model", '
          '"pick": "A" or "B", "reason"}, then run: python3 evals/shared/label_tools.py score')


def preview(text):
    text = " ".join(text.split())
    return text if len(text) <= PREVIEW else text[:PREVIEW] + "..."


def cmd_score(args):
    p = paths(args.dir)
    if not os.path.exists(p["key"]):
        die(f"{show(p['key'])} does not exist. Run python3 evals/shared/label_tools.py sample "
            f"first.")
    sample = {(r["model"], r["id"]): r for _, r in read_jsonl(
        p["sample"], "Run python3 evals/shared/label_tools.py sample first.")}
    labels = {}
    hint = ('Write one line per sampled pair: {"id": ..., "model": ..., "pick": "A" or "B", '
            '"reason": ...}, then run score again.')
    for n, row in read_jsonl(p["labels"], hint):
        where = f"{show(p['labels'])} line {n}"
        k = (row.get("model"), row.get("id"))
        if not all(isinstance(x, str) for x in k):
            die(f"{where} needs an \"id\" and a \"model\", copied from the sample.")
        if k not in sample:
            die(f"{where}: {k[0]} {k[1]} is not a pair in {show(p['sample'])}. Copy the "
                f"\"id\" and \"model\" from the sample exactly.")
        pick = str(row.get("pick", "")).strip().upper()
        if pick not in ("A", "B"):
            die(f"{where}: \"pick\" must be \"A\" or \"B\", not {json.dumps(row.get('pick'))}.")
        if k in labels:
            die(f"{where}: {k[0]} {k[1]} is labeled twice. Keep one of the two lines.")
        labels[k] = {"pick": pick, "reason": str(row.get("reason") or "").strip()}
    missing = [k for k in sample if k not in labels]
    if missing:
        die(f"{len(missing)} of the {len(sample)} sampled pairs have no label yet: "
            f"{', '.join(f'{m} {i}' for m, i in missing)}. Label every pair before scoring; "
            f"the key stays closed until then.")
    with open(p["key"], encoding="utf-8") as f:
        key = {(r["model"], r["id"]): r["chosen_side"] for r in json.load(f)["key"]}
    if set(key) != set(sample):
        die(f"{show(p['key'])} does not match {show(p['sample'])}. Draw a new sample with "
            f"sample --force.")

    print("How many of your picks matched Claude's chosen answer:")
    width = max(len(m) for m in MODELS) + 1
    disagree, total = [], 0
    for m in MODELS:
        ks = [k for k in sample if k[0] == m]
        same = sum(labels[k]["pick"] == key[k] for k in ks)
        total += same
        disagree += [k for k in ks if labels[k]["pick"] != key[k]]
        if ks:
            print(f"  {m + ':':{width}} {same} of {len(ks)} ({100 * same / len(ks):.0f}%)")
    print(f"  {'all:':{width}} {total} of {len(sample)} ({100 * total / len(sample):.0f}%)")
    if not disagree:
        print("\nNo disagreements: you picked Claude's chosen answer on every pair.")
        return
    print(f"\nThe {len(disagree)} pairs where you picked the rejected answer:")
    for n, k in enumerate(disagree, 1):
        row, chosen = sample[k], key[k]
        prompt = row["prompt"].strip()
        if prompt.startswith("Question:") and prompt.endswith("Answer:"):
            prompt = prompt[len("Question:"):-len("Answer:")].strip()
        print(f"\n[{n}] {k[0]} {k[1]}: you picked {labels[k]['pick']}, Claude's chosen answer "
              f"is {chosen}")
        print(f"  Prompt: {' '.join(prompt.split())}")
        for side in ("A", "B"):
            who = "Claude's chosen" if side == chosen else "rejected"
            print(f"  {side} ({who}): {preview(row[side])}")
        print(f"  Your reason: {labels[k]['reason'] or '(none given)'}")


def build_parser():
    ap = argparse.ArgumentParser(
        prog="label_tools.py", description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="command", required=True)
    for name, func, text in (
            ("sample", cmd_sample, "draw the pairs to label blind and write the key "
                                   "(don't open training/label-key.json until the labels "
                                   "are written)"),
            ("score", cmd_score, "compare training/labels.jsonl with the key")):
        p = sub.add_parser(name, help=text, description=text)
        p.add_argument("--dir", default=TRAINING,
                       help="the training folder (default: training/ in the repo root)")
        p.set_defaults(func=func)
        if name == "sample":
            p.add_argument("--n", type=int, default=15, help="pairs per model (default 15)")
            p.add_argument("--seed", type=int,
                           help="seed for the draw (default: a new random one, saved in the "
                                "key, so the same seed redraws the same sample)")
            p.add_argument("--force", action="store_true",
                           help="replace an earlier sample, key and labels (they are moved to "
                                "training/replaced-<date-time>/)")
    return ap


def main(argv=None):
    args = build_parser().parse_args(argv)
    if getattr(args, "n", 1) < 1:
        die("--n must be at least 1.")
    args.func(args)
    return 0


if __name__ == "__main__":
    sys.exit(main())
