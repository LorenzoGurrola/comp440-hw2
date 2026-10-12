# Training data for Part 2

This folder holds the data your two models are trained on in Part 2. Three files come with the
template. The rest are written in your repository while you work through Steps 5 and 6.

**Please don't edit the three files that come with the template.** Everyone in the class trains
from the same example answers and the same prompts, so the differences between your models and a
classmate's come from your constitutions, not from the data. The notebook and the
`build-preferences` skill also read these files by their exact names.

## The files

| File | Rows | What it is | Used in |
|---|---|---|---|
| `sft-dolly-600.jsonl` | 600 | Questions with human-written answers, for training on example answers (SFT) | Step 7 |
| `prompts-300.jsonl` | 300 | Questions, each with a human-written answer, that Claude answers under your constitutions | Step 5 |
| `readout-10.jsonl` | 10 | Questions with short answers, kept out of training, for reading the models' answers side by side | Steps 7 and 8 |
| `pairs-succinct.jsonl`, `pairs-persona.jsonl` | 300 each | Your preference pairs: Claude's answer under each constitution (*chosen*) and the human answer (*rejected*) | Steps 5, 6 and 8 |
| `label-sample.jsonl`, `label-key.json` | 30 | The pairs you label blind (15 per model), and the key saying which side is Claude's answer | Step 6 |
| `labels.jsonl` | 30 | Your labels, one per pair in the sample | Step 6 |

The files in the last three rows don't come with the template. Claude's `build-preferences`
skill writes the pairs files, `evals/shared/label_tools.py sample` writes the sample and the key,
and Claude writes `labels.jsonl` from what you tell it. **Don't open `label-key.json` until
`labels.jsonl` holds a label for every pair in the sample.** Seeing the key first would turn your
labels into a copy of Claude's. `label_tools.py score` opens it for you once the labels are in.

Here is one line of `sft-dolly-600.jsonl`:

```
{"id": "sft-001", "prompt": "Question: Is society ready for flying cars ?\nAnswer:", "completion": " No, significant work needs to done in terms of : Infrastructure to support cars that can traverse the airspace New FAA regulations to manage airspace safety New driver safety training and licenses New charging stations New insurance policies"}
```

During SFT the model reads the `prompt` and learns to write the `completion`. The completion starts
with a space because the model writes it right after "Answer:".

Here is one line of `prompts-300.jsonl`:

```
{"id": "pair-001", "question": "What is a noun?", "prompt": "Question: What is a noun?\nAnswer:", "human": " A noun is a naming word. It generally refers to the name of a specific object, person, place or idea."}
```

In Step 5, Claude writes its own answer to the `question` under each of your constitutions. That
answer becomes *chosen* in your pairs file, and the `human` answer becomes *rejected*.

The answers are people's answers, unedited. Some have typos, some are wrong, and some were true in
2023 but are out of date now. I left them as they are: what the SFT model learns from them,
mistakes included, is part of what you'll look at in Step 7.

## Where the data came from

Every question and human answer here comes from
[databricks-dolly-15k](https://huggingface.co/datasets/databricks/databricks-dolly-15k), about
15,000 questions and answers that Databricks employees wrote by hand in 2023. I built the files
this way:

- Kept only rows with no reference passage, in the categories `open_qa`, `general_qa`,
  `brainstorming` and `creative_writing`, with an answer of 60 to 700 characters and a question
  of at most 250 characters. That leaves 5,628 rows.
- Shuffled them with Python's `random.seed(0)` followed by `random.shuffle()`.
- Took the first 600 for `sft-dolly-600.jsonl`. These are the same 600 examples I used when I
  tried the training on a T4 before the course.
- Took the next 300 questions for `prompts-300.jsonl`, skipping any question that repeats one
  already picked.
- Picked the 10 readout questions by hand from the later rows with short answers: everyday
  questions with a settled answer.
- Checked every question in the three files against all the test prompts, the shared ones in
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
