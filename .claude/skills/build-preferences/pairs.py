#!/usr/bin/env python3
"""Build the preference pairs for Part 2 Step 5. Used by the build-preferences skill.

Claude's answer-writer subagents write the answers; this script does everything around them.
Run it from the repository's folder. Standard library only: nothing to install.

  plan    copies the constitution for one model (Core, that model's style, the conflict rule,
          and for the persona the voice samples) into training/.batches/<model>/, splits
          training/prompts-300.jsonl into batches, and prints the lines to give each
          answer-writer. Run it again to carry on: finished batches are kept.
  status  shows which batches have answers, and the lines for the ones that still need a writer.
  show    prints a few answers from one batch, word for word, with their questions.
  merge   checks the answers (every prompt answered once, none empty, none copied from the
          human answer), writes redo batches for any gaps, and when nothing is missing writes
          training/pairs-<model>.jsonl. It also prints a variety check: openings, endings and
          phrases that many answers share.

Example:
  python3 .claude/skills/build-preferences/pairs.py plan --model succinct
  ... one answer-writer subagent per batch ...
  python3 .claude/skills/build-preferences/pairs.py merge --model succinct
"""
from __future__ import annotations

import argparse
import collections
import glob
import hashlib
import json
import os
import random
import re
import shutil
import sys

MODELS = {"succinct": "Succinct style", "persona": "Persona style"}
CONSTITUTIONS = "constitutions.md"
VOICE_SAMPLES = "voice-samples.md"
PROMPTS = os.path.join("training", "prompts-300.jsonl")
BATCH_ROOT = os.path.join("training", ".batches")
MAX_REDO_ROUNDS = 2
COPY_RUN = 12      # this many words in a row shared with the human answer counts as copied
LONG_WORDS = 150   # answers longer than this are reported


def die(msg):
    print(f"error: {msg}", file=sys.stderr)
    sys.exit(1)


def read_jsonl(path):
    rows, bad = [], 0
    with open(path, encoding="utf-8") as f:
        for line in f:
            if not line.strip():
                continue
            try:
                rows.append(json.loads(line))
            except json.JSONDecodeError:
                bad += 1
    return rows, bad


def write_jsonl(path, rows):
    with open(path, "w", encoding="utf-8") as f:
        for r in rows:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")


def sha256(text):
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def words(text):
    """Lowercase words, letters only: list numbers and punctuation don't count."""
    return re.findall(r"[^\W\d_]+", text.lower())


# ---------- the constitution ----------

def sections(path):
    """Map each '## ' heading of a Markdown file to its text, with HTML comments removed."""
    with open(path, encoding="utf-8") as f:
        text = re.sub(r"<!--.*?-->", "", f.read(), flags=re.S)
    out, name = {}, None
    for line in text.splitlines():
        if line.startswith("## "):
            name = line[3:].strip()
            out[name] = []
        elif name is not None:
            out[name].append(line)
    return {k: "\n".join(v).strip() for k, v in out.items()}, text


def unfilled(text):
    return not text.strip() or "XXXX" in text


def build_constitution(model):
    """The text one model's writers follow: Core, its style, the conflict rule (and samples)."""
    if not os.path.isfile(CONSTITUTIONS):
        die(f"{CONSTITUTIONS} not found. Run this from the repository's folder.")
    secs, _ = sections(CONSTITUTIONS)
    parts = ["# The constitution for these answers", ""]
    for name in ("Core", MODELS[model], "When they conflict"):
        if name not in secs:
            die(f"{CONSTITUTIONS} has no '## {name}' section.")
        if unfilled(secs[name]):
            die(f"the '## {name}' section of {CONSTITUTIONS} is not filled in yet (Step 2).")
        parts += [f"## {name}", "", secs[name], ""]
    if model == "persona":
        if not os.path.isfile(VOICE_SAMPLES):
            die(f"{VOICE_SAMPLES} not found (Step 1).")
        _, text = sections(VOICE_SAMPLES)
        body = re.sub(r"^# .*$", "", text, flags=re.M).strip()
        body = re.sub(r"^## ", "### ", body, flags=re.M)
        if unfilled(body):
            die(f"{VOICE_SAMPLES} is not filled in yet (Step 1).")
        parts += ["## Voice samples", "",
                  "The person's own words, to show how they sound. Never copy a sentence or a "
                  "distinctive phrase from them into an answer.", "", body, ""]
    return "\n".join(parts)


