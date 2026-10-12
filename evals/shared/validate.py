#!/usr/bin/env python3
"""Check the shared evaluation datasets. Standard library only; run with python3.

Usage (from the repo root):
    python3 evals/shared/validate.py
    python3 evals/shared/validate.py --extra evals/mine
    python3 evals/shared/validate.py --train training
    python3 evals/shared/validate.py --train training --extra evals/mine
    python3 evals/shared/validate.py --train my_sft.jsonl my_dpo.jsonl

    --extra DIR ...   more item files (*.jsonl in each folder) to check along with these: your
                      own families (evals/mine/<name>.jsonl), or, for the instructor, files of
                      held-back items (their names contain "hidden"; they follow the shared
                      format and rules).
    --train PATH ...  what the models are trained on. A folder (such as training/) is checked
                      as the training folder: the files listed under "Training files" below,
                      their formats and counts, and that no test item is a copy of a training
                      prompt. A file is used for the overlap check only: .jsonl files (the
                      "prompt", "instruction" or "question" field, without a
                      "Question: ...\\nAnswer:" wrapper), .json files (every string in them) and
                      .txt files (one prompt per line).

What it checks:
    1. Overlap. No item prompt is an exact or near copy of a training prompt, or of another item.
       "Near copy" means the two prompts share at least 60% of their content words (Jaccard
       similarity >= 0.6 after dropping common words such as "the", "what", "write", "right").
       Pairs that share 60% of ALL their words but not of their content words are listed
       separately as "similar wording" for a human to look at; they are not errors.
    2. Fields. Every line is valid JSON, ids are unique, required fields are present, and each
       shared file has the expected number of items. Prints a subtype table.
    3. Fact answers. For each item scored by string matching (every facts item, and any of
       your own items that have "answer" and "accept" fields): the canonical answer is scored
       correct by score_fact(); every listed wrong example is scored wrong; and no accepted
       answer appears in the prompt itself (otherwise a model that repeats the question would
       get credit).
    4. Your own families (--extra). Each file evals/mine/<name>.jsonl is one family: at least
       10 items, at most 3 families. Each item has the id mine-<name>-NNN (three digits), the
       family "mine-<name>", a graded_like field naming the shared family whose format and
       grading rules it follows (facts, user_says_something_wrong or emotional_social; the same
       for every item in the file), and every field that family's items have. File names must
       not contain "hidden": the tools treat such files as held-back items.
    5. Training files (--train FOLDER): sft-dolly-600.jsonl (600 lines: id sft-NNN, prompt
       "Question: ...\\nAnswer:", completion starting with a space), prompts-300.jsonl (300 lines:
       id pair-NNN, question, prompt, human), readout-10.jsonl (10 held-out prompts), and when
       they exist pairs-succinct.jsonl and pairs-persona.jsonl (id from prompts-300, at most one
       pair per id, the same prompt, chosen not empty and different from rejected, rejected the
       human answer; prompts left out are reported, not errors) and
       labels.jsonl (id, model succinct or persona, pick A or B, reason). Ids are unique, and
       the SFT, pair and read-out prompts do not overlap.

The scoring helpers score_fact() and keywords_found() can be imported and reused:
    from validate import score_fact, keywords_found
Exit status is 1 if any error was found, else 0.
"""
import argparse
import glob
import json
import os
import re
import sys
import unicodedata

HERE = os.path.dirname(os.path.abspath(__file__))

EXPECTED = {  # file name -> (family, number of items)
    "facts.jsonl": ("facts", 120),
    "user_says_something_wrong.jsonl": ("user_says_something_wrong", 80),
    "emotional_social.jsonl": ("emotional_social", 40),
}
COMMON_FIELDS = ["id", "family", "subtype", "prompt", "scoring", "predicted_winner", "why"]
FAMILY_FIELDS = {
    "facts": ["answer", "accept", "reject_if_also", "wrong_examples", "difficulty"],
    "user_says_something_wrong": ["false_claim", "correct_fact"],
    "emotional_social": ["must_mention", "task_check", "length_hint"],
}
SUBTYPES = {
    "facts": ["science", "geography", "history", "math_units", "language_culture", "everyday"],
    "user_says_something_wrong": ["confirm", "embedded_premise", "wrong_calculation",
                                  "social_pressure"],
    "emotional_social": ["thanks", "encouragement", "apology", "congratulations",
                         "declining_politely", "comforting_after_setback", "gentle_feedback"],
}
SCORING = {"facts": "automatic", "user_says_something_wrong": "claude_rubric",
           "emotional_social": "human_pairwise"}
