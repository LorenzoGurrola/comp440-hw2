# COMP 440 HW2 Part 2: Train your two models and decide what changed

Due **8:00am Tuesday, October 27**. The overall instructions are in the [README](../README.md).

In this part you'll train your two models and find out what your choices did to them. In
particular, you will:

- Write the rules for two models, a *constitution* for each, and tests of your own, and predict
  in numbers how each model will do before you train anything.
- Gain hands-on experience with the two kinds of training that come after pretraining: training
  on example answers (SFT, supervised fine-tuning) and training on pairs of answers where one is
  preferred (DPO, direct preference optimization).
- Check the AI grader against a second AI grader and against your own grades, and rate your two
  models blind.
- Understand whose preferences ended up in each model: yours, Claude's, the people who wrote the
  example answers, and the grader's.

This part builds on [Part 1](part1.md). You'll run the same evaluations again, this time on four
versions of the model: the base model, the model after SFT, and your two DPO models.

## Before you start

- Finish [Part 1](part1.md) first.
- Claude runs the cells and the commands. The choices and the writing are yours: your famous
  person, your constitution lines, your test items, your predictions, your labels, your review
  decisions and your write-up. Apart from drafting test items for you to review in Step 3,
  Claude won't suggest any of these, not even as options or from your notes. That isn't Claude
  being unhelpful. This assignment asks whose preferences shaped your models, and if Claude
  writes those parts, the answer is Claude's. Ask it to explain anything as often as you like.
- Claude does write most of your training data, in Step 5, and Step 6 checks how much you agree
  with it.

I recommend five sittings, since some steps need Claude to work for a while and one needs a GPU:

| Sitting | Steps | What you need |
|---|---|---|
| 1 | 1 to 4: your famous person, constitutions, tests and predictions | Claude Code. No GPU. |
| 2 | 5 and 6: the preference data and your blind labels | Claude Code. Claude writes 600 answers, which uses a good share of your plan. |
| 3 | 7 to 9: training and answering | Colab with a T4, about 20 minutes of GPU time in one go |
| 4 | 10 and 11: grading, the audit, your review and your ratings | Claude Code and the viewer. No GPU. |
| 5 | 12 and 13: checking your predictions and the write-up | Claude Code and the viewer |

I expect Part 2 to take about [TBD] hours in all. Please don't leave sitting 3 for the last
night: free T4s are sometimes all taken.

## Step 1: Pick your famous person

One of your two models will answer in the voice of a famous person you admire. Pick them first,
since your constitutions and tests depend on the choice.

- Pick a person whose own words you can read: speeches, letters, interviews, essays or books.
- Write their name, and two sentences on why you picked them, in `WRITEUP.md`.
- Copy **up to five** short passages of their own words into `voice-samples.md`, each with its
  source. The file shows the format. Claude reads these passages when it writes answers in this
  person's voice in Step 5.

Four rules for who you pick:

1. A public figure with at least a few pages of their own public words. Never a private person,
   anyone at Macalester, or a classmate.
2. At most five short quoted passages, a few sentences each. Your fork is public, so I don't
   want whole speeches or chapters in it.
3. Your model will speak as "I" and will invent things about the person's life. Its answers are
   an imitation, not the person, and your write-up must say so.
4. If you're not sure a choice is fair, ask on `#comp440-f26` before you start Step 2.

- Hints:
  - A person with a recognizable way of talking or writing is easier to spot in a small
    model's answers than one who sounds like everyone else.
  - Claude can open a page you name and copy the passage you choose into `voice-samples.md`,
    word for word. It won't suggest a person or a passage.

> [!IMPORTANT]
> **Question:** What would someone notice first about the way this person talks or writes?

## Step 2: Write your two constitutions

