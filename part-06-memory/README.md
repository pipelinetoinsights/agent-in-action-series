# Part 6 — Memory: Agents That Remember Between Runs

Code for [Agents in Action #6](https://pipeline2insights.substack.com) on [Pipeline to Insights](https://pipeline2insights.substack.com).

A pipeline health monitor that reads `agent_memory.json` before it reasons and writes back to it before it exits — the same checkpoint-read / checkpoint-write pattern as a streaming job's state store, just pointed at an LLM call. `check_table` runs a real `SELECT COUNT(*)` against a local SQLite `warehouse.db`, same as Part 2 and Part 3.

## Setup

```bash
pip install anthropic
export ANTHROPIC_API_KEY="sk-ant-..."
```

## Run it

```bash
python memory_agent.py     # first run — seeds warehouse.db (10,000 orders, 5,400 customers), no memory yet, records a baseline
python simulate_drop.py    # deletes 2,000 real rows from orders — simulates an incident
python memory_agent.py     # second run — memory exists, agent catches the real drop
```

`simulate_drop.py` runs an actual `DELETE FROM orders`. Nothing about `check_table` or the agent's reasoning changes between the two `memory_agent.py` runs — the only difference is that the second run has `agent_memory.json` on disk to read.

## Files

| File | What it does |
|------|-------------|
| `memory_agent.py` | `load_memory` / `save_memory` (the state store) + `check_table` (real SQLite query) + `build_system_prompt` (inject prior findings) + `run_health_check` (wire it together) |
| `simulate_drop.py` | Deletes 2,000 rows from `orders` in `warehouse.db` to simulate a real incident |

## What you should see

First run (empty memory, fresh `warehouse.db`) — the agent just records a baseline:

```
Status: Baseline Established — No anomalies to report
orders: 10,000 rows
customers: 5,400 rows
```

After `simulate_drop.py`, second run (memory now has the first run's numbers) — same code, same query, but the agent catches it because it read `agent_memory.json` first:

```
ALERT — orders table: Significant Row Count Drop
Row Count: 10,000 → 8,000 (−20%)
Recommended action: Investigate immediately. Check pipeline logs, recent
DML history, and audit logs for this table before the next pipeline run proceeds.
```

`warehouse.db` and `agent_memory.json` are both gitignored — delete them and rerun `memory_agent.py` to start over from a clean baseline.