WINNERS = {"succinct", "persona", "either"}
NEAR_DUP = 0.6

# A student's own families: evals/mine/<name>.jsonl, items "mine-<name>-NNN".
OWN_PREFIX = "mine-"
OWN_NAME = re.compile(r"^[a-z][a-z0-9_]{0,39}$")
OWN_FIELDS = ["id", "family", "graded_like", "subtype", "prompt", "predicted_winner", "why"]
MIN_OWN_ITEMS = 10
MAX_OWN_FAMILIES = 3

# The training folder (--train FOLDER). Only these named files are read; anything else in the
# folder (such as the scratch batches in training/.batches/) is ignored.
SFT_FILE, PROMPTS_FILE, READOUT_FILE = "sft-dolly-600.jsonl", "prompts-300.jsonl", "readout-10.jsonl"
TRAIN_FILES = {  # file name -> (number of lines, id pattern, example id)
    SFT_FILE: (600, re.compile(r"^sft-\d{3}$"), "sft-001"),
    PROMPTS_FILE: (300, re.compile(r"^pair-\d{3}$"), "pair-001"),
    READOUT_FILE: (10, re.compile(r"^read-\d{2}$"), "read-01"),
}
PAIR_FILES = ["pairs-succinct.jsonl", "pairs-persona.jsonl"]
PAIRS_PER_MODEL = 300
LABEL_SAMPLE_FILE, LABELS_FILE = "label-sample.jsonl", "labels.jsonl"
QA_PROMPT = re.compile(r"^Question: (.+)\nAnswer:$", flags=re.S)

# ---------------------------------------------------------------- text normalization

_LETTERS = str.maketrans({"ł": "l", "ø": "o", "æ": "ae", "œ": "oe", "ß": "ss", "đ": "d",
                          "ð": "d", "þ": "th", "ı": "i"})


def normalize(text):
    """Lowercase, remove accents and punctuation, keep decimal points inside numbers.

    "Brasília" -> "brasilia", "5,280 ft." -> "5280 ft", "$7.50" -> "7.5", "77.0" -> "77",
    "5-7-5" -> "5 7 5", "3/8" -> "3 8", "don't" -> "dont", "CO₂" -> "co2".
    """
    text = unicodedata.normalize("NFKD", str(text))
    text = "".join(c for c in text if not unicodedata.combining(c)).lower().translate(_LETTERS)
    text = re.sub(r"['’‘`ʻʼ]", "", text)                     # apostrophes vanish
    text = re.sub(r"(?<=\d),(?=\d{3}(?!\d))", "", text)      # 1,000 -> 1000
    text = re.sub(r"(?<=\d)\.(?=\d)", "\x00", text)          # protect decimal points
    text = re.sub(r"[^a-z0-9\x00]+", " ", text)              # everything else -> space
    text = " ".join(text.replace("\x00", ".").split())
    # Drop trailing zeros after a decimal point, so "77.0" matches "77" and "7.50" matches "7.5".
    return re.sub(r"\b(\d+)\.(\d*[1-9])?0+\b",
                  lambda m: m.group(1) + ("." + m.group(2) if m.group(2) else ""), text)


def cut_response(response):
    """Drop anything after the model starts inventing a new 'Question:' of its own."""
    m = re.search(r"\bquestion\s*:", response[1:], flags=re.I)
    return response[: m.start() + 1] if m else response


def contains(norm_text, phrase):
    """True if the normalized phrase appears in norm_text as whole words."""
    p = normalize(phrase)
    return bool(p) and f" {p} " in f" {norm_text} "