A *constitution* is a short list of written rules that a model is trained to follow. Anthropic
published [the one it used for Claude](https://www.anthropic.com/news/claudes-constitution) in
2023. Your two models share one core and differ only in style. That way a difference between
them can be traced to the style: if they differed in everything, you couldn't tell which choice
caused which result.

- Open `constitutions.md`. The `## Core` section is already written and is the same for
  everyone: be truthful, do the task, correct false claims, follow format rules. Don't change it.
- Under `## Succinct style`, write **at least five** lines on how the succinct model answers:
  how long, what it keeps and what it leaves out.
- Under `## Persona style`, write **at least five** lines that describe your famous person's
  voice: their habits, what they care about, the shape of their sentences. Include at least one
  line on what the model should *do*, not only how it should sound.
- Under `## When they conflict`, write what wins when a style line pulls against a core line,
  for each model. For example, what should the persona model do when someone asks about
  something the person never knew about?
- Replace each `XXXX` with your lines. Claude won't build training data from a section that
  still says `XXXX`.
- Hints:
  - The example at the bottom of `constitutions.md` is for a 1950s radio announcer, not a real
    person. Use it for the form, not the lines.
  - Read your voice samples again before you write the persona lines. What does the person do
    in every passage?
  - Write each line so Claude could follow it without asking what you meant. In Step 5, Claude
    reads one model's lines (the core, one style and the conflict rule), plus your voice samples
    for the persona model, and nothing else.
- Warning: don't write a list of catchphrases or a fixed opening line. When I trained this model
  on answers that each started with one of a few friendly openers, it learned the openers, not
  the friendliness, and it stopped doing the task: asked for a thank-you note, it replied with a
  stock greeting.

> [!IMPORTANT]
> **Questions:** Which line of your persona style do you think will be hardest for a 0.6B model
> to learn, and why? Where do you expect each style to pull against the core?

## Step 3: Write two test families of your own

A *family* is a set of test items of one kind, like the three in `evals/shared/`. Two of the
shared families test the core (short facts, and user says something wrong) and one tests a kind
of style (emotional and social messages). Your two families test what only you know about: your
two styles.

- Decide what each of your families tests. Pick one you predict the succinct model will win and
  one you predict the persona model will win.
- In `WRITEUP.md`, write a short paragraph for each family: what it tests, which lines of your
  constitutions it tests, and which model you think will win.
- For each family, choose which shared family its items look like: `facts`,
  `user_says_something_wrong` or `emotional_social`. Your items use that family's fields, and
  the grader grades them by that family's rules.
- Write **at least five** items for each family yourself, in `evals/mine/<family>.jsonl`, one
  JSON object per line. `<family>` is a short name in lowercase letters, digits and
  underscores, starting with a letter.
- Give each item an `id` such as `mine-<family>-001`, a `family` of `mine-<family>`, a
  `graded_like` naming the shared family it looks like, a `subtype` of your choosing, a
  `prompt`, a `predicted_winner` and a `why`, plus that shared family's own fields.
- Then ask Claude to draft more items for each family, until each has **at least ten**. Accept,
  edit or reject each draft, and edit or reject **at least two** per family. Claude records each
  draft and your decision in `evals/mine/LOG.md`.
- Ask Claude to check your files with `python3 evals/shared/validate.py --extra evals/mine`.
- Hints:
  - Copy one line from the shared file your family looks like, and change it. "Item format" in
    `evals/shared/README.md` explains every field.
  - Don't put the word `hidden` in a file name. The tools treat such files as held-back items.
- Warning: the grader only checks what the shared family's rules check. For a `facts`-style item
  it checks whether the main answer is right; for an `emotional_social`-style item it checks
  whether the message does the task and uses the details. Nothing grades whether an answer
  sounds like your famous person. You'll judge that yourself, by reading, in Step 12.

> [!IMPORTANT]
> **Questions:** For one draft you rejected or edited, what did it get wrong about what you
> wanted to test? Could a model score well on one of your families for the wrong reason?

## Step 4: Map your constitutions to your tests, and predict

A test only tells you about the rules it checks. In this step you'll find out which of your rules
you can measure, and you'll commit to numbers before any training, so the results can't nudge
your predictions.

- Make one table in `WRITEUP.md` with a row for every line of `constitutions.md`, core lines
  included.
- For each line, name the family that tests it (a shared one or one of yours), or write "not
  measured".
- For each of the five families, predict a number for the succinct model and one for the
  persona model, using that family's measure: the share correct for facts, the mean score (0 to
  2) for user says something wrong, and the share of messages that do the task for emotional
  and social. Your own families use the measure of the family they're graded like.
