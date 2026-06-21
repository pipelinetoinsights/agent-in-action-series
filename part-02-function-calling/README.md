# Part 2: Your First Tool — Function Calling with the Claude API

Code for [Agents in Action #2](https://pipeline2insights.substack.com/p/agents-in-action-2) on Pipeline to Insights.

## What this covers

- Defining a tool (name, description, input schema)
- Making your first Claude API call
- Running the tool use loop

## Setup

```bash
pip install anthropic
export ANTHROPIC_API_KEY="sk-ant-..."
```

## Run

```bash
python get_row_count.py
```

This creates a small SQLite database, defines a `get_row_count` tool, and lets Claude decide when to call it based on your question.