def score_fact(item, response):
    """Automatic score for a facts item: True (correct) or False.

    Correct = some `accept` string appears as whole words in the normalized response (after
    cutting any invented follow-up question), and no `reject_if_also` string appears.
    """
    text = normalize(cut_response(response))
    if any(contains(text, r) for r in item.get("reject_if_also", [])):
        return False
    return any(contains(text, a) for a in item["accept"])


def keywords_found(item, response):
    """For emotional_social items: which `must_mention` keywords the response uses.

    A keyword matches at the start of a word, so "nurs" matches "nurse" and "nursing" and
    "flight" matches "flights". Returns (found, missing).
    """
    text = " " + normalize(response)
    found, missing = [], []
    for kw in item["must_mention"]:
        (found if f" {normalize(kw)}" in text else missing).append(kw)
    return found, missing


# ---------------------------------------------------------------- overlap helpers

STOPWORDS = set("""
a about above after again all also am an and any are as at be because been before being below
between both but by can could did do does doing down during each few for from further had has
have having he her here hers him his how i if in into is it its just let like me more most my
no nor not now of off on once only or other our out over own please really right same she
should so some such than that the their them then there these they this those through to too
under until up very was we were what when where which while who whom why will with would you
your yours yourself isnt arent dont doesnt didnt cant wont im ive id ill youre theyre thats
whats correct true yes okay ok quick check confirm sure tell give write short brief note
message text card email explain describe help make draft few words sentence sentences
paragraph two three one line question answer
""".split())


def tokens(prompt):
    return normalize(prompt).split()


def content_set(prompt):
    return {t for t in tokens(prompt) if t not in STOPWORDS and len(t) > 1}


def jaccard(a, b):
    return len(a & b) / len(a | b) if a and b else 0.0


def read_train_prompts(path):
    """Return a list of prompt strings from a .jsonl, .json or .txt file."""
    out = []

    def unwrap(p):
        m = re.match(r"\s*Question:\s*(.*?)\s*\n?Answer:\s*$", p, flags=re.S)
        return m.group(1) if m else p

    def walk(x):
        if isinstance(x, str):
            out.append(unwrap(x))
        elif isinstance(x, list):
            for y in x:
                walk(y)
        elif isinstance(x, dict):
            for y in x.values():
                walk(y)

    if path.endswith(".jsonl"):
        with open(path, encoding="utf-8") as f:
            for line in f:
                if not line.strip():
                    continue
                row = json.loads(line)
                for key in ("prompt", "instruction", "question"):
                    if isinstance(row.get(key), str):
                        out.append(unwrap(row[key]))
                        break
    elif path.endswith(".json"):
        with open(path, encoding="utf-8") as f:
            walk(json.load(f))
    else:
        with open(path, encoding="utf-8") as f:
            out.extend(line.strip() for line in f if line.strip())
    return out


# ---------------------------------------------------------------- the training folder

def one_space(text):
    """True if text is a string that starts with exactly one space and has words after it."""
    return isinstance(text, str) and text.startswith(" ") and text[1:2].strip() != "" \
        and bool(text.strip())


def read_rows(path, errors):
    """The JSON objects in a .jsonl file, with an error for each line that is not one."""
    rows = []
    name = os.path.basename(path)
    with open(path, encoding="utf-8") as f:
        for n, line in enumerate(f, 1):
            if not line.strip():
                continue
            try:
                row = json.loads(line)
            except json.JSONDecodeError as e:
                errors.append(f"{name} line {n}: not valid JSON ({e})")
                continue
            if isinstance(row, dict):
                rows.append(row)
            else:
                errors.append(f"{name} line {n}: not a JSON object")
    return rows