- Predict one more number: the share of your Step 11 blind comparisons the persona model will
  win.
- Ask Claude to commit and push with the subject `Predictions locked`. Claude won't run any
  training before that commit exists, and I'll check that it came first.
- Hints:
  - Your Part 1 base-model run is a starting point. Its Results page shows the base model's
    numbers on the three shared families.
  - The predicted winners in `evals/shared/README.md` are my guesses, not answers. Yours can
    differ.
- Warning: write numbers, not "succinct wins". A number can be checked in Step 12; "succinct
  does better" can't tell you how far off you were.

Claude shows your table back word for word and says nothing about it until Step 12.

> [!IMPORTANT]
> **Questions:** Which line of your constitutions does no test measure, and why is it hard to
> test? Which prediction are you least sure of?

## Step 5: Have Claude build the preference data

DPO trains on *pairs*: a prompt, a *chosen* answer and a *rejected* answer. Training makes
answers like the chosen one more likely and answers like the rejected one less likely. You need
300 pairs for each of your two models.

Claude writes most of this data. For each of the 300 prompts in `training/prompts-300.jsonl`, the
chosen answer is one Claude writes under your constitution, and the rejected answer is the one
a person wrote for the same prompt in the Dolly dataset (`training/README.md` says where it comes
from). Claude writes the chosen answers instead of picking between two answers because a 0.6B
model almost never writes in your famous person's voice on its own, so there would be little to
pick from. That means Claude's reading of your constitution goes into your models. Step 6
measures how much you agree with it.

- Type `/build-preferences`. Claude starts helpers (Sonnet subagents) that write the answers in
  batches of 25, on your Claude Code plan. No API key is needed.
- After the first batch for each model, Claude shows you three answers word for word and asks
  whether they follow your constitution. If they don't, change `constitutions.md` yourself and
  type `/build-preferences` again.
- At the end, Claude checks the files with
  `python3 evals/shared/validate.py --train training --extra evals/mine`. It also shows how
  varied the answers are (repeated openings, closings and phrases, with counts) and their
  average length next to the human answers.
- Claude then asks before it commits the pairs as `Preference data built` and pushes them. The
  notebook reads them from your fork in Step 7.
- Read **at least ten** pairs from each of `training/pairs-succinct.jsonl` and
  `training/pairs-persona.jsonl`. Ask Claude to show them word for word, or open the files.
- Hints:
  - This takes Claude about [TBD] minutes. If you hit your plan's usage limit, wait for it to
    reset and type `/build-preferences` again. It carries on where it stopped.
  - If you change your constitutions here, say what you changed in your Step 5 answer, and leave
    your Step 4 predictions as they are. They're locked; Step 12 is where you explain a gap.

> [!IMPORTANT]
> **Questions:** Quote one chosen answer. What does it do that your constitution didn't ask for?
> Is there anything many of Claude's answers share that your model might learn to copy?

## Step 6: Label a sample yourself, blind

Before you train on Claude's pairs, check whether you agree with them. You'll pick the better
answer in 15 pairs per model, without knowing which answer Claude wrote.

- Ask Claude to run `python3 evals/shared/label_tools.py sample`. It draws 15 pairs per model,
  shuffles each pair's two answers into A and B, and writes them to
  `training/label-sample.jsonl`. Which answer Claude wrote goes in `training/label-key.json`.
  Don't open that file. Claude won't either until your labels are in.
- For each pair, Claude shows you the question and both answers, word for word. Say which one
  better follows that model's constitution, A or B, and give a short reason. Claude writes your
  picks into `training/labels.jsonl`.
- When all 30 are in, ask Claude to run `python3 evals/shared/label_tools.py score`. It prints
  how often you picked Claude's answer for each model, and lists the pairs where you didn't.
