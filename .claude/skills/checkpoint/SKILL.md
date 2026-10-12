---
name: checkpoint
description: The end-of-part ritual for HW2. Run it at the end of every part and before submission. Checks the part's run folder (in Part 2, also the files it hands in and that the predictions were locked before the training data), names the part's blank writeup slots, confirms this session is in TRANSCRIPT.md, and commits and pushes the part once the student says yes.
---

Five steps, in this order, every time. Stop at the first thing missing: that is the current step,
and the part is not done until it is filled.

1. Check the part's run folder. Part 0 has no run folder, so skip this step for Part 0. Show
   what you found in one line each. Do not say whether the numbers look right.
   - Part 1: a folder under `evals/runs/` with a response file for the base model and a Sonnet
     grades folder, and `status` in its `run.json` at `graded` or later.
   - Part 2: the four-model folder under `evals/runs/`, with response files for `base`, `sft`,
     `succinct` and `persona` in `responses/`; a Sonnet grades folder (usually
     `grades/sonnet-low/`) and the Opus audit (usually `grades/opus-medium-audit/`); their
     review decisions (`review/decisions-<name>.jsonl`); their ratings
     (`ratings/ratings.jsonl`); and `status` in `run.json` at `audited` or later.
     Then the other files Part 2 hands in: `constitutions.md`, `voice-samples.md`, at least
     two families in `evals/mine/` and `evals/mine/LOG.md`, `training/pairs-succinct.jsonl`,
     `training/pairs-persona.jsonl` and `training/labels.jsonl`. Run
     `python3 evals/shared/validate.py --train training --extra evals/mine` and paste its last
     line.
   - Part 2, the order of the commits. Predictions made after training aren't predictions, so
     `Predictions locked` must come before the training data. Find the first commit that holds
     it: the first line of
     `git log --reverse --format='%h %s' -- training/pairs-succinct.jsonl training/pairs-persona.jsonl training/labels.jsonl`.
     Then run `git log --format=%s HASH~1` with that commit's hash, which lists every commit
     before it, and check that one subject there is exactly `Predictions locked`. Say what you
     found in one line. If it is missing or came later, say so plainly and go on: it can't be
     fixed now, and the history must never be rewritten to change it.
2. Read `WRITEUP.md` in full, every line: if the Read tool stops early, read the rest. Never
   say you read all of it unless you did. Then name, one line each, every slot in **this part's
   section** that is still `XXXX`, and every answer that doesn't answer its step's question.
   Name them and ask what each needs; do not suggest wording.
3. Run `python3 dump_transcript.py` and paste its last line. It says how many sessions are in
   `TRANSCRIPT.md` and whether this session is one of them. If the script fails on their
   machine, say so and go on: it costs them nothing.
4. If they have not already said to commit this part, ask whether they are ready, and wait.
   Only on a yes, said now or earlier in the message that asked for this checkpoint, commit and
   push:

   ```
   git add -A
   git commit -m "Part N done"
   git push
   ```

   On anything other than a yes, say what is still open and stop.
5. Remind them to submit their repository URL through the form:
   https://forms.gle/mgKcnqzTGxNaGvteA. When they say they have, say **YOU ARE FINISHED WITH
   PART N!**

Nothing here is a judgment about the work. Presence and form only.