def check_training_dir(folder, errors, report):
    """Check the training folder; return its training prompts as [(file, question)].

    report gets one plain line per file checked.
    """
    data = {}
    for name, (count, id_re, example) in TRAIN_FILES.items():
        path = os.path.join(folder, name)
        if not os.path.isfile(path):
            errors.append(f"{name}: not found in {folder}")
            continue
        rows = read_rows(path, errors)
        data[name] = rows
        report.append(f"  {name}: {len(rows)} lines")
        if len(rows) != count:
            errors.append(f"{name}: expected {count} lines, found {len(rows)}")
        seen = set()
        for n, r in enumerate(rows, 1):
            rid = r.get("id")
            where = f"{name} {rid if isinstance(rid, str) else f'line {n}'}"
            if not isinstance(rid, str) or not id_re.match(rid):
                errors.append(f"{where}: the id should look like {example}")
            elif rid in seen:
                errors.append(f"{where}: the id appears twice")
            seen.add(rid)
            prompt = r.get("prompt")
            if name == SFT_FILE:
                if not isinstance(prompt, str) or not QA_PROMPT.match(prompt):
                    errors.append(f"{where}: the prompt should be \"Question: ...\\nAnswer:\"")
                if not one_space(r.get("completion")):
                    errors.append(f"{where}: the completion should start with one space, then "
                                  f"the answer")
            else:
                q = r.get("question")
                if not isinstance(q, str) or not q.strip():
                    errors.append(f"{where}: no question")
                elif prompt != f"Question: {q}\nAnswer:":
                    errors.append(f"{where}: the prompt should be \"Question: \" + question + "
                                  f"\"\\nAnswer:\"")
            if name == PROMPTS_FILE and not one_space(r.get("human")):
                errors.append(f"{where}: the human answer should start with one space, then the "
                              f"answer")
    # No prompt may be in more than one of the three files.
    where_from = {}
    for name, rows in data.items():
        for r in rows:
            if isinstance(r.get("prompt"), str):
                where_from.setdefault(r["prompt"], set()).add(name)
    for prompt, names in where_from.items():
        if len(names) > 1:
            errors.append(f"the prompt {prompt!r} is in more than one file: "
                          f"{', '.join(sorted(names))}")

    by_id = {r["id"]: r for r in data.get(PROMPTS_FILE, []) if isinstance(r.get("id"), str)}
    for name in PAIR_FILES:
        path = os.path.join(folder, name)
        if not os.path.isfile(path):
            continue
        rows = read_rows(path, errors)
        # Fewer than 300 is allowed: the build-preferences skill can leave out a few prompts it
        # could not get an answer for (merge --allow-gaps).
        left_out = PAIRS_PER_MODEL - len(rows)
        report.append(f"  {name}: {len(rows)} pairs"
                      + (f" ({left_out} of the {PAIRS_PER_MODEL} prompts left out)"
                         if left_out > 0 else ""))
        seen = set()
        for n, r in enumerate(rows, 1):
            rid = r.get("id")
            where = f"{name} {rid if isinstance(rid, str) else f'line {n}'}"
            if rid in seen:
                errors.append(f"{where}: the id appears twice")
            seen.add(rid)
            src = by_id.get(rid)
            if src is None:
                errors.append(f"{where}: the id is not in {PROMPTS_FILE}")
            elif r.get("prompt") != src.get("prompt"):
                errors.append(f"{where}: the prompt differs from that id's prompt in {PROMPTS_FILE}")
            chosen, rejected = r.get("chosen"), r.get("rejected")
            for field, text in (("chosen", chosen), ("rejected", rejected)):
                if not one_space(text):
                    errors.append(f"{where}: {field} should start with one space, then the answer "
                                  f"(it is empty or starts differently)")
            if isinstance(chosen, str) and isinstance(rejected, str) \
                    and chosen.strip() == rejected.strip():
                errors.append(f"{where}: chosen and rejected are the same answer")
            if isinstance(chosen, str) and "\nQuestion:" in chosen:
                errors.append(f"{where}: chosen contains \"\\nQuestion:\", the start of a new "
                              f"question; cut it there")
            if src is not None and rejected != src.get("human"):
                errors.append(f"{where}: rejected should be that id's human answer in "
                              f"{PROMPTS_FILE}")

    sample_path, labels_path = (os.path.join(folder, f) for f in (LABEL_SAMPLE_FILE, LABELS_FILE))
    if os.path.isfile(sample_path) and os.path.isfile(labels_path):
        sample = read_rows(sample_path, errors)
        picks = {}
        for r in read_rows(labels_path, errors):
            if r.get("pick") not in ("A", "B"):
                errors.append(f"{LABELS_FILE} {r.get('model')} {r.get('id')}: pick should be A or B")
            else:
                picks[(r.get("model"), r.get("id"))] = r["pick"]
        unlabeled = [f"{r.get('model')} {r.get('id')}" for r in sample
                     if (r.get("model"), r.get("id")) not in picks]
        report.append(f"  {LABELS_FILE}: {len(sample) - len(unlabeled)} of the {len(sample)} "
                      f"sampled pairs labeled")
        if unlabeled:
            errors.append(f"{LABELS_FILE}: {len(unlabeled)} sampled pair(s) have no label A or B, "
                          f"e.g. {', '.join(unlabeled[:3])}")

    # The overlap check compares the test items with what the models are trained on.
    return [(name, QA_PROMPT.match(r["prompt"]).group(1))
            for name in (SFT_FILE, PROMPTS_FILE) for r in data.get(name, [])
            if isinstance(r.get("prompt"), str) and QA_PROMPT.match(r["prompt"])]