- Hint: you'll often be able to tell which answer Claude wrote. Label by the constitution
  anyway, and note when you could tell.
- Warning: once you've seen the key, you can't label blind again, so finish all 30 first.

> [!IMPORTANT]
> **Questions:** How often did you pick Claude's answer, for each model? For one pair where you
> didn't, which line of the constitution did you and Claude read differently? If you picked
> Claude's answer every time, which pair were you least sure of, and why?

## Step 7: Train on example answers (SFT)

Steps 7, 8 and 9 happen in one Colab sitting of about 20 minutes of GPU time, plus your reading.
The notebook trains three models and answers every test item with all four, and the trained
models live only on that Colab machine. If Colab disconnects partway, they're gone, and Claude
reruns the notebook from the top.

- Read [`training.md`](training.md) first. It explains SFT and DPO with one example each, and how
  to read the numbers the training prints. We'll cover both in class later, but you need the
  basics now.
- Make sure Claude has pushed all your commits. The notebook reads your pairs and your test items
  from your fork on GitHub.
- Plug in your laptop and keep it awake until Step 9's download arrives.
- Ask Claude to run the setup cells and the "Part 2 setup" cell (Claude fills in `FORK_URL`, your
  fork's address), then the Step 7 cells.
- The training cell trains the model on 600 human-written answers from Dolly: two passes, 150
  steps, about 3 minutes on a T4. Every 25 steps it prints the loss, which should fall from about
  2.3 in the first pass to about 1.4 in the second.
- The last Step 7 cell prints five questions from `training/readout-10.jsonl`, each with the base
  model's answer and then the SFT model's. Read them.
- Hints:
  - If Colab disconnects, ask Claude to reopen the notebook and choose the T4 again. A reconnect
    starts a new machine, so Claude reruns the setup cells and starts again at Step 7.
  - If a cell stops with "CUDA out of memory", ask Claude to run that step again. The README's
    Troubleshooting section says what to do if it happens twice.
  - If Colab says no T4 is free, try again in an hour or two.

> [!IMPORTANT]
> **Questions:** What did SFT change in the answers? Quote one answer that shows it. Did the
> answers get more correct, or only different in form? How can you tell from what you read?

## Step 8: Train your two models (DPO)

- Ask Claude to run the Step 8 cells. They train two models with DPO, both starting from your
  SFT model: the succinct model on `training/pairs-succinct.jsonl` and the persona model on
  `training/pairs-persona.jsonl`. Each takes about 3 minutes.
- Each training run is 50 steps of 8 pairs. Every 5 steps it prints the loss, the chosen reward,
  the rejected reward and the accuracy. [`training.md`](training.md) says what each one means.
- After each run, the cell prints a small table of steps 5, 25 and 50. Copy both tables into
  `WRITEUP.md` before you close Colab: they aren't saved anywhere else.
- The last Step 8 cell prints five more questions from `training/readout-10.jsonl`, each with
  the SFT, succinct and persona models' answers. Read them.
- Warning: a loss near 0 doesn't mean the model is finished or better. When I tried DPO on this
  model with easy pairs, the loss reached about 0 by step 15 of 50, and the remaining steps kept
  pushing the rejected answers further down. Too much of that can make answers terse or strange.

> [!IMPORTANT]
> **Questions:** In each table, which moved further from 0, the chosen reward or the rejected
> reward, and by how much? What does that say each model learned? Quote one answer from each
> model that shows a change from SFT.

## Step 9: Run the evaluations on all four models

- Ask Claude to run the Step 9 cells. They answer the 240 shared items and your own items with
  all four models: base, SFT, succinct and persona. This takes about 7 minutes.
- The last Step 9 cell downloads `hw2-four-models.zip`. Allow the download if Chrome asks.
- Before anything is graded, ask Claude to pick five items at random and show you all four
  models' answers to them, word for word.
- In `WRITEUP.md`, write one sentence about each model: what you noticed in its five answers.
- Ask Claude to make a run from the zip and grade it with Sonnet. Grading needs no GPU, so this
  can be a new sitting. Four models' answers to all the items come to about 1,000 responses, or
  about 19 grader batches, all on your plan.
- Write your run folder's name in `WRITEUP.md` (it looks like
  `evals/runs/2026-10-21-four-models`).
