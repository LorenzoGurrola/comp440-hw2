---
name: build-preferences
description: Part 2 Step 5 of HW2. Builds the preference pairs from the student's two constitutions. For each of the 300 training prompts, answer-writer subagents (Sonnet) write the answer each constitution asks for (chosen), paired with the human answer (rejected). Pauses after the first batch of each model so the student can read three answers, checks that every prompt is answered once, reports repeated openings and phrases, checks the files, and commits and pushes them on a yes. Carries on where it stopped after a usage limit. Use when asked to "build the preference data", "make the pairs", "/build-preferences", or to carry on after a limit.
---

# Build the preference pairs (Part 2 Step 5)

The `answer-writer` subagent (`.claude/agents/answer-writer.md`, Sonnet) writes the answers for
one batch of prompts; its definition is the one place the writing rules are written. `pairs.py`
in this folder does everything else: it copies each model's constitution, splits the prompts
into batches, keeps track of finished batches, checks the answers and writes the pairs files.
Run every command from the repository's folder.

Each pair has a prompt from `training/prompts-300.jsonl`, a *chosen* answer (Claude's, written
under one constitution) and a *rejected* answer (the human answer from the Dolly dataset). One
file per model: `training/pairs-succinct.jsonl` and `training/pairs-persona.jsonl`. In Step 8,
DPO trains each model to prefer its chosen answers.

Rules for the whole skill:

- Never write or edit `constitutions.md` or `voice-samples.md` on your own. They are the
  student's work (Steps 1 and 2). If they want to change one, they edit it or dictate the
  change for you to type, under the dictation rule in `CLAUDE.md`, then run this skill again.
- Never say whether the answers are good or follow the constitution. That is the student's
  reading, and Step 6 measures it.
- Give each writer only the lines `pairs.py` printed: no hints about the person, no examples,
  no opinion of the constitution. The answers should come from the constitution alone, so that
  what the models learn can be traced back to it.
- Never describe or summarize the answers. When they ask to see answers or pairs, show them
  word for word and in full: with `pairs.py show`, or the lines of a pairs file they ask for.

## 0. Before starting

1. Run `git log --format=%s`. If no commit's whole subject is exactly `Predictions locked`,
   stop and say that Step 4 comes first. Predictions made after seeing the training data
   aren't predictions.
2. In one message, say what is about to happen: about 24 Claude subagents write 600 answers,
   12 batches per model, succinct first. After each model's first batch you'll show three
   answers and ask whether they look like what that constitution asks for. It runs on their
   Claude plan and uses a good part of one usage window. If a usage limit stops it, finished
   batches are kept, and running `/build-preferences` again after the limit resets carries on
   from there. Ask whether to start.

Then do steps 1 to 5 for `succinct`, and again for `persona`. MODEL below is one of the two.

## 1. Plan the model's batches

```
python3 .claude/skills/build-preferences/pairs.py plan --model MODEL
```

- It copies the Core, that model's style section and "When they conflict" (and for the persona,
  `voice-samples.md`) into `training/.batches/MODEL/constitution.md`, splits the prompts into
  batches of 25 and prints the exact prompt for each batch's writer.
- If it says a section or file is not filled in yet, stop and name the step it belongs to.
- If it says `training/prompts-300.jsonl` is not found, their copy doesn't have the Part 2
  files yet: run the template-update check in `CLAUDE.md`, then try again.
- If it says "Already planned", it is carrying on: finished batches are kept and it lists only
  the batches that still need a writer. If every batch has been written, go to step 5; if only
  batch 01 has, go to step 3; if batch 01 and others have, go to step 4.
- If it says the constitution changed since the batches were written, tell them the earlier
  MODEL answers were written under the old text, and ask before running `plan --model MODEL
  --restart`, which deletes them.

## 2. Write the first batch

Call the Agent tool once, for batch 01 only, with:

- `subagent_type`: `"answer-writer"`
- `model`: `"sonnet"`
- `description`: `"Write MODEL answers, batch 01"`
- `prompt`: exactly the three lines `plan` printed for that batch, and nothing else:

  ```
  Constitution: training/.batches/MODEL/constitution.md
  Input batch: training/.batches/MODEL/in-01.jsonl
  Output file: training/.batches/MODEL/out-01.jsonl
  ```

## 3. Pause: three answers, word for word

```
python3 .claude/skills/build-preferences/pairs.py show --model MODEL --batch 1 --n 3
```

Show its output word for word and in full, with no summary, comment or description. Then ask
one question: do these look like what your MODEL constitution asks for?

- On a yes, go on to step 4.
- On a no, stop. They change `constitutions.md` (or dictate the change), as in Step 2, then
  run `/build-preferences` again; `plan` will notice the change. Don't suggest what to change.
- If they want to see more first, run `show` again with `--n 6` or another `--batch`, and
  show it the same way.
- If `show` says batch 01 has no answers, the writer failed: run step 2 once more.

## 4. Write the rest

Run `python3 .claude/skills/build-preferences/pairs.py status --model MODEL`. It lists the
batches that still need a writer, with the exact lines for each. Spawn one `answer-writer` per
batch exactly as in step 2. Launch at most 8 in one message; agents in one message run in
parallel. Wait for all of them to finish before launching the next group. Don't poll with
sleep or status loops. A writer that fails or writes bad lines needs no retry now: step 5
catches it.

## 5. Merge, then redo the gaps (at most twice)

```
python3 .claude/skills/build-preferences/pairs.py merge --model MODEL
```

- A writer's final message is not a count you can trust. Merge counts every answer: each
  prompt answered exactly once, no empty answer, none copied from the human answer.
- If its output ends with `REDO NEEDED`, spawn one `answer-writer` per redo row exactly as in
  step 2, with the lines it printed, then run merge again.
- If it ends with `GAPS REMAIN`, tell them how many prompts are still missing and ask whether
  to leave them out (`merge --model MODEL --allow-gaps`). A few missing pairs barely change
  the training.
- When it writes `training/pairs-MODEL.jsonl`, show its output from "Wrote" to the end word
  for word: the count, the average lengths and the variety check. Say in one line what the variety check counts:
  openings, endings and phrases that many answers share. A model trained on them tends to
  learn those phrases rather than the style, as a test model in this course did. Don't say
  whether the numbers are high or low. If they want to change the constitution because of what
  they see, they can, and run this skill again. Ask whether to go on.

## 6. Check the files

After both models:

```
python3 evals/shared/validate.py --train training --extra evals/mine
```

It checks that no test item, shared or theirs, is a copy or near copy of a training prompt,
and that the training files have the right fields. Show its summary lines. If it lists one of
their own items as too close to a training prompt, show both and let them decide whether to
change their item, under Step 3's rules; the pairs stay as they are. If it reports any other
problem, stop, show it, and ask them to post it in `#comp440-f26`.

## 7. Commit and push

The notebook fetches the pairs from their fork on GitHub, so they must be pushed before the
training cells run. Ask whether to commit and push them, and wait. Only on a yes:

```
python3 dump_transcript.py
git add training/pairs-succinct.jsonl training/pairs-persona.jsonl
git commit -m "Preference data built"
git push
```

Then say that Step 6, labeling a sample of the pairs blind, is next.

## Notes

- `training/.batches/` holds the working files: each model's copy of its constitution, the
  batches, the answers and the redo files. `pairs.py` keeps that folder out of git. Never edit
  the files there by hand, since `merge` counts exactly what the writers wrote.
- Writing the answers runs on the student's Claude Code plan and counts against its usage
  limits. It costs no API dollars and needs no API key.
- If a usage limit stops the build, nothing finished is lost. When they run
  `/build-preferences` again, start at step 0 (skip its second item) and go through both
  models: a model whose batches are all written goes straight to step 5, which writes the same
  pairs file again.
- If the Agent tool does not offer `answer-writer`, the session probably started before the
  agent file existed. Restart Claude Code following "Restarting Claude Code" in `CLAUDE.md`,
  then carry on from step 1; finished batches are kept.