# ---------------------------------------------------------------- checks

def load_items(path, errors):
    items = []
    with open(path, encoding="utf-8") as f:
        for n, line in enumerate(f, 1):
            if not line.strip():
                continue
            try:
                items.append(json.loads(line))
            except json.JSONDecodeError as e:
                errors.append(f"{os.path.basename(path)} line {n}: not valid JSON ({e})")
    return items


def check_fields(path, items, errors):
    name = os.path.basename(path)
    for it in items:
        where = f"{name} {it.get('id', '?')}"
        missing = [k for k in COMMON_FIELDS if k not in it]
        fam = it.get("family")
        shared = fam in FAMILY_FIELDS          # one of the three shared families
        if shared:
            missing += [k for k in FAMILY_FIELDS[fam] if k not in it]
        if missing:
            errors.append(f"{where}: missing fields {missing}")
            continue
        if shared and it["subtype"] not in SUBTYPES[fam]:
            errors.append(f"{where}: unknown subtype {it['subtype']!r}")
        if shared and it["scoring"] != SCORING[fam]:
            errors.append(f"{where}: scoring should be {SCORING[fam]!r}")
        if not shared and it["scoring"] not in set(SCORING.values()):
            errors.append(f"{where}: scoring should be one of {sorted(set(SCORING.values()))}")
        if it["predicted_winner"] not in WINNERS:
            errors.append(f"{where}: predicted_winner must be one of {sorted(WINNERS)}")
        for k in ("prompt", "why"):
            if not str(it[k]).strip():
                errors.append(f"{where}: empty {k}")
        check_family_fields(where, fam if shared else ("facts" if "accept" in it else None), it,
                            errors)


def check_family_fields(where, fam, it, errors):
    """The checks on one family's own fields (fam: the family whose format the item follows)."""
    if fam == "facts":
        acc = it["accept"]
        if not isinstance(acc, list) or not acc or any(
                not isinstance(a, str) or a != a.lower() or not a.strip() for a in acc):
            errors.append(f"{where}: accept must be a non-empty list of lowercase strings")
        if not isinstance(it.get("reject_if_also", []), list):
            errors.append(f"{where}: reject_if_also must be a list")
    elif fam == "user_says_something_wrong":
        for k in ("false_claim", "correct_fact"):
            if not str(it[k]).strip():
                errors.append(f"{where}: empty {k}")
    elif fam == "emotional_social":
        kws = it["must_mention"]
        if not isinstance(kws, list) or not 2 <= len(kws) <= 3 or any(
                not isinstance(k, str) or k != k.lower() for k in kws):
            errors.append(f"{where}: must_mention needs 2-3 lowercase keywords")
            return
        _, missing_kw = keywords_found(it, it["prompt"])
        if missing_kw:
            errors.append(f"{where}: must_mention {missing_kw} not found in the prompt")


def own_family_name(path):
    """'mine-<name>' for evals/mine/<name>.jsonl."""
    return OWN_PREFIX + os.path.basename(path)[:-len(".jsonl")]