# ---------- batches ----------

def model_dir(model):
    return os.path.join(BATCH_ROOT, model)


def load_prompts():
    if not os.path.isfile(PROMPTS):
        die(f"{PROMPTS} not found. Run this from the repository's folder.")
    rows, bad = read_jsonl(PROMPTS)
    if bad:
        die(f"{PROMPTS} has {bad} lines that are not valid JSON.")
    for r in rows:
        for field in ("id", "question", "prompt", "human"):
            if not isinstance(r.get(field), str) or not r[field].strip():
                die(f"{PROMPTS}: a line has no '{field}' ({r.get('id', 'no id')}).")
    ids = [r["id"] for r in rows]
    if len(set(ids)) != len(ids):
        die(f"{PROMPTS} lists an id twice.")
    return rows


def writer_lines(d, inp, out):
    return (f"Constitution: {os.path.join(d, 'constitution.md')}\n"
            f"Input batch: {inp}\nOutput file: {out}")


def batch_state(batch, answers_ok):
    if not os.path.isfile(batch["output"]):
        return "missing"
    done = sum(i in answers_ok for i in batch["ids"])
    return "complete" if done == len(batch["ids"]) else f"partial ({done} of {len(batch['ids'])})"


def cmd_plan(args):
    d = model_dir(args.model)
    prompts = load_prompts()
    constitution = build_constitution(args.model)
    key = {"constitution_sha256": sha256(constitution),
           "prompts_sha256": sha256(json.dumps(prompts, sort_keys=True)), "size": args.size}
    plan_path = os.path.join(d, "plan.json")
    if os.path.isfile(plan_path) and not args.restart:
        with open(plan_path, encoding="utf-8") as f:
            plan = json.load(f)
        if all(plan.get(k) == v for k, v in key.items()):
            print("Already planned; finished batches are kept.")
            return cmd_status(args)
        what = ("the constitution" if plan.get("constitution_sha256") !=
                key["constitution_sha256"] else "the prompts or the batch size")
        die(f"{what} changed since the {args.model} batches in {d} were written. To start "
            f"the {args.model} answers over, run plan again with --restart (it deletes them).")
    if os.path.isdir(d):
        shutil.rmtree(d)
    os.makedirs(d)
    with open(os.path.join(BATCH_ROOT, ".gitignore"), "w", encoding="utf-8") as f:
        f.write("# Working files of the build-preferences skill; not committed.\n*\n")
    with open(os.path.join(d, "constitution.md"), "w", encoding="utf-8") as f:
        f.write(constitution)
    batches = []
    for n, start in enumerate(range(0, len(prompts), args.size), 1):
        chunk = prompts[start:start + args.size]
        inp, out = os.path.join(d, f"in-{n:02d}.jsonl"), os.path.join(d, f"out-{n:02d}.jsonl")
        write_jsonl(inp, [{"id": r["id"], "question": r["question"], "human": r["human"]}
                          for r in chunk])
        batches.append({"n": n, "input": inp, "output": out, "ids": [r["id"] for r in chunk]})
    plan = dict(key, model=args.model, prompts=len(prompts), batches=batches, redo_round=0)
    with open(plan_path, "w", encoding="utf-8") as f:
        json.dump(plan, f, indent=1)
    print(f"Planned {len(prompts)} {args.model} answers in {len(batches)} batches of up to "
          f"{args.size}, under {os.path.join(d, 'constitution.md')}.")
    return cmd_status(args)


