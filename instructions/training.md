# Training your models: SFT and DPO

In Steps 7 and 8 of [Part 2](part2.md) you train four models: two with SFT, then two with DPO,
each starting from one of the SFT models. We'll cover these two kinds of training in class on
October 29 and November 3, after Part 2 is due, so this page gives you what you need now: one
example of each, what the numbers the training prints mean, and what one training step is. It
should take about 15 minutes to read.

## Where you start

In Part 1 you saw that the base model does one thing: given some text, it gives a probability
for every possible next token. Asked a question, it answers, and then it often keeps going with
whatever tends to follow on the web, such as another question. Training changes the model's
weights so that some continuations become more likely and others less likely. SFT and DPO both
do that. They differ in what the model is shown.

## SFT: training on example answers

*SFT*, supervised fine-tuning, shows the model a prompt followed by an example answer. Your two
SFT runs use the chosen answers in your pairs files, the ones Claude wrote under each
constitution in Step 5: one run on `training/pairs-succinct.jsonl`, the other on
`training/pairs-persona.jsonl`. Here are the two parts of a pairs-file line that SFT reads. I
wrote this chosen answer myself, by following the 1950s radio announcer example at the bottom of
`constitutions.md`:

```
"prompt": "Question: Why do my fingers hurt when playing guitar?\nAnswer:"
"chosen": " Those steel strings are pressing into soft skin, and that's why your fingertips ache. Here's the good news, listeners: play a little every day, and in a few weeks you'll grow calluses, tough little pads that let you play for an hour without a wince."
```

The `prompt` is the question, in the same `Question: ...\nAnswer:` form as the tests. The
`chosen` answer is the example the model learns to write.

The model reads the prompt and the answer, token by token. At each token of the answer, it gives
a probability to every possible next token, and training checks how much of that probability
went to the token that actually comes next. Only the answer is scored. The model reads the
prompt but isn't scored on it, because we want it to learn to answer questions, not to write
them.

### What the loss means

The *loss* for one token is -ln(p), where p is the probability the model gave to the answer's
actual next token, and ln is the natural logarithm (the ln key on a calculator). The loss the
notebook prints is the average over many tokens.

| Probability given to the answer's next token | Loss |
|---|---|
| 0.10 (1 in 10) | 2.3 |
| 0.25 (1 in 4) | 1.4 |
| 0.50 (1 in 2) | 0.69 |
| 0.90 | 0.11 |

When I tried this on 300 answers Claude wrote under one student's succinct constitution, the
loss was about 2 in the first pass and about 0.8 in the second. Roughly, the model went from
giving the answer's next token about a 1 in 7 chance to about a 1 in 2 chance.

Part of that drop is learning, and part is memory: in the second pass, the model has already seen
every example once. A falling loss tells you the model got better at predicting these 300
answers. It doesn't tell you whether it got better at answering new questions. For that, you read
its answers.

### What one step is

A *step* is one small change to the weights. The notebook takes a *batch* of 8 examples and
computes their average loss. It works out which direction to move each of the model's roughly 600
million weights to lower that loss, and moves each one a tiny amount. The *learning rate*, 2e-5
here, sets how far. 300 examples in batches of 8 is 38 steps per pass (the last batch holds only
4), and two passes make 76 steps.

What SFT mostly teaches is the form of an answer and when to stop. Claude's habits come along
too: its length, its favorite phrases and its tone. In practice, AI labs shape much of a model's
personality in SFT, by training it on answers written in the voice they want. That is what your
two SFT runs do, and DPO then sharpens it.

## DPO: training on preferences

*DPO*, direct preference optimization, shows the model pairs of answers to the same prompt, one
*chosen* and one *rejected*. It changes the weights so that answers like the chosen one become
more likely than answers like the rejected one. DPO teaches the model which style of answer to
prefer; it doesn't add new facts. Here is the whole pairs-file line from the SFT example above.
Its prompt and its rejected answer are line 69 of `training/prompts-300.jsonl`: the rejected
answer is the one a person wrote for Dolly.

```
{"id": "pair-069", "prompt": "Question: Why do my fingers hurt when playing guitar?\nAnswer:", "chosen": " Those steel strings are pressing into soft skin, and that's why your fingertips ache. Here's the good news, listeners: play a little every day, and in a few weeks you'll grow calluses, tough little pads that let you play for an hour without a wince.", "rejected": " While learning guitar, it is very common for finger tips to hurt. Usually what occurs with practice is the development of tougher skin called calluses that make the guitar less painful to play."}
```