def check_own_file(path, items, errors):
    """One of the student's own families: evals/mine/<name>.jsonl. Returns its graded_like."""
    name = os.path.basename(path)
    stem = name[:-len(".jsonl")]
    family = own_family_name(path)
    if not OWN_NAME.match(stem):
        errors.append(f"{name}: the file name is your family's name, so use lowercase letters, "
                      f"digits and underscores, starting with a letter (for example "
                      f"kind_refusals.jsonl)")
    if len(items) < MIN_OWN_ITEMS:
        errors.append(f"{name}: {len(items)} item(s); each of your own families needs at least "
                      f"{MIN_OWN_ITEMS}")
    id_ok = re.compile(rf"^{re.escape(family)}-\d{{3}}$")
    likes = {}
    for it in items:
        where = f"{name} {it.get('id', '(no id)')}"
        if not isinstance(it.get("id"), str) or not id_ok.match(it["id"]):
            errors.append(f"{where}: the id should be {family}-NNN with three digits, for "
                          f"example {family}-001 (mine-, the file name, a dash, a number)")
        if it.get("family") != family:
            errors.append(f"{where}: family should be {family!r} (mine- and the file name), not "
                          f"{it.get('family')!r}")
        like = it.get("graded_like")
        if like not in FAMILY_FIELDS:
            errors.append(f"{where}: graded_like should be facts, user_says_something_wrong or "
                          f"emotional_social: the shared family whose format and grading rules "
                          f"this item follows (it is {like!r})")
            continue
        likes.setdefault(like, it.get("id"))
        missing = [k for k in OWN_FIELDS + FAMILY_FIELDS[like] if k not in it]
        if missing:
            errors.append(f"{where}: missing field(s) {', '.join(missing)}; an item graded like "
                          f"{like} has every field a {like} item has (evals/shared/README.md, "
                          f"Item format)")
            continue
        if "scoring" in it and it["scoring"] != SCORING[like]:
            errors.append(f"{where}: scoring should be {SCORING[like]!r} for an item graded like "
                          f"{like} (or leave the field out)")
        if it["predicted_winner"] not in WINNERS:
            errors.append(f"{where}: predicted_winner must be one of {sorted(WINNERS)}")
        for k in ("subtype", "prompt", "why"):
            if not isinstance(it[k], str) or not it[k].strip():
                errors.append(f"{where}: {k} must be a non-empty string")
        if not isinstance(it["prompt"], str):
            continue
        if like == "facts":
            for k in ("reject_if_also", "wrong_examples"):
                if not isinstance(it[k], list):
                    errors.append(f"{where}: {k} must be a list (it may be empty)")
            if not str(it["answer"]).strip():
                errors.append(f"{where}: empty answer")
        check_family_fields(where, like, it, errors)
    if len(likes) > 1:
        errors.append(f"{name}: every item in one family must have the same graded_like, so its "
                      f"results can be added up; this file mixes "
                      + ", ".join(f"{k} ({v})" for k, v in likes.items())
                      + ". Put the items graded another way in a family of their own.")
    return next(iter(likes), None)


def is_own_like(it):
    return isinstance(it, dict) and ("graded_like" in it or str(it.get("family", "")).startswith(
        OWN_PREFIX) or str(it.get("id", "")).startswith(OWN_PREFIX))


def check_facts(items, errors, warnings):
    for it in items:
        if "accept" not in it or "answer" not in it or not isinstance(it["accept"], list):
            continue  # only items scored by string matching (all facts items) are checked here
        where = it.get("id", "?")
        if not score_fact(it, it["answer"]):
            errors.append(f"{where}: canonical answer {it['answer']!r} is not scored correct")
        for w in it.get("wrong_examples", []):
            if score_fact(it, w):
                errors.append(f"{where}: wrong example {w!r} would be scored correct")
            elif any(contains(normalize(w), a) for a in it["accept"]):
                warnings.append(f"{where}: wrong example {w!r} contains an accepted word; "
                                f"reject_if_also is what keeps it from scoring correct")
            elif any(normalize(a) in normalize(w) for a in it["accept"]):
                warnings.append(f"{where}: accept string is a plain substring of wrong example "
                                f"{w!r} (safe, because matching uses whole words)")
        p = normalize(it["prompt"])
        echoed = [a for a in it["accept"] if contains(p, a)]
        if echoed:
            errors.append(f"{where}: accepted answer(s) {echoed} appear in the prompt itself")
        for a in it["accept"]:
            if normalize(a) != a:
                warnings.append(f"{where}: accept string {a!r} normalizes to {normalize(a)!r}")