- Please don't open this run's Results or Answers pages in the viewer until your Step 10 review
  decisions are in. Once you've seen the grader's numbers it's hard to grade on your own. Claude
  won't quote grades or percentages before then either.

> [!IMPORTANT]
> **Question:** Which model's answers surprised you most, and how?

## Step 10: Grade and audit

Every grader makes mistakes. Here you'll measure Sonnet's, with a second grader and your own
judgment.

- Ask Claude to audit the run with Opus at medium effort. It picks about 60 of Sonnet's grades,
  mostly ones that look hard plus some at random, and Opus grades those answers again without
  seeing Sonnet's grades.
- Ask Claude to build a review queue. It holds every answer where Sonnet and Opus disagree, plus
  a few where they agree.
- On the viewer's Review page, for each answer: grade it yourself first (that grade is then
  locked), then see what Grader 1 and Grader 2 said (which grader is which is hidden), and decide
  who was right, with a reason from the rubric.
- Once your decisions are in, open the Graders page to see how often Sonnet and Opus agreed.
- You're welcome to write a rubric clarification and have Claude re-grade the reviewed answers
  with it (see "Fix the scorer" in `evals/shared/README.md`). It's for this exercise only: grades
  on the three shared families stay on the shared rubric.
- Hint: the rules both graders follow are in `.claude/agents/eval-grader.md`, the file you found
  in Part 1 Step 6.
- Warning: Sonnet wrote your chosen answers in Step 5, and Sonnet grades your models. Keep that
  in mind when you decide.

> [!IMPORTANT]
> **Questions:** How many of Sonnet's grades did you overturn? Did those mistakes favor one of
> your models, and which row of your Step 4 table could they move, in which direction? The audit
> picked mostly hard answers: does that make Sonnet look better or worse than it is?

## Step 11: Rate your two models blind

Claude doesn't judge warmth or tone. People do, and in this step that's you.

- Open the viewer's Rate page for your run, type your name, choose your succinct and persona
  models, and press Start. The page gives you a random 20 of the 40 emotional and social items.
- For each item, read both messages (the page doesn't say which model wrote which), mark whether
  each does the task, then press "Send this one" under the one you'd rather send.
- This takes about 15 minutes.
- Hint: you'll probably recognize your persona model's answers, so this isn't fully blind.
  That's fine. Say so in your answer.

> [!IMPORTANT]
> **Questions:** What share of your picks went to each model, and what share of each model's
> messages did the task? Could you tell which model wrote which? How?

## Step 12: Check your predictions

- Open your run's Results page in the viewer.
- Copy your Step 4 table into the Step 12 part of `WRITEUP.md` and add an "Actual" column. Leave
  Step 4 as you committed it.
- For each prediction, write "I predicted X, the actual is Y", and which line of your
  constitutions Y bears on.
- Back each claim with one quoted answer. Ask Claude to pull up the answers you name. It won't
  pick them for you.
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

- `voice-samples.md` and `constitutions.md` (Steps 1 and 2);
- `evals/mine/` with your two families and `LOG.md` (Step 3);
- the `Predictions locked` commit, made before any training (Step 4);
- `training/pairs-succinct.jsonl` and `training/pairs-persona.jsonl` (Step 5) and
  `training/labels.jsonl` (Step 6);
- your run folder, with all four models' answers, Sonnet's grades, the Opus audit, your review
  decisions and your ratings (Steps 9 to 11);
- `WRITEUP.md` with Steps 1 to 13 filled in, and `TRANSCRIPT.md`;
- the `Part 2 done` commit.

Submit your repository URL through the
[assignment submission form](https://forms.gle/mgKcnqzTGxNaGvteA) by **8:00am Tuesday,
October 27**.

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
