# COMP 440 HW2 Part 2: Train your two models and decide what changed

Due **8:00am Tuesday, October 27**. The overall instructions are in the [README](../README.md).

In this part you'll train your two models and find out what your choices did to them. In
particular, you will:

- Write the rules for two models (a *constitution* for each) and tests of your own, and predict
  in numbers how each model will do before you train anything.
- Gain hands-on experience with training on example answers (SFT, supervised fine-tuning) and
  on pairs of answers where one is preferred (DPO, direct preference optimization).
- Check the AI grader against a second AI grader and your own grades, and rate your two models
  blind.
- Understand whose preferences ended up in each model.

This part builds on [Part 1](part1.md), so finish that first. You'll run the same evaluations on
four versions of the model: the base model, the model after SFT, and your two DPO models.

## Before you start

The choices and the writing in this part are yours, and Claude won't suggest them: this
assignment asks whose preferences shaped your models, and if Claude wrote those parts, the answer
would be Claude's. You can type your words yourself or dictate them to Claude, which writes them
down, tidied only with your OK, and adds nothing. Claude also runs the cells and commands,
explains anything you ask, drafts test items for you to review (Step 3) and writes most of your
training data (Step 5).

I recommend five sittings, since some steps need Claude to work for a while and one needs a GPU:

| Sitting | Steps | What you need |
|---|---|---|
| 1 | 1 to 4 | Claude Code |
| 2 | 5 and 6 | Claude Code, and a good share of your plan |
| 3 | 7 to 9 | Colab with a T4, about 20 GPU minutes in one go |
| 4 | 10 and 11 | Claude Code and the viewer |
| 5 | 12 and 13 | Claude Code and the viewer |

I expect Part 2 to take about [TBD] hours in all. Please don't leave sitting 3 for the last
night: free T4s are sometimes all taken.

## Step 1: Pick your famous person

One of your two models will answer in the voice of a famous person you admire. Your
constitutions and tests depend on this choice, so it comes first.

- Write their name, and two sentences on why you picked them, in `WRITEUP.md`.
- Copy **up to five** short passages of their own words into `voice-samples.md`, each with its
  source, as the file shows. Claude reads them when it writes answers in this voice in Step 5.

Four rules for who you pick:

1. A public figure with at least a few pages of their own public words. Never a private
   person, anyone at Macalester, or a classmate.
2. At most five passages, a few sentences each. Your fork is public, so I don't want whole
   speeches or chapters in it.
3. Your model will speak as "I" and invent things about the person's life. Its answers are an
   imitation, not the person, and your write-up must say so.
4. If you're not sure a choice is fair, ask on `#comp440-f26` before Step 2.

- Hints:
  - A person with a recognizable way of talking is easier to spot in a small model's answers.
  - Claude can copy a passage you choose, from a page you name, into `voice-samples.md`.
  - Quotation websites often credit people with words they never said. Take your passages from
    a primary source: the person's own book, speech, letter or interview.

> [!IMPORTANT]
> **Question:** What would someone notice first about the way this person talks or writes?

## Step 2: Write your two constitutions

A *constitution* is a short list of written rules that a model is trained to follow (here is
[the one Anthropic published for Claude](https://www.anthropic.com/news/claudes-constitution) in
2023). Your two models share one core and differ only in style, so that a difference between them
can be traced to the style.

- Open `constitutions.md`. Its `## Core` section is the same for everyone; don't change it. The
  radio announcer at the bottom shows the form.
- Under `## Succinct style`, write **at least five** lines on how the succinct model answers:
  how long, what it keeps and what it leaves out.
- Under `## Persona style`, write **at least five** lines on your person's voice: their habits,
  what they care about, the shape of their sentences. At least one line should say what the
  model *does*, not only how it sounds.
- Under `## When they conflict`, write, for each model, what wins when a style line pulls against
  a core line: for example, when the persona model is asked about something the person never
  knew.
- Warning: no catchphrases or fixed opening lines. When I trained this model on answers that each
  began with one of a few friendly openers, it learned the openers, not the friendliness: asked
  for a thank-you note, it replied with a stock greeting.

> [!IMPORTANT]
> **Questions:** Which line of your persona style do you think will be hardest for a 0.6B model
> to learn, and why? Where do you expect each style to pull against the core?

## Step 3: Write two test families of your own

A *family* is a set of test items of one kind, like the three in `evals/shared/`. Your two
families test what only you know about: your two styles.

- Pick one family you predict the succinct model will win and one the persona model will win. In
  `WRITEUP.md`, write a short paragraph for each: what it tests, which constitution lines it
  tests, and which model you think will win.
- Each family's items copy the format of one shared family (`facts`,
  `user_says_something_wrong` or `emotional_social`), name it in a `graded_like` field, and are
  graded by its rules. "Your own families" in `evals/shared/README.md` lists the fields.