def load_plan(model):
    path = os.path.join(model_dir(model), "plan.json")
    if not os.path.isfile(path):
        die(f"no {model} batches yet. Run: python3 {sys.argv[0]} plan --model {model}")
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def collect(model, plan, prompts):
    """Every valid answer, by id, from the batch outputs and then the redo outputs."""
    human = {r["id"]: r["human"] for r in prompts}
    d = model_dir(model)
    outs = [b["output"] for b in plan["batches"]]
    outs += sorted(glob.glob(os.path.join(d, "redo-*-out.jsonl")))
    ok, problems, extra, bad_json = {}, {}, 0, 0
    for path in outs:
        if not os.path.isfile(path):
            continue
        rows, bad = read_jsonl(path)
        bad_json += bad
        for r in rows:
            i = r.get("id") if isinstance(r, dict) else None
            if i not in human or i in ok:
                extra += 1
                continue
            why = answer_problem(r.get("answer"), human[i])
            if why:
                problems[i] = why
            else:
                ok[i] = r["answer"].strip()
                problems.pop(i, None)
    return ok, problems, extra, bad_json


def answer_problem(answer, human):
    if not isinstance(answer, str) or not answer.strip():
        return "empty"
    if re.search(r"(^|\n)\s*Question:", answer):
        return "contains 'Question:'"
    a, h = words(answer), words(human)
    if a == h:
        return "the same as the human answer"
    runs = {tuple(h[k:k + COPY_RUN]) for k in range(len(h) - COPY_RUN + 1)}
    if any(tuple(a[k:k + COPY_RUN]) in runs for k in range(len(a) - COPY_RUN + 1)):
        return f"copies {COPY_RUN} or more words in a row from the human answer"
    return None


def cmd_status(args):
    plan = load_plan(args.model)
    prompts = load_prompts()
    ok, problems, _, _ = collect(args.model, plan, prompts)
    d = model_dir(args.model)
    todo = []
    print(f"{args.model}: {len(ok)} of {plan['prompts']} prompts answered.")
    for b in plan["batches"]:
        state = batch_state(b, ok)
        print(f"  batch {b['n']:02d}  {len(b['ids'])} prompts  {state}")
        if state == "missing":
            todo.append(b)
    if not todo:
        print(f"Every batch has been written (merge redoes any gaps). Next: python3 "
              f"{sys.argv[0]} merge --model {args.model}")
        return todo
    print(f"\nBatches that need an answer-writer: {len(todo)}. The prompt for each, exactly:")
    for b in todo:
        print(f"\n[batch {b['n']:02d}]\n{writer_lines(d, b['input'], b['output'])}")
    return todo


def cmd_show(args):
    plan = load_plan(args.model)
    b = next((b for b in plan["batches"] if b["n"] == args.batch), None)
    if b is None or not os.path.isfile(b["output"]):
        die(f"batch {args.batch} of {args.model} has no answers yet.")
    prompts = {r["id"]: r for r in load_prompts()}
    rows, _ = read_jsonl(b["output"])
    good = [r for r in rows if isinstance(r, dict) and r.get("id") in b["ids"]
            and not answer_problem(r.get("answer"), prompts[r["id"]]["human"])]
    for r in random.Random(args.seed).sample(good, min(args.n, len(good))):
        print(f"Question: {prompts[r['id']]['question']}\nAnswer: {r['answer'].strip()}\n")


# ---------- merge ----------

def variety(answers, n_show=8):
    """Openings, endings and four-word phrases shared by many answers, with counts."""
    n = len(answers)
    floor = max(3, round(0.05 * n))
    openers = collections.Counter(" ".join(words(a)[:3]) for a in answers if words(a))
    closers = collections.Counter(" ".join(words(a)[-3:]) for a in answers if words(a))
    phrases = collections.Counter()
    for a in answers:
        w = words(a)
        phrases.update({" ".join(w[k:k + 4]) for k in range(len(w) - 3)})
    lines = []
    for title, counter, least in (("Openings (first three words)", openers, floor),
                                  ("Endings (last three words)", closers, floor),
                                  ("Phrases (four words) in many answers", phrases,
                                   max(3, round(0.10 * n)))):
        common = [(t, c) for t, c in counter.most_common(n_show) if c >= least]
        lines.append(f"{title}, used by {least} or more of the {n} answers:")
        lines += [f"  {c:4d}  \"{t}\"" for t, c in common] or ["  none"]
    return lines


