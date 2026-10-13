# Training data for Part 2

This folder holds the data your two models are trained on in Part 2. Two files come with the
template. The rest are written in your repository while you work through Steps 5 and 6.

**Please don't edit the two files that come with the template.** Everyone in the class trains
from the same prompts, so the differences between your models and a
classmate's come from your constitutions, not from the data. The notebook and the
`build-preferences` skill also read these files by their exact names.

## The files

| File | Rows | What it is | Used in |
|---|---|---|---|
| `prompts-300.jsonl` | 300 | Questions, each with a human-written answer, that Claude answers under your constitutions | Step 5 |
| `readout-10.jsonl` | 10 | Questions with short answers, kept out of training, for reading the models' answers side by side | Steps 7 and 8 |
| `pairs-succinct.jsonl`, `pairs-persona.jsonl` | 300 each | Your preference pairs: Claude's answer under each constitution (*chosen*) and the human answer (*rejected*). SFT trains on the chosen answers, DPO on the pairs | Steps 5 to 8 |
| `label-sample.jsonl`, `label-key.json` | 10 | The pairs you label blind (5 per model), and the key saying which side is Claude's answer | Step 6 |
| `labels.jsonl` | 10 | Your labels, one per pair in the sample | Step 6 |

The files in the last three rows don't come with the template. Claude's `build-preferences`
skill writes the pairs files, `evals/shared/label_tools.py sample` writes the sample and the key,
and Claude writes `labels.jsonl` from what you tell it. **Don't open `label-key.json` until
`labels.jsonl` holds a label for every pair in the sample.** Seeing the key first would turn your
labels into a copy of Claude's. `label_tools.py score` opens it for you once the labels are in.

Here is one line of `prompts-300.jsonl`:

```
{"id": "pair-001", "question": "What is a noun?", "prompt": "Question: What is a noun?\nAnswer:", "human": " A noun is a naming word. It generally refers to the name of a specific object, person, place or idea."}
```

In Step 5, Claude writes its own answer to the `question` under each of your constitutions. That
answer becomes *chosen* in your pairs file, and the `human` answer becomes *rejected*. In Step 7,
SFT reads each pair's `prompt` and learns to write its chosen answer; in Step 8, DPO trains on the
whole pair. Every answer starts with a space because the model writes it right after "Answer:".

The human answers are people's answers, unedited. Some have typos, some are wrong, and some were
true in 2023 but are out of date now. I left them as they are: they are the answers your models
learn to prefer less.

## Where the data came from

Every question and human answer here comes from
[databricks-dolly-15k](https://huggingface.co/datasets/databricks/databricks-dolly-15k), about
15,000 questions and answers that Databricks employees wrote by hand in 2023. I built the files
this way:

- Kept only rows with no reference passage, in the categories `open_qa`, `general_qa`,
  `brainstorming` and `creative_writing`, with an answer of 60 to 700 characters and a question
  of at most 250 characters. That leaves 5,628 rows.
- Shuffled them with Python's `random.seed(0)` followed by `random.shuffle()`.
- Set aside the first 600, which I used when I tried the training on a T4 before the course.
- Took the next 300 questions for `prompts-300.jsonl`, skipping any question that repeats one
  already picked. Later I swapped out seven that asked for a list or weren't questions, each for
  a plain question further down the shuffled rows, keeping its id.
- Picked the 10 readout questions by hand from the later rows with short answers: everyday
  questions with a settled answer.
- Checked every question in the two files against all the test prompts, the shared ones in
  `evals/shared/` and the held-back ones, and dropped any that matched or came close. A model
  trained on a test question could pass that test by memory, and then the test would measure
  nothing.

In each answer, line breaks and repeated spaces were collapsed into single spaces. Nothing else
was changed.

## License

databricks-dolly-15k is by Databricks, Inc., and is licensed under the
[Creative Commons Attribution-ShareAlike 3.0 Unported License](https://creativecommons.org/licenses/by-sa/3.0/)
(CC BY-SA 3.0). The files in this folder are a selection from it, reformatted as described above,
and they are shared under the same license.

"ShareAlike" means anything built from this data must carry the same license. That includes your
pairs files, because each pair holds a human answer from `prompts-300.jsonl`. Your fork is public,
so leave this README in place: it gives the credit and the license the data requires.