DPO keeps two copies of the model on the GPU: the one being trained, and a frozen copy of the
model you started from. For each of your two models, that's its own SFT model. For each answer
in a pair, DPO compares how likely the two copies find that whole answer.

### The reward

The *reward* for an answer is 0.1 times how much more likely the answer became, compared with the
model you started from. "How much more likely" is measured with a natural log:

```
reward = 0.1 × ln(p_now / p_start)
```

Here p_now is the probability that the model being trained gives the whole answer, and p_start is
the probability the frozen SFT copy gives it. The 0.1 is a setting called *beta*: the smaller it
is, the further DPO lets the model drift from where it started.

- A reward of 0 means the answer is exactly as likely as before.
- A positive reward means it's more likely.
- A negative reward means it's less likely. A reward of -0.69 means the answer is 1/1000 as likely
  as before, since ln(1/1000) = -6.9. So a large negative number, like -15, means the model now
  almost never writes answers like the rejected one.

### A worked example

Suppose that partway through training, for the guitar pair:

1. The model gives the chosen answer 3 times the probability the SFT model gave it. Its reward is
   0.1 × ln(3) = +0.11.
2. It gives the rejected answer 1/1000 of the probability the SFT model gave it. Its reward is
   0.1 × ln(1/1000) = -0.69.
3. The loss for this pair is -ln(σ(0.11 - (-0.69))) = -ln(σ(0.80)) = 0.37. Here
   σ(x) = 1 / (1 + e^-x) turns any number into a probability between 0 and 1, and e^-x is the
   number e (about 2.718) raised to the power -x.

The loss depends only on the gap between the two rewards, here 0.80. At the start both rewards are
0, the gap is 0, and the loss is ln(2) = 0.69. As the gap grows, the loss falls toward 0. The
*accuracy* the notebook prints is the share of pairs where the chosen answer's reward beats the
rejected answer's.

Because only the gap matters, DPO can widen it in two ways: by making chosen answers more likely,
or by making rejected answers less likely. The reward log tells you which one happened.

### What a reward log looks like

Before the course, I tried DPO on this model with made-up pairs. Each prompt had a short, plain
answer (the first sentence of a Dolly answer) and the same answer padded with a stock friendly
opening and closing. One run chose the plain answer, and the other chose the padded one. Here are
four lines of the first run's log:

| Step | Loss | Chosen reward | Rejected reward | Accuracy |
|---|---|---|---|---|
| 5 | 0.503 | +0.02 | -0.84 | 0.82 |
| 10 | 0.003 | -0.05 | -15.2 | 1.00 |
| 15 | 0.000 | -0.19 | -23.2 | 1.00 |
| 50 | 0.000 | -0.65 | -28.5 | 1.00 |

In this run, the chosen answers barely moved and the rejected answers fell a long way: the model
mostly learned to avoid padded answers, not to write plain ones. The second run went the other
way. Its chosen (padded) answers rose to +6.2 by step 50, and its rejected (plain) answers fell
only to -1.4. Your logs may look like either one, or like neither.

Also notice that the loss was about 0 by step 15, but the rejected reward kept falling for the
next 35 steps. A loss of 0 means every pair's gap is already wide, not that training stopped
changing the model.

### What one DPO step is

It's the same idea as in SFT: one step looks at 8 pairs and moves the weights a little, with a
smaller learning rate (5e-6). The GPU can only hold 2 pairs at a time, so the notebook adds up the
changes from 4 groups of 2 before it moves the weights. Each of your DPO runs is 38 steps of 8
pairs, 304 pairs in all, so it sees each of your 300 pairs about once.

## Why GPU memory is tight

The T4 has about 14.5 GB of memory you can use, and SFT on this model used 14.0 GB at its peak.
DPO holds two copies of the model. Also, Qwen's vocabulary is large (about 152,000 tokens), so the
table of next-token scores for every position in 8 answers is over 1 GB by itself. That's why the
batches are small, and why "CUDA out of memory" is the error you're most likely to see. The
[README](../README.md#troubleshooting)'s Troubleshooting section says what to do.

## If you want more

- [TRL's SFT Trainer](https://huggingface.co/docs/trl/sft_trainer) and
  [DPO Trainer](https://huggingface.co/docs/trl/dpo_trainer) pages, for the library the notebook
  uses.
- [The DPO paper](https://arxiv.org/abs/2305.18290) (Rafailov and others, 2023), which derives the
  reward above.
- [databricks-dolly-15k](https://huggingface.co/datasets/databricks/databricks-dolly-15k), where
  the human answers come from. `training/README.md` says how I picked them.