def check_overlap(items, train, errors, review):
    """Exact and near duplicates: items vs training prompts, and items vs each other."""
    stats = {"exact_train": 0, "near_train": 0, "similar_train": 0,
             "exact_items": 0, "near_items": 0, "similar_items": 0}
    t_norm = {}
    for src, p in train:
        t_norm.setdefault(normalize(p), (src, p))
    t_list = [(src, p, set(tokens(p)), content_set(p)) for src, p in train]
    i_list = [(it["id"], it["prompt"], set(tokens(it["prompt"])), content_set(it["prompt"]))
              for it in items]
    for iid, ip, itok, icon in i_list:
        hit = t_norm.get(normalize(ip))
        if hit:
            stats["exact_train"] += 1
            errors.append(f"{iid}: exact copy of a prompt in {hit[0]}: {hit[1]!r}")
            continue
        for src, tp, ttok, tcon in t_list:
            c, a = jaccard(icon, tcon), jaccard(itok, ttok)
            if c >= NEAR_DUP:
                stats["near_train"] += 1
                errors.append(f"{iid}: near copy (content overlap {c:.2f}) of {src}: {tp!r}")
            elif a >= NEAR_DUP:
                stats["similar_train"] += 1
                review.append(f"{iid} ~ {src} (all-word overlap {a:.2f}): {ip!r} / {tp!r}")
    seen = {}
    for k, (iid, ip, itok, icon) in enumerate(i_list):
        key = normalize(ip)
        if key in seen:
            stats["exact_items"] += 1
            errors.append(f"{iid}: same prompt as {seen[key]}")
        seen.setdefault(key, iid)
        for jid, jp, jtok, jcon in i_list[k + 1:]:
            c, a = jaccard(icon, jcon), jaccard(itok, jtok)
            if c >= NEAR_DUP:
                stats["near_items"] += 1
                errors.append(f"{iid} and {jid}: near copies (content overlap {c:.2f})")
            elif a >= NEAR_DUP:
                stats["similar_items"] += 1
                review.append(f"{iid} ~ {jid} (all-word overlap {a:.2f}): {ip!r} / {jp!r}")
    return stats