def cmd_merge(args):
    plan = load_plan(args.model)
    unwritten = [b["n"] for b in plan["batches"] if not os.path.isfile(b["output"])]
    if unwritten:
        print(f"No answers yet for batch {', '.join(f'{n:02d}' for n in unwritten)}. Run "
              f"those writers first; this lists them:\n  python3 {sys.argv[0]} status "
              f"--model {args.model}")
        sys.exit(1)
    prompts = load_prompts()
    ok, problems, extra, bad_json = collect(args.model, plan, prompts)
    d = model_dir(args.model)
    missing = [r for r in prompts if r["id"] not in ok]
    print(f"{args.model}: {len(ok)} of {len(prompts)} prompts have a usable answer.")
    if bad_json or extra:
        print(f"  Ignored: {bad_json} lines that were not valid JSON, {extra} lines with an "
              f"unknown or repeated id.")
    if problems:
        print("  Answers that can't be used:")
        for why, c in collections.Counter(problems.values()).most_common():
            print(f"    {c:4d}  {why}")
    if missing and not args.allow_gaps:
        if plan.get("redo_round", 0) >= MAX_REDO_ROUNDS:
            print(f"\nStill missing after {MAX_REDO_ROUNDS} redo rounds: "
                  f"{', '.join(r['id'] for r in missing)}\nGAPS REMAIN. To leave these prompts "
                  f"out, run merge again with --allow-gaps.")
            sys.exit(1)
        plan["redo_round"] = plan.get("redo_round", 0) + 1
        rnd = plan["redo_round"]
        print(f"\nREDO NEEDED (round {rnd} of {MAX_REDO_ROUNDS}). One answer-writer per row, "
              f"with exactly these lines, then run merge again:")
        size = len(plan["batches"][0]["ids"])
        for k, start in enumerate(range(0, len(missing), size), 1):
            chunk = missing[start:start + size]
            inp = os.path.join(d, f"redo-{rnd}-{k:02d}-in.jsonl")
            out = os.path.join(d, f"redo-{rnd}-{k:02d}-out.jsonl")
            write_jsonl(inp, [{"id": r["id"], "question": r["question"], "human": r["human"]}
                              for r in chunk])
            print(f"\n[redo {k:02d}, {len(chunk)} prompts]\n{writer_lines(d, inp, out)}")
        with open(os.path.join(d, "plan.json"), "w", encoding="utf-8") as f:
            json.dump(plan, f, indent=1)
        sys.exit(1)

    pairs = []
    for r in prompts:
        if r["id"] in ok:
            rejected = r["human"] if r["human"].startswith(" ") else " " + r["human"]
            pairs.append({"id": r["id"], "prompt": r["prompt"], "chosen": " " + ok[r["id"]],
                          "rejected": rejected})
    out_path = os.path.join("training", f"pairs-{args.model}.jsonl")
    write_jsonl(out_path, pairs)
    chosen = [p["chosen"].strip() for p in pairs]
    mean = lambda xs: sum(xs) / max(1, len(xs))
    print(f"\nWrote {out_path}: {len(pairs)} pairs"
          + (f" ({len(missing)} of the {len(prompts)} prompts left out)." if missing else "."))
    print(f"Average length: Claude's answers {mean([len(c.split()) for c in chosen]):.0f} "
          f"words, the human answers {mean([len(p['rejected'].split()) for p in pairs]):.0f}. "
          f"{sum(len(c.split()) > LONG_WORDS for c in chosen)} of Claude's answers are over "
          f"{LONG_WORDS} words.")
    print("\n".join(["", "Variety check."] + variety(chosen)))


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    sub = ap.add_subparsers(dest="cmd", required=True)
    for name, func in (("plan", cmd_plan), ("status", cmd_status), ("show", cmd_show),
                       ("merge", cmd_merge)):
        p = sub.add_parser(name)
        p.add_argument("--model", required=True, choices=sorted(MODELS))
        p.set_defaults(func=func)
        if name == "plan":
            p.add_argument("--size", type=int, default=25, help="prompts per batch (default 25)")
            p.add_argument("--restart", action="store_true",
                           help="delete this model's batches and start over")
        if name == "show":
            p.add_argument("--batch", type=int, default=1)
            p.add_argument("--n", type=int, default=3)
            p.add_argument("--seed", type=int, default=440)
        if name == "merge":
            p.add_argument("--allow-gaps", action="store_true",
                           help="write the pairs file without the prompts still missing")
    args = ap.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
