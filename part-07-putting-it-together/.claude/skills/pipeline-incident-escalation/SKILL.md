---
name: pipeline-incident-escalation
description: Investigates and escalates a table row-count anomaly flagged by
  pipeline_monitor.py. Use when an on-call engineer asks about an ANOMALY
  alert, a table row-count drop, or "is this table okay" after a pipeline
  health monitor alert.
---

# Pipeline Incident Escalation

Follow this procedure whenever asked to investigate a row-count anomaly on a
monitored table (`orders`, `customers`, `payments`). Do not skip steps.

This is deliberately a human-facing procedure, not something
`pipeline_monitor.py` runs on its own — the monitor's job ends at flagging an
anomaly. Deciding how to respond is a judgement call for the on-call engineer,
with this runbook as the guide.

## Step 1: Re-check the table right now

Call the `check_table` MCP tool for the table in question (requires the
`warehouse` MCP server registered — see this project's README). Don't trust
only the monitor's last reading; the incident may already be resolving or
worsening.

## Step 2: Compare against the alert

- If the current count is still down more than 10% from what the monitor
  reported as the previous baseline, treat this as **active**.
- If the count has recovered, treat this as **resolved** but still report it —
  a self-healing drop is still worth a paper trail.

## Step 3: Escalate

For an **active** incident, produce a message in this exact format for
`#data-incidents`:

```
🔴 INCIDENT — <table> row count
Baseline: <previous count> → Current: <current count> (<percent> drop)
Checked at: <timestamp>
Recommended: check upstream ingestion logs and recent DML history for
<table> before the next scheduled load runs.
```

For a **resolved** incident, post a short note instead:

```
✅ RESOLVED — <table> row count has recovered to <current count>.
No action needed, logging for the record.
```

## Step 4: Never guess the numbers

Every number in the escalation message must come from Step 1's tool call or
the previous baseline the engineer gives you — never estimate or round a row
count. This is the same rule as Part 2's tools: a tool exists precisely
because guessing a row count is worse than useless.
