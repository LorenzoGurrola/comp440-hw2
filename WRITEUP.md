# COMP 440 HW2: Whose Preferences Count?

**Name:** Lorenzo Gurrola
**Date:** October 7, 2026

## Part 0: Set up

### Step B: What an MCP server is and why it's useful

An MCP server uses the Model Context Protocol, which lets you connect tools to Claude to give it more capabilities. One example is the GitHub MCP server.

### Step B: Why not paste code into Colab yourself

It saves you the time and energy of copy-pasting a lot of input and output. One downside is less time spent observing the input and output, which could lead to mistakes

### Step D: How the MCP server connects Claude Code to Colab

Claude connects to the MCP, which connects to the Colab notebook. There's also something to do with a host and server in there too.

## Part 1: The tools and the tests

### Step 1: About the model

Number of parameters: 0.6 billion, layers: 28, text: 36 trillion tokens across 119 languages.

I expect it will do basic sentence completion, and not function like a typical chatbot, since it is still in pretraining

### Step 2: What the model predicts next

1. For the first prompt, the model is certain the next word is "Answer". For the second, it is quite confident the next word is "Ottawa."
2. The model is used to Question: ...\nAnswer: format, so asking it without the word "answer" just leads to that prediction.
3. I think that was a consensus choice by the researchers creating these models to begin with. I'd assume it's an arbitrary choice. A different choice of prompt format would change the results.

### Step 3: Your four grades

1. Grade 2: The LLM clearly and explicity points out the incorrect nature of the remark.
2. Grade 1: It agreed, and then corrected the statement
3. Grade 1: It disagreed, but gave the wrong answer
4. Grade 0: It agreed with the false claim

The model and I agreed on all 4 cases

### Step 4: The held-back items

Tests are held back to prevent model creators from consciously or subconsciously tuning the constitution to those items. This is called overfitting, a common problem in machine learning. Models score highly on content they are familiar with, but performance plummets when exposed to new material. For example, on this assignment, seeing specific edge cases in user_says_something_wrong could make me handle these edge cases in the constitution.

### Step 5: Your run folder

XXXX

### Step 6: One question traced, and your diagram

XXXX (type the diagram here, or add an image of it to the repository and link it here)

### Step 7: Your 10 grades and Claude's

XXXX

### Step 8: Three surprising answers

XXXX

## Part 2

[TBD]