- Write **at least five** items for each family yourself, in `evals/mine/<family>.jsonl`.
- Then ask Claude to draft more, until each family has **at least ten**. Accept, edit or reject
  each draft, and edit or reject **at least two** per family. Claude logs each draft and your
  decision in `evals/mine/LOG.md`.
- Ask Claude to check the files with `python3 evals/shared/validate.py --extra evals/mine`.
- Warning: nothing grades whether an answer sounds like your famous person; the grader checks
  only what the shared family's rules check. You'll judge the voice yourself in Step 12.

> [!IMPORTANT]
> **Questions:** For one draft you rejected or edited, what did it get wrong about what you
> wanted to test? Could a model score well on one of your families for the wrong reason?

## Step 4: Map your constitutions to your tests, and predict

A test only tells you about the rules it checks. Here you'll see which of your rules you can
measure, and commit to numbers before any training, so the results can't nudge your predictions.

- In `WRITEUP.md`, make one table with a row for every line of `constitutions.md`, core
  included, naming the family that tests it (shared or yours) or "not measured".
- For each of the five families, predict a number for each of your two models, in that family's
  measure: the share correct (facts), the mean score from 0 to 2 (user says something wrong), or
  the share of messages that do the task (emotional and social). Your families use the measure
  of the family they're graded like. Write numbers, not "succinct wins": only a number tells you
  how far off you were.
- Predict one more number: the share of your Step 11 blind comparisons the persona model will
  win.
- Ask Claude to commit and push with the subject `Predictions locked`. Nothing is built or
  trained before that commit, and I'll check that it came first.
- Hint: your Part 1 base-model run is a starting point.

> [!IMPORTANT]
> **Questions:** Which line of your constitutions does no test measure, and why is it hard to
> test? Which prediction are you least sure of?

## Step 5: Have Claude build the preference data

DPO trains on *pairs*: a prompt, a *chosen* answer and a *rejected* answer. It makes answers
like the chosen one more likely and answers like the rejected one less likely. Each model needs
300 pairs.

For each prompt in `training/prompts-300.jsonl`, Claude writes the chosen answer under your
constitution, and the rejected answer is a person's answer from the Dolly dataset (see
`training/README.md`). Claude writes them, rather than picking the better of two model answers,
because a 0.6B model almost never writes in your person's voice on its own. That puts Claude's
reading of your constitution into your models.

- Type `/build-preferences`. Claude starts helpers (Sonnet subagents) that write the answers in
  batches of 25, on your Claude Code plan, with no API key.
- After each model's first batch, Claude shows you three answers and asks whether they follow
  your constitution. If not, change `constitutions.md` and type `/build-preferences` again.
- At the end, Claude shows how varied and how long the answers are, checks the files, and asks
  before it commits and pushes them as `Preference data built`. The notebook reads them from
  your fork.
- Read **at least ten** pairs from each of `training/pairs-succinct.jsonl` and
  `training/pairs-persona.jsonl`.
- Hints:
  - This takes Claude about [TBD] minutes. If you hit your plan's usage limit, type
    `/build-preferences` again after it resets; it carries on where it stopped.
  - If you change your constitutions here, say what you changed in your Step 5 answer. Leave
    your Step 4 predictions as they are: Step 12 is where you explain a gap.

> [!IMPORTANT]
> **Questions:** Quote one chosen answer. What does it do that your constitution didn't ask for?
> Is there anything many of Claude's answers share that your model might learn to copy?

## Step 6: Label a sample yourself, blind

Before you train on Claude's pairs, check whether you agree with them: you'll pick the better
answer in 15 pairs per model without knowing which one Claude wrote.

- Ask Claude to run `python3 evals/shared/label_tools.py sample`. It draws 15 pairs per model,
  shuffles each pair's answers into A and B in `training/label-sample.jsonl`, and writes which
  side is Claude's to `training/label-key.json`. Don't open the key until all 30 labels are in:
  once you've seen it, you can't label blind again.
- For each pair, Claude shows you the question and both answers. Say which better follows that
  model's constitution, A or B, with a short reason. Claude writes your picks into
  `training/labels.jsonl`.
- Then ask Claude to run `python3 evals/shared/label_tools.py score`. It prints how often you
  picked Claude's answer for each model, and lists the pairs where you didn't.
- Hint: you'll often be able to tell which answer is Claude's. Label by the constitution anyway,
  and note when you could tell.

> [!IMPORTANT]
> **Questions:** How often did you pick Claude's answer, for each model? For one pair where you
> didn't, which line of the constitution did you and Claude read differently? If you picked
> Claude's answer every time, which pair were you least sure of, and why?