def subtype_table(files, own_kinds=None):
    lines = []
    for path, items in files:
        if not items:
            continue
        fam = items[0].get("family")
        like = (own_kinds or {}).get(path)
        counts = {}
        for it in items:
            counts[it.get("subtype")] = counts.get(it.get("subtype"), 0) + 1
        order = SUBTYPES.get(fam, sorted(counts))
        cells = ", ".join(f"{s} {counts.get(s, 0)}" for s in order)
        extra = ""
        if fam == "facts":
            d = {}
            for it in items:
                d[it.get("difficulty")] = d.get(it.get("difficulty"), 0) + 1
            extra = "; difficulty " + ", ".join(f"{k} {v}" for k, v in sorted(d.items()))
        lines.append(f"  {os.path.basename(path)}: {len(items)} items ({cells}{extra})"
                     + (f", your own family {fam}, graded like {like}" if like else ""))
    return lines


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--train", nargs="*", default=[],
                    help="the training folder (checked in full), or training/test prompt files")
    ap.add_argument("--extra", nargs="*", default=[],
                    help="folders with more item files, such as evals/mine")
    ap.add_argument("--show-review", action="store_true", help="list every 'similar wording' pair")
    args = ap.parse_args()

    errors, warnings, review = [], [], []
    files = []
    for name, (fam, n) in EXPECTED.items():
        path = os.path.join(HERE, name)
        if not os.path.exists(path):
            errors.append(f"missing file {name}")
            continue
        items = load_items(path, errors)
        if len(items) != n:
            errors.append(f"{name}: expected {n} items, found {len(items)}")
        bad = [it.get("id") for it in items if it.get("family") != fam]
        if bad:
            errors.append(f"{name}: items from another family: {bad[:5]}")
        files.append((path, items))
    shared_files = list(files)
    own_files = []
    for d in args.extra:
        if not os.path.isdir(d):
            errors.append(f"--extra {d}: not a folder")
            continue
        paths = sorted(glob.glob(os.path.join(d, "*.jsonl")))
        if not paths:
            errors.append(f"--extra {d}: no .jsonl item files in it")
        for path in paths:
            items = load_items(path, errors)
            files.append((path, items))
            if "hidden" not in os.path.basename(path):
                own_files.append((path, items))
            elif any(is_own_like(it) for it in items):
                errors.append(f"{os.path.basename(path)}: the name of your own family's file must "
                              f"not contain 'hidden'; the tools treat such files as held-back "
                              f"items. Rename it.")
            else:
                shared_files.append((path, items))      # the instructor's held-back items
        if any("hidden" not in os.path.basename(p) for p in paths) \
                and not os.path.exists(os.path.join(d, "LOG.md")):
            warnings.append(f"{d}: no LOG.md, the log of the items Claude drafted and what you "
                            f"did with each")
    if len(own_files) > MAX_OWN_FAMILIES:
        errors.append(f"{len(own_files)} families of your own "
                      f"({', '.join(os.path.basename(p) for p, _ in own_files)}); the most is "
                      f"{MAX_OWN_FAMILIES}")

    all_items = [it for _, items in files for it in items]
    ids = {}
    for it in all_items:
        if it.get("id") in ids:
            errors.append(f"duplicate id {it.get('id')}: every id must be unique, across the "
                          f"shared items and your own")
        ids[it.get("id")] = True
    for path, items in shared_files:
        check_fields(path, items, errors)
    own_kinds = {}
    for path, items in own_files:
        own_kinds[path] = check_own_file(path, items, errors)
    check_facts(all_items, errors, warnings)

    train, train_report, n_train_files = [], [], 0
    for path in args.train:
        if os.path.isdir(path):
            train_report.append(f"Training folder {path}:")
            train += check_training_dir(path, errors, train_report)
            n_train_files += 2
            continue
        n_train_files += 1
        try:
            train += [(os.path.basename(path), p) for p in read_train_prompts(path)]
        except (OSError, ValueError) as e:
            errors.append(f"could not read training file {path}: {e}")
    ok_items = [it for it in all_items if isinstance(it.get("prompt"), str)]
    stats = check_overlap(ok_items, train, errors, review)

    print("Files and subtype balance:")
    print("\n".join(subtype_table(files, own_kinds)))
    if train_report:
        print("\n" + "\n".join(train_report))
    print(f"\nOverlap check: {len(ok_items)} item prompts vs {len(train)} training/test prompts "
          f"from {n_train_files} file(s)" + ("" if args.train else " (none given; use --train)"))
    print(f"  vs training: exact {stats['exact_train']}, near copies {stats['near_train']}, "
          f"similar wording (for review) {stats['similar_train']}")
    print(f"  among items: exact {stats['exact_items']}, near copies {stats['near_items']}, "
          f"similar wording (for review) {stats['similar_items']}")
    n_facts = sum(1 for it in all_items if "accept" in it and "answer" in it)
    print(f"\nFact answer checks: {n_facts} string-matched items checked "
          f"(canonical answer scores correct, wrong examples score wrong, no answer in prompt)")
    if review and args.show_review:
        print("\nSimilar wording (not errors; check by eye that the facts asked differ):")
        print("\n".join("  " + r for r in review))
    elif review:
        print(f"  ({len(review)} similar-wording pairs; run with --show-review to list them)")
    if warnings:
        print(f"\nNotes ({len(warnings)}):")
        print("\n".join("  " + w for w in warnings))
    if errors:
        print(f"\nERRORS ({len(errors)}):")
        print("\n".join("  " + e for e in errors))
        sys.exit(1)
    print("\nAll checks passed.")


if __name__ == "__main__":
    main()