## Step 7: Train on example answers (SFT)

Steps 7, 8 and 9 happen in one Colab sitting of about 20 GPU minutes. The trained models live
only on that Colab machine: if Colab disconnects, they're gone, and Claude reruns the notebook
from the top.

- Read [`training.md`](training.md) first. It explains SFT and DPO with one example each, and how
  to read the numbers training prints. We'll cover both in class later, but you need the basics
  now.
- Claude pushes your commits before it runs the cells, since the notebook reads your files from
  your fork on GitHub. Keep your laptop plugged in and awake until Step 9's download arrives.
- Ask Claude to run the "Part 2 setup" cell, with the Part 1 cells it needs, then the Step 7
  cells.
- The training cell trains on 600 human-written Dolly answers: two passes, 150 steps, about 3
  minutes on a T4. Every 25 steps it prints the loss, which should fall from about 2.3 in the
  first pass to about 1.4 in the second.
- The last Step 7 cell prints five questions from `training/readout-10.jsonl`, each with the base
  and SFT models' answers. Read them.
- Hints:
  - If Colab says no T4 is free, try again in an hour or two.
  - If a cell stops with "CUDA out of memory", the README's Troubleshooting section says what to
    do.

> [!IMPORTANT]
> **Questions:** What did SFT change in the answers? Quote one answer that shows it. Did the
> answers get more correct, or only different in form? How can you tell from what you read?

## Step 8: Train your two models (DPO)

- Ask Claude to run the Step 8 cells. They train two models with DPO, both starting from your
  SFT model: the succinct model on `training/pairs-succinct.jsonl` and the persona model on
  `training/pairs-persona.jsonl`, about 3 minutes each.
- Each run is 50 steps of 8 pairs. Every 5 steps it prints the loss, the chosen reward, the
  rejected reward and the accuracy; [`training.md`](training.md) says what each one means.
- Each run ends with a small table of steps 5, 25 and 50. Copy both tables into `WRITEUP.md`
  before you close Colab: they aren't saved anywhere else.
- The last Step 8 cell prints five more readout questions, each with the SFT, succinct and
  persona models' answers. Read them.

> [!IMPORTANT]
> **Questions:** In each table, which moved further from 0, the chosen reward or the rejected
> reward, and by how much? What does that say each model learned? Quote one answer from each
> model that shows a change from SFT.

## Step 9: Run the evaluations on all four models

- Ask Claude to run the Step 9 cells. They answer the 240 shared items and your own items with
  all four models: base, SFT, succinct and persona. This takes about 7 minutes.
- The last Step 9 cell downloads `hw2-four-models.zip`. Allow the download if Chrome asks.
- Before anything is graded, ask Claude to show you all four models' answers to five items picked
  at random. In `WRITEUP.md`, write one sentence about each model: what you noticed. Grading
  starts only once those four sentences are in.
- Ask Claude to make a run from the zip and grade it with Sonnet: about 1,000 answers, on your
  plan. Grading needs no GPU, so this can be a new sitting.
- Write your run folder's name in `WRITEUP.md` (it looks like
  `evals/runs/2026-10-21-four-models`).
- Please don't open this run's Results or Answers pages until your Step 10 review decisions are
  in. Once you've seen the grader's numbers, it's hard to grade on your own.

> [!IMPORTANT]
> **Question:** Which model's answers surprised you most, and how?

## Step 10: Grade and audit

Every grader makes mistakes. Here you'll measure Sonnet's, with a second grader and your own
judgment.

- Ask Claude to audit the run with Opus at medium effort. Opus grades about 60 answers again,
  mostly ones that look hard, without seeing Sonnet's grades.
- Ask Claude to build a review queue: every answer where Sonnet and Opus disagree, plus a few
  where they agree.
- On the viewer's Review page, grade each answer yourself first (that grade is then locked), then
  see what Grader 1 and Grader 2 said, and decide who was right, with a reason from the rubric.
- You're welcome to write a rubric clarification and have Claude re-grade the reviewed answers
  with it ("Fix the scorer" in `evals/shared/README.md`). It's for this exercise only: your
  grades stay on the shared rubric.
- Hint: both graders follow `.claude/agents/eval-grader.md`, the file you found in Part 1 Step 6.
- Warning: Sonnet wrote your chosen answers in Step 5, and Sonnet grades your models. Keep that
  in mind when you decide.

> [!IMPORTANT]
> **Questions:** How many of Sonnet's grades did you overturn? Did those mistakes favor one of
> your models, and which row of your Step 4 table could they move, in which direction? The audit
> picked mostly hard answers: does that make Sonnet look better or worse than it is?

## Step 11: Rate your two models blind

Claude doesn't judge warmth or tone. People do, and in this step that's you.

- Open the viewer's Rate page for your run, type your name, choose your succinct and persona
  models, and press Start. You get a random 20 of the 40 emotional and social items, about 15
  minutes' work.
- For each item, read both messages (the page doesn't say which model wrote which), mark whether
  each does the task, then press "Send this one" under the one you'd rather send.
- Hint: you'll probably recognize your persona model's answers, so this isn't fully blind.
  That's fine; say so in your answer.

> [!IMPORTANT]
> **Questions:** What share of your picks went to each model, and what share of each model's
> messages did the task? Could you tell which model wrote which? How?

## Step 12: Check your predictions

- Open your run's Results page in the viewer.
- Copy your Step 4 table into the Step 12 part of `WRITEUP.md` and add an "Actual" column. Leave
  Step 4 as you committed it.
- For each prediction, write "I predicted X, the actual is Y", and which line of your
  constitutions Y bears on. Back each claim with one quoted answer; Claude will pull up the
  answers you name.
- Read **at least five** of the persona model's answers to your own items, and say whether they
  sound like your famous person, quoting one. Nothing else grades that.

> [!IMPORTANT]
> **Questions:** Which prediction was furthest off, and what didn't you know when you made it?
> Did the core hold: are your two models about the same on the two core families? If not, which
> style line do you think crowded it out?

## Step 13: Write up whose preferences count

Write **500 to 800 words** in `WRITEUP.md`, in your own words. At a minimum I am looking for:

- every place a preference entered your two models, and whose it was: yours, Claude's, the Dolly
  writers', the test writers' (mine and yours), the grader's, and Qwen's makers';
- one training pair and one persona answer, quoted, and what the model copied that your
  constitution didn't ask for;
- one claim your persona model made as "I" that it invented, and a sentence saying that its
  answers are an imitation of the person, not the person;
- where you disagreed with Claude (in your labels, grades or review decisions) and what changed
  because of it;
- one thing about your models you couldn't measure;
- how you used Claude in this part, following the class's
  [AI-use norms](https://docs.google.com/document/d/1Eb6qxeS2wy-9TBzL8eGk9j75iYu_yEV4VoLQaywRz8E/edit).

When you're done, ask Claude to run the checkpoint. It commits and pushes your work as
`Part 2 done`.

## What to submit

Your repository, pushed by **8:00am Tuesday, October 27**. At a minimum I am looking for:

- `voice-samples.md`, `constitutions.md`, and `evals/mine/` with your two families and
  `LOG.md` (Steps 1 to 3);
- the `Predictions locked` commit, made before any training (Step 4);
- `training/pairs-succinct.jsonl` and `training/pairs-persona.jsonl` (Step 5) and
  `training/labels.jsonl` (Step 6);
- your run folder, with all four models' answers, Sonnet's grades, the Opus audit, your review
  decisions and your ratings (Steps 9 to 11);
- `WRITEUP.md` with Steps 1 to 13 filled in, and `TRANSCRIPT.md`;
- the `Part 2 done` commit.

Submit your repository URL through the
[assignment submission form](https://forms.gle/mgKcnqzTGxNaGvteA) by the deadline.

After the deadline I'll retrain your two models from the files in your fork and run them on the
held-back items. So leave `constitutions.md`, `training/` and `evals/mine/` as they were when you
trained.

## Grading rubric

Part 2 is 50% of the assignment. Within it:

- Constitutions and tests: 15% - Your two constitutions share one core and differ only in style,
  with a conflict rule; each family has at least five items you wrote and two logged edits or
  rejections; every constitution line is mapped to a family or listed as not measured.
- Predictions and labels: 20% - Your predictions are numbers and were committed before any
  training; your blind labels were written before you saw which answer Claude wrote; you explain
  one pair where you and Claude read the constitution differently, or, if you picked Claude's
  answer every time, the pair you were least sure of and why.
- Reading the models: 10% - Your Step 7, 8 and 9 answers each name one concrete change, seen in
  a quoted answer or a reward number, not a restatement of `training.md`.
- The run: 10% - Your run folder holds all four models' answers on the shared and your own
  items, Sonnet's grades, the Opus audit, your review decisions and your ratings.
- Checking the grader: 15% - Each review decision gives a reason from the rubric, and you say
  which model the grader's mistakes favored and whether they could change one row of your table.
- Whose preferences count: 30% - Each prediction is checked against a number and a quoted
  answer; you quote one training pair and one persona answer and name what the model copied that
  your constitution didn't ask for; you say whose choices shaped each result, in your own words.

## FAQ

FAQ: TBA (ask a question on `#comp440-f26`!)
